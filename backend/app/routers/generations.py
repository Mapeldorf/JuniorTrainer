from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status

from app.deps import require_tech_lead
from app.orchestrator import run_generation
from app.rate_limit import START_GENERATION_LIMIT, limiter
from app.schemas.generation import (
    ExerciseCandidate,
    GenerationStatusResponse,
    GenerationSummary,
    StartGenerationRequest,
    StartGenerationResponse,
)
from app.schemas.profile import Profile
from app.supabase_client import get_admin_client

router = APIRouter(tags=["generations"])


_GENERATION_SUMMARY_FIELDS = "id, status, technologies, repo_name, kind, error_message, created_at"


def _to_generation_summary(row: dict) -> GenerationSummary:
    return GenerationSummary(
        id=row["id"],
        status=row["status"],
        technologies=[t.strip() for t in row["technologies"].split(",") if t.strip()],
        repo=row["repo_name"] or None,
        kind=row["kind"],
        error_message=row.get("error_message"),
        created_at=row["created_at"],
    )


def _canonicalize_technologies(technologies: list[str]) -> list[str]:
    """Valida las tecnologias contra el catalogo canonico y devuelve sus
    nombres canonicos, sin duplicados (change `catalogo-tecnologias`,
    requisito "Tecnologias de la generacion limitadas al catalogo"). La
    comparacion ignora mayusculas y espacios sobrantes; cualquier tecnologia
    que no exista en el catalogo hace que la peticion se rechace con 422."""
    catalog_rows = get_admin_client().table("technology").select("name").execute().data or []
    catalog = {row["name"].strip().lower(): row["name"] for row in catalog_rows}

    canonical: list[str] = []
    unknown: list[str] = []
    for tech in technologies:
        name = catalog.get(tech.strip().lower())
        if name is None:
            unknown.append(tech)
        elif name not in canonical:
            canonical.append(name)

    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"tecnologias fuera del catalogo: {unknown!r}",
        )
    return canonical


@router.post("/generations", status_code=status.HTTP_201_CREATED)
@limiter.limit(START_GENERATION_LIMIT)
async def start_generation(
    request: Request,
    body: StartGenerationRequest,
    background_tasks: BackgroundTasks,
    profile: Profile = Depends(require_tech_lead),
) -> StartGenerationResponse:
    """Inicia una generacion (tarea 6.2). Crea la fila en `generating` y
    lanza la orquestacion en segundo plano con `BackgroundTasks` -- la
    respuesta HTTP llega con el id antes de que ningun agente responda
    (requisito "Generacion no se ejecuta en la peticion HTTP"); `BackgroundTasks`
    basta aqui porque no hace falta cancelar la tarea desde fuera ni que
    sobreviva a que el proceso se reinicie (ver design.md)."""
    # generation.repo_name es texto libre de display; guarda la referencia
    # "owner/repo" tal cual (change acceso-repo-github-tool), igual que
    # antes guardaba repo_path -- sigue sin anadirse una columna nueva.
    # Las tecnologias se validan contra el catalogo canonico antes de crear
    # la fila (change catalogo-tecnologias): una tecnologia fuera del
    # catalogo responde 422 sin crear ninguna generacion.
    technologies = _canonicalize_technologies(body.technologies)
    repo_name = f"{body.owner}/{body.repo}" if body.owner and body.repo else ""
    result = (
        get_admin_client()
        .table("generation")
        .insert(
            {
                "repo_name": repo_name,
                "technologies": ", ".join(technologies),
                "kind": body.kind,
                "status": "generating",
                "created_by": profile.id,
            }
        )
        .execute()
    )
    generation_id = result.data[0]["id"]

    background_tasks.add_task(
        run_generation,
        generation_id,
        technologies,
        body.owner,
        body.repo,
        body.kind,
        body.count,
        profile.id,
    )

    return StartGenerationResponse(id=generation_id)


