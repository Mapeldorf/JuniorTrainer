from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

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
    repo_name = f"{body.owner}/{body.repo}" if body.owner and body.repo else ""
    result = (
        get_admin_client()
        .table("generation")
        .insert(
            {
                "repo_name": repo_name,
                "technologies": ", ".join(body.technologies),
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
        body.technologies,
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
