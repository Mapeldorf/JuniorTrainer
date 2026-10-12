from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import require_tech_lead
from app.schemas.exercise import ExerciseDeleteRequest, SavedExercise
from app.schemas.generation import ExerciseType
from app.schemas.profile import Profile
from app.supabase_client import get_admin_client

router = APIRouter(tags=["exercises"])

_EXERCISE_FIELDS = "id, type, statement, code, expected_answer, saved, deleted_at"


def _get_exercise_or_404(exercise_id: str) -> dict:
    result = (
        get_admin_client()
        .table("exercise")
        .select(_EXERCISE_FIELDS)
        .eq("id", exercise_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejercicio no encontrado")
    return rows[0]


@router.post("/exercises/{exercise_id}/save")
async def save_exercise(
    exercise_id: str,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> SavedExercise:
    """Guarda un ejercicio candidato como definitivo (tarea 2.2, capacidad
    exercise-catalog: "Guardar un ejercicio candidato como definitivo").
    A partir de aqui la base de datos ya hace el ejercicio inmutable salvo
    `deleted_at` (trigger `exercise_lock_after_saved`, 0001_schema.sql)."""
    exercise = _get_exercise_or_404(exercise_id)

    if exercise["deleted_at"] is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El ejercicio esta eliminado y no se puede guardar",
        )
    if exercise["saved"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El ejercicio ya esta guardado",
        )

    result = (
        get_admin_client()
        .table("exercise")
        .update({"saved": True})
        .eq("id", exercise_id)
        .execute()
    )
    return SavedExercise(**result.data[0])


@router.get("/exercises")
async def list_saved_exercises(
    type: ExerciseType | None = Query(default=None),
    q: str | None = Query(default=None, description="Texto a buscar en el enunciado"),
    _tech_lead: Profile = Depends(require_tech_lead),
) -> list[SavedExercise]:
    """Lista los ejercicios definitivos (tarea 2.3, capacidad exercise-catalog:
    "Listar y buscar ejercicios definitivos"): `saved = true`, no eliminados,
    filtrables por tipo y buscables por texto en el enunciado. Es la fuente
    para componer un bloque (POST /blocks)."""
    query = (
        get_admin_client()
        .table("exercise")
        .select(_EXERCISE_FIELDS)
        .eq("saved", True)
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
    )
    if type is not None:
        query = query.eq("type", type)
    if q:
        query = query.ilike("statement", f"%{q}%")

    result = query.execute()
    return [SavedExercise(**row) for row in (result.data or [])]


@router.patch("/exercises/{exercise_id}")
async def delete_exercise(
    exercise_id: str,
    body: ExerciseDeleteRequest,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> SavedExercise:
    """Borrado logico de un ejercicio definitivo (tarea 2.4, capacidad
    exercise-catalog: "Eliminar logicamente un ejercicio definitivo").
    Deja de aparecer en `GET /exercises` y de poder anadirse a bloques
    nuevos (trigger `block_exercise_requires_saved`, 0001_schema.sql ya
    rechaza insertar en block_exercise un exercise_id con deleted_at
    informado); no afecta a bloques que ya lo contengan ni a copias de
    asignacion ya creadas, porque esas tablas no referencian deleted_at."""
    exercise = _get_exercise_or_404(exercise_id)

    if not exercise["saved"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se puede eliminar un ejercicio ya guardado como definitivo",
        )
    if exercise["deleted_at"] is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El ejercicio ya esta eliminado",
        )

    deleted_at = datetime.now(timezone.utc).isoformat()
    result = (
        get_admin_client()
        .table("exercise")
        .update({"deleted_at": deleted_at})
        .eq("id", exercise_id)
        .execute()
    )
    return SavedExercise(**result.data[0])
