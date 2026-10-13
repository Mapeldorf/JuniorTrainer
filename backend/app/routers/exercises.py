from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import require_tech_lead
from app.schemas.exercise import (
    ExerciseDeleteRequest,
    SaveExerciseRequest,
    SavedExercise,
    SavedExerciseListItem,
)
from app.schemas.generation import ExerciseType
from app.schemas.profile import Profile
from app.supabase_client import get_admin_client

router = APIRouter(tags=["exercises"])

_EXERCISE_FIELDS = "id, type, name, statement, code, expected_answer, saved, deleted_at"
# `generation(technologies, repo_name)` es un embed de PostgREST por la
# unica FK de exercise a generation (exercise.generation_id); no hace
# falta alias ni hint de columna porque no hay ambiguedad (0001_schema.sql).
_SAVED_EXERCISE_FIELDS = (
    "id, type, name, statement, code, expected_answer, saved, deleted_at, "
    "generation(technologies, repo_name)"
)


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


def _to_saved_exercise_list_item(row: dict, block_usage_count: int = 0) -> SavedExerciseListItem:
    """Aplana el embed de `generation` (tarea 1.5 de
    frontend-tech-lead-ejercicios) sobre los campos propios del ejercicio;
    solo para `GET /exercises` -- `SavedExercise` (guardar/eliminar) no
    cambia de forma."""
    generation = row.get("generation") or {"technologies": "", "repo_name": None}
    technologies_raw = generation.get("technologies") or ""
    return SavedExerciseListItem(
        id=row["id"],
        type=row["type"],
        name=row["name"],
        statement=row["statement"],
        code=row["code"],
        expected_answer=row["expected_answer"],
        technologies=[t.strip() for t in technologies_raw.split(",") if t.strip()],
        repo_path=generation.get("repo_name") or None,
        block_usage_count=block_usage_count,
    )


@router.post("/exercises/{exercise_id}/save")
async def save_exercise(
    exercise_id: str,
    body: SaveExerciseRequest | None = None,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> SavedExercise:
    """Guarda un ejercicio candidato como definitivo (tarea 2.2, capacidad
    exercise-catalog: "Guardar un ejercicio candidato como definitivo").
    A partir de aqui la base de datos ya hace el ejercicio inmutable salvo
    `deleted_at` (trigger `exercise_lock_after_saved`, 0001_schema.sql).

    `body.expected_answer` (tarea 1.4 de frontend-tech-lead-ejercicios) y
    `body.name` (change `ejercicios-con-nombre`, requisito "Guardar un
    candidato con el nombre editado") son opcionales: si vienen
    informados, sustituyen a la respuesta esperada y/o al nombre
    generados antes de guardar; si se omiten -- o se omite el body
    entero -- se guardan los originales (comportamiento sin cambios)."""
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

    update = {"saved": True}
    if body is not None and body.expected_answer is not None:
        update["expected_answer"] = body.expected_answer
    if body is not None and body.name is not None:
        update["name"] = body.name

    result = (
        get_admin_client().table("exercise").update(update).eq("id", exercise_id).execute()
    )
    return SavedExercise(**result.data[0])


@router.get("/exercises")
async def list_saved_exercises(
    type: ExerciseType | None = Query(default=None),
    q: str | None = Query(default=None, description="Texto a buscar en el nombre o en el enunciado"),
    _tech_lead: Profile = Depends(require_tech_lead),
) -> list[SavedExerciseListItem]:
    """Lista los ejercicios definitivos (tarea 2.3, capacidad exercise-catalog:
    "Listar y buscar ejercicios definitivos"): `saved = true`, no eliminados,
    filtrables por tipo y buscables por texto en el nombre o en el enunciado
    (change `ejercicios-con-nombre`, design.md decision 5: union aditiva,
    cualquier busqueda que antes encontraba algo por su enunciado lo sigue
    encontrando). Es la fuente para componer un bloque (POST /blocks).
    Incluye las tecnologias y el repositorio de la generacion de cada
    ejercicio (tarea 1.5 de frontend-tech-lead-ejercicios), sin filtrar por
    el estado de esa generacion -- la pantalla de guardados los necesita
    incluso cuando ya esta `done` (design.md decision 9)."""
    query = (
        get_admin_client()
        .table("exercise")
        .select(_SAVED_EXERCISE_FIELDS)
        .eq("saved", True)
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
    )
    if type is not None:
        query = query.eq("type", type)
    if q:
        query = query.or_(f"name.ilike.%{q}%,statement.ilike.%{q}%")

    result = query.execute()
    rows = result.data or []

    # tarea 2.2, design.md - decision D4: en cuantos bloques (activos o
    # eliminados) esta cada ejercicio, en una sola consulta agrupada sobre
    # los ids de esta pagina, no una por ejercicio.
    exercise_ids = [row["id"] for row in rows]
    usage_counts: dict[str, int] = {}
    if exercise_ids:
        usage_rows = (
            get_admin_client()
            .table("block_exercise")
            .select("exercise_id")
            .in_("exercise_id", exercise_ids)
            .execute()
            .data
            or []
        )
        for usage_row in usage_rows:
            usage_counts[usage_row["exercise_id"]] = usage_counts.get(usage_row["exercise_id"], 0) + 1

    return [
        _to_saved_exercise_list_item(row, block_usage_count=usage_counts.get(row["id"], 0))
        for row in rows
    ]


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