@router.get("/generations")
async def list_pending_generations(
    _profile: Profile = Depends(require_tech_lead),
) -> list[GenerationSummary]:
    """Lista las generaciones pendientes de revision (tarea 1.2 de
    frontend-tech-lead-ejercicios, capacidad exercise-generation: "Listar
    las generaciones pendientes"): solo las que estan en curso
    (`generating`) o listas para revisar (`ready`), mas recientes primero.
    Las ya cerradas (`done`) y las fallidas (`error`) quedan fuera (change
    `ocultar-generaciones-error`): las `error` no son accionables desde
    este listado, siguen almacenadas y consultables por su id con
    `GET /generations/{id}`. No hace falta parametro de filtro porque no
    hay ningun caso de uso que necesite ver las no listadas (design.md
    decision 2)."""
    result = (
        get_admin_client()
        .table("generation")
        .select(_GENERATION_SUMMARY_FIELDS)
        .in_("status", ["generating", "ready"])
        .order("created_at", desc=True)
        .execute()
    )
    return [_to_generation_summary(row) for row in (result.data or [])]


@router.post("/generations/{generation_id}/close")
async def close_generation(
    generation_id: str,
    _profile: Profile = Depends(require_tech_lead),
) -> GenerationSummary:
    """Cierra la revision de una generacion lista (tarea 1.3 de
    frontend-tech-lead-ejercicios, capacidad exercise-generation: "Cierre
    de la revision de una generacion"): solo desde `ready`, pasa a `done`
    y a partir de ese momento deja de aparecer en `GET /generations`,
    tenga o no candidatos todavia sin guardar (design.md decision 3 --
    operacion dedicada, no implicita en guardar un ejercicio)."""
    gen_result = (
        get_admin_client()
        .table("generation")
        .select(_GENERATION_SUMMARY_FIELDS)
        .eq("id", generation_id)
        .limit(1)
        .execute()
    )
    rows = gen_result.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generacion no encontrada")
    generation = rows[0]

    if generation["status"] != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede cerrar la revision de una generacion lista (ready)",
        )

    result = (
        get_admin_client()
        .table("generation")
        .update({"status": "done"})
        .eq("id", generation_id)
        .execute()
    )
    return _to_generation_summary(result.data[0])


@router.get("/generations/{generation_id}")
async def get_generation(
    generation_id: str,
    _profile: Profile = Depends(require_tech_lead),
) -> GenerationStatusResponse:
    """Consulta el estado de una generacion (tarea 6.3): en curso, Ready
    con sus candidatos, o error con el mensaje de la causa."""
    gen_result = (
        get_admin_client()
        .table("generation")
        .select("id, status, error_message")
        .eq("id", generation_id)
        .limit(1)
        .execute()
    )
    rows = gen_result.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generacion no encontrada")
    generation = rows[0]

    candidates: list[ExerciseCandidate] = []
    if generation["status"] == "ready":
        ex_result = (
            get_admin_client()
            .table("exercise")
            .select("id, type, name, statement, code, expected_answer")
            .eq("generation_id", generation_id)
            .eq("saved", False)
            .is_("deleted_at", "null")
            .execute()
        )
        candidates = [ExerciseCandidate(**row) for row in (ex_result.data or [])]

    return GenerationStatusResponse(
        id=generation["id"],
        status=generation["status"],
        error_message=generation.get("error_message"),
        candidates=candidates,
    )


@router.delete("/generations/{generation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_generation(
    generation_id: str,
    _profile: Profile = Depends(require_tech_lead),
) -> Response:
    """Elimina una generacion por revisar y todos sus candidatos (tarea 2.1
    del change `eliminar-generaciones-por-revisar`, capacidad
    `exercise-generation`: "Eliminar una generacion por revisar"). Solo
    desde `ready` (mismo criterio que el cierre); se rechaza si algun
    ejercicio de la generacion ya esta guardado como definitivo, para no
    tocar el catalogo ni los bloques o asignaciones que puedan
    referenciarlo (design.md - D3).

    El borrado es una unica sentencia: las FK de `exercise` y
    `repo_access_log` hacia `generation` son `on delete cascade`
    (0008_generation_cascade_delete.sql), asi que candidatos y registros de
    auditoria desaparecen con ella (design.md - D2)."""
    gen_result = (
        get_admin_client()
        .table("generation")
        .select("id, status")
        .eq("id", generation_id)
        .limit(1)
        .execute()
    )
    rows = gen_result.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generacion no encontrada")
    if rows[0]["status"] != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede eliminar una generacion lista (ready)",
        )

    saved_result = (
        get_admin_client()
        .table("exercise")
        .select("id")
        .eq("generation_id", generation_id)
        .eq("saved", True)
        .limit(1)
        .execute()
    )
    if saved_result.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar una generacion con ejercicios ya guardados",
        )

    get_admin_client().table("generation").delete().eq("id", generation_id).execute()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
