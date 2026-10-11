from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.deps import require_tech_lead
from app.orchestrator import run_generation
from app.schemas.generation import (
    ExerciseCandidate,
    GenerationStatusResponse,
    StartGenerationRequest,
    StartGenerationResponse,
)
from app.schemas.profile import Profile
from app.supabase_client import get_admin_client

router = APIRouter(tags=["generations"])


@router.post("/generations", status_code=status.HTTP_201_CREATED)
async def start_generation(
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
    result = (
        get_admin_client()
        .table("generation")
        .insert(
            {
                # generation.repo_name es texto libre de display; se reutiliza
                # tal cual para guardar repo_path (decision tomada con el
                # usuario antes de implementar: no se anade una columna nueva).
                "repo_name": body.repo_path or "",
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
        run_generation, generation_id, body.technologies, body.repo_path, body.kind, body.count
    )

    return StartGenerationResponse(id=generation_id)


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
            .select("id, type, statement, code, expected_answer")
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
