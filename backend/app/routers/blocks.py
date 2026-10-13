from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import require_tech_lead
from app.schemas.block import (
    AssignBlockRequest,
    AssignBlockResponse,
    AssignedStudentSummary,
    AssignmentResult,
    BlockCreateRequest,
    BlockDetail,
    BlockExerciseItem,
    BlockSummary,
    BlockUpdateRequest,
    ExerciseProgress,
    StudentProgress,
)
from app.schemas.exercise import SavedExercise
from app.schemas.profile import Profile
from app.supabase_client import get_admin_client

router = APIRouter(tags=["blocks"])


def _get_block_or_404(block_id: str) -> dict:
    result = (
        get_admin_client()
        .table("block")
        .select("id, name, created_at, updated_at, deleted_at")
        .eq("id", block_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bloque no encontrado")
    return rows[0]


def _block_has_answers(block_id: str) -> bool:
    assignments = (
        get_admin_client().table("assignment").select("id").eq("block_id", block_id).execute()
    )
    assignment_ids = [row["id"] for row in (assignments.data or [])]
    if not assignment_ids:
        return False
    answers = (
        get_admin_client()
        .table("answer")
        .select("id")
        .in_("assignment_id", assignment_ids)
        .limit(1)
        .execute()
    )
    return bool(answers.data)


def _validate_exercise_ids(exercise_ids: list[str]) -> None:
    """Comparte la comprobacion de "solo ejercicios definitivos, sin
    duplicados" entre crear (3.2) y editar (3.4) un bloque. La base de
    datos ya rechaza anadir un ejercicio no guardado o eliminado a
    `block_exercise` (trigger `block_exercise_requires_saved`,
    0001_schema.sql); esta comprobacion en Python solo da un mensaje de
    error mejor antes de intentarlo."""
    if len(set(exercise_ids)) != len(exercise_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La lista de ejercicios tiene ids repetidos",
        )

    result = (
        get_admin_client()
        .table("exercise")
        .select("id, saved, deleted_at")
        .in_("id", exercise_ids)
        .execute()
    )
    rows = {row["id"]: row for row in (result.data or [])}
    for exercise_id in exercise_ids:
        row = rows.get(exercise_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El ejercicio {exercise_id} no existe",
            )
        if not row["saved"] or row["deleted_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El ejercicio {exercise_id} no es definitivo o esta eliminado",
            )


def _get_block_detail(block: dict) -> BlockDetail:
    rows = (
        get_admin_client()
        .table("block_exercise")
        .select(
            "position, "
            "exercise:exercise_id(id, type, name, statement, code, expected_answer, deleted_at)"
        )
        .eq("block_id", block["id"])
        .order("position")
        .execute()
    )
    exercises = []
    for row in rows.data or []:
        # tarea 1.3, design.md - decision D3: `deleted_at` solo se usa
        # para derivar `exercise_deleted`, nunca llega a `SavedExercise`.
        exercise_row = dict(row["exercise"])
        exercise_deleted = exercise_row.pop("deleted_at", None) is not None
        exercises.append(
            BlockExerciseItem(
                position=row["position"],
                exercise=SavedExercise(**exercise_row),
                exercise_deleted=exercise_deleted,
            )
        )
    # tarea 1.3, design.md - decision D2: mismo significado y misma
    # funcion que en el listado (tarea 1.2), aqui para un solo bloque.
    return BlockDetail(**block, exercises=exercises, resolved=_block_has_answers(block["id"]))


@router.post("/blocks", status_code=status.HTTP_201_CREATED)
async def create_block(
    body: BlockCreateRequest,
    tech_lead: Profile = Depends(require_tech_lead),
) -> BlockDetail:
    """Crea un bloque (tarea 3.2, capacidad exercise-blocks: "Crear un
    bloque de ejercicios"). `body.exercise_ids` ya viene validado a 1-100
    por `BlockCreateRequest`; aqui solo falta que todos sean definitivos
    y distintos entre si."""
    _validate_exercise_ids(body.exercise_ids)

    block_result = (
        get_admin_client()
        .table("block")
        .insert({"name": body.name, "created_by": tech_lead.id})
        .execute()
    )
    block = block_result.data[0]

    try:
        get_admin_client().table("block_exercise").insert(
            [
                {"block_id": block["id"], "exercise_id": exercise_id, "position": position}
                for position, exercise_id in enumerate(body.exercise_ids, start=1)
            ]
        ).execute()
    except Exception:
        # No hay transaccion entre las dos llamadas REST; si la segunda
        # falla, se deshace el bloque para no dejar uno vacio huerfano.
        get_admin_client().table("block").delete().eq("id", block["id"]).execute()
        raise

    return _get_block_detail(block)


@router.get("/blocks")
async def list_blocks(
    deleted: bool = Query(default=False, description="true para 'Bloques eliminados'"),
    _tech_lead: Profile = Depends(require_tech_lead),
) -> list[BlockSummary]:
    """Lista los bloques (tarea 3.3, capacidad exercise-blocks: "Listar y
    ver el detalle de un bloque"), activos o eliminados segun `deleted`."""
    query = get_admin_client().table("block").select(
        "id, name, created_at, updated_at, deleted_at"
    )
    query = query.is_("deleted_at", "null") if not deleted else query.not_.is_("deleted_at", "null")
    blocks = query.order("created_at", desc=True).execute().data or []

    if not blocks:
        return []

    block_ids = [block["id"] for block in blocks]
    exercise_rows = (
        get_admin_client()
        .table("block_exercise")
        .select("block_id")
        .in_("block_id", block_ids)
        .execute()
        .data
        or []
    )
    counts: dict[str, int] = {}
    for row in exercise_rows:
        counts[row["block_id"]] = counts.get(row["block_id"], 0) + 1

    # tarea 1.2, design.md - decision D1/D2: una sola consulta extra de
    # asignaciones (con el nombre del alumno) para toda la pagina, en vez
    # de pedir el detalle de cada bloque por separado.
    assignment_rows = (
        get_admin_client()
        .table("assignment")
        .select("id, block_id, student_id, profile:student_id(name)")
        .in_("block_id", block_ids)
        .execute()
        .data
        or []
    )
    assigned_students_by_block: dict[str, list[AssignedStudentSummary]] = {}
    assignment_ids_by_block: dict[str, list[str]] = {}
    for row in assignment_rows:
        assigned_students_by_block.setdefault(row["block_id"], []).append(
            AssignedStudentSummary(id=row["student_id"], name=row["profile"]["name"])
        )
        assignment_ids_by_block.setdefault(row["block_id"], []).append(row["id"])

    # "Resuelto" = alguna de las asignaciones del bloque tiene al menos
    # una respuesta registrada (misma regla que `_block_has_answers`,
    # aqui resuelta para todos los bloques de la pagina de una vez).
    resolved_block_ids: set[str] = set()
    all_assignment_ids = [row["id"] for row in assignment_rows]
    if all_assignment_ids:
        answered_assignment_ids = {
            row["assignment_id"]
            for row in (
                get_admin_client()
                .table("answer")
                .select("assignment_id")
                .in_("assignment_id", all_assignment_ids)
                .execute()
                .data
                or []
            )
        }
        for block_id, assignment_ids in assignment_ids_by_block.items():
            if any(aid in answered_assignment_ids for aid in assignment_ids):
                resolved_block_ids.add(block_id)

    return [
        BlockSummary(
            **block,
            exercise_count=counts.get(block["id"], 0),
            assigned_students=assigned_students_by_block.get(block["id"], []),
            resolved=block["id"] in resolved_block_ids,
        )
        for block in blocks
    ]


@router.get("/blocks/{block_id}")
async def get_block(
    block_id: str,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> BlockDetail:
    """Detalle de un bloque, eliminado o no (tarea 3.3)."""
    block = _get_block_or_404(block_id)
    return _get_block_detail(block)


@router.patch("/blocks/{block_id}")
async def update_block(
    block_id: str,
    body: BlockUpdateRequest,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> BlockDetail:
    """Edita el nombre y/o la composicion de un bloque (tarea 3.4,
    capacidad exercise-blocks: "Editar un bloque solo si nadie lo ha
    resuelto"). Reemplazo completo de `exercise_ids`, no un diff (ver
    design.md - Decisions). Se comprueba en Python que el bloque no tiene
    respuestas antes de tocar nada, para no dejar una mitad del cambio
    aplicada; el trigger `block_lock_after_answered`/`block_exercise_lock_after_answered`
    (migracion 0005) sigue siendo quien lo garantiza a nivel de datos."""
    block = _get_block_or_404(block_id)

    if body.name is None and body.exercise_ids is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hay que indicar al menos name o exercise_ids",
        )

    if _block_has_answers(block_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El bloque ya tiene respuestas registradas: no se puede editar",
        )

    if body.exercise_ids is not None:
        _validate_exercise_ids(body.exercise_ids)

    if body.name is not None:
        get_admin_client().table("block").update({"name": body.name}).eq("id", block_id).execute()

    if body.exercise_ids is not None:
        get_admin_client().table("block_exercise").delete().eq("block_id", block_id).execute()
        get_admin_client().table("block_exercise").insert(
            [
                {"block_id": block_id, "exercise_id": exercise_id, "position": position}
                for position, exercise_id in enumerate(body.exercise_ids, start=1)
            ]
        ).execute()

    updated_block = _get_block_or_404(block_id)
    return _get_block_detail(updated_block)


@router.delete("/blocks/{block_id}")
async def delete_block(
    block_id: str,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> BlockDetail:
    """Borrado logico de un bloque (tarea 3.5, capacidad exercise-blocks:
    "Eliminar un bloque sin afectar a quien lo tiene asignado"): pasa a
    "Bloques eliminados", deja de poder asignarse (ver POST
    /blocks/{id}/assignments), pero sigue en solo lectura con sus
    asignaciones y resultados existentes."""
    block = _get_block_or_404(block_id)
    if block["deleted_at"] is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El bloque ya esta eliminado")

    deleted_at = datetime.now(timezone.utc).isoformat()
    get_admin_client().table("block").update({"deleted_at": deleted_at}).eq("id", block_id).execute()

    updated_block = _get_block_or_404(block_id)
    return _get_block_detail(updated_block)


@router.post("/blocks/{block_id}/assignments", status_code=status.HTTP_201_CREATED)
async def assign_block(
    block_id: str,
    body: AssignBlockRequest,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> AssignBlockResponse:
    """Asigna un bloque a uno o varios alumnos (tarea 4.2, capacidad
    block-assignment: "Asignar un bloque crea una copia inmutable de sus
    ejercicios"). Procesa cada alumno por separado: quien ya tenia el
    bloque asignado se omite sin error: no se crea una segunda asignacion,
    pero tampoco falla la asignacion de los demas (ver design.md -
    Decisions). Si algun `student_id` no es un alumno valido, o el bloque
    esta eliminado, no se crea ninguna asignacion."""
    block = _get_block_or_404(block_id)
    if block["deleted_at"] is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El bloque esta eliminado: no se puede asignar",
        )

    student_ids = list(dict.fromkeys(body.student_ids))  # unicos, orden estable
    profiles = (
        get_admin_client()
        .table("profile")
        .select("id, role")
        .in_("id", student_ids)
        .execute()
        .data
        or []
    )
    profiles_by_id = {row["id"]: row for row in profiles}
    for student_id in student_ids:
        row = profiles_by_id.get(student_id)
        if row is None or row["role"] != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{student_id} no es un alumno valido",
            )

    existing = (
        get_admin_client()
        .table("assignment")
        .select("student_id")
        .eq("block_id", block_id)
        .in_("student_id", student_ids)
        .execute()
        .data
        or []
    )
    already_assigned = {row["student_id"] for row in existing}
    to_create = [sid for sid in student_ids if sid not in already_assigned]

    created_assignments: list[dict] = []
    if to_create:
        block_exercises = (
            get_admin_client()
            .table("block_exercise")
            .select("exercise_id, position")
            .eq("block_id", block_id)
            .execute()
            .data
            or []
        )

        insert_result = (
            get_admin_client()
            .table("assignment")
            .insert(
                [
                    {"block_id": block_id, "student_id": sid, "block_name": block["name"]}
                    for sid in to_create
                ]
            )
            .execute()
        )
        created_assignments = insert_result.data or []

        try:
            get_admin_client().table("assignment_exercise").insert(
                [
                    {
                        "assignment_id": assignment["id"],
                        "exercise_id": be["exercise_id"],
                        "position": be["position"],
                    }
                    for assignment in created_assignments
                    for be in block_exercises
                ]
            ).execute()
        except Exception:
            # Igual que en create_block: sin transaccion entre llamadas,
            # se deshacen las asignaciones recien creadas si falla la copia.
            get_admin_client().table("assignment").delete().in_(
                "id", [a["id"] for a in created_assignments]
            ).execute()
            raise

    results = [
        AssignmentResult(
            student_id=sid, status="already_assigned" if sid in already_assigned else "created"
        )
        for sid in student_ids
    ]
    return AssignBlockResponse(results=results)


@router.get("/blocks/{block_id}/assignments")
async def get_block_progress(
    block_id: str,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> list[StudentProgress]:
    """Progreso por alumno asignado (tarea 4.3, modificado por la tarea 6.1
    de la capacidad block-assignment: "Consultar el progreso de un bloque
    asignado"): que ejercicios de su copia tienen respuesta y, si la hay,
    el verdict (correct/incomplete/incorrect) de la valoracion."""
    _get_block_or_404(block_id)

    assignments = (
        get_admin_client()
        .table("assignment")
        .select("id, student_id, profile:student_id(name)")
        .eq("block_id", block_id)
        .execute()
        .data
        or []
    )
    if not assignments:
        return []

    assignment_ids = [a["id"] for a in assignments]

    # tarea 3.2, design.md - decision D5: tipo y enunciado se leen desde
    # la copia propia de cada asignacion (join con `exercise` aqui), nunca
    # desde la composicion actual del bloque -- pueden diferir si el
    # bloque se edito entre dos asignaciones, ambas antes de la primera
    # respuesta.
    exercise_rows = (
        get_admin_client()
        .table("assignment_exercise")
        .select("assignment_id, exercise_id, position, exercise:exercise_id(type, name, statement)")
        .in_("assignment_id", assignment_ids)
        .order("position")
        .execute()
        .data
        or []
    )
    answer_rows = (
        get_admin_client()
        .table("answer")
        .select("assignment_id, exercise_id, verdict, text, justification")
        .in_("assignment_id", assignment_ids)
        .execute()
        .data
        or []
    )
    # tarea 3.2 (requisito "Consultar el progreso de un bloque asignado",
    # version modificada): ya no basta con el verdict, tambien se informa
    # el texto de la respuesta y la justificacion de cada una.
    answer_by_pair: dict[tuple[str, str], dict] = {
        (row["assignment_id"], row["exercise_id"]): row for row in answer_rows
    }

    exercises_by_assignment: dict[str, list[dict]] = {}
    for row in exercise_rows:
        exercises_by_assignment.setdefault(row["assignment_id"], []).append(row)

    progress: list[StudentProgress] = []
    for assignment in assignments:
        assignment_id = assignment["id"]
        exercises: list[ExerciseProgress] = []
        for row in exercises_by_assignment.get(assignment_id, []):
            answer = answer_by_pair.get((assignment_id, row["exercise_id"]))
            exercises.append(
                ExerciseProgress(
                    exercise_id=row["exercise_id"],
                    position=row["position"],
                    name=row["exercise"]["name"],
                    type=row["exercise"]["type"],
                    statement=row["exercise"]["statement"],
                    answered=answer is not None,
                    verdict=answer["verdict"] if answer is not None else None,
                    # la columna de la tabla es `text`; el DTO la expone como
                    # `answer_text` (mismo mapeo que `assignments.py`).
                    answer_text=answer["text"] if answer is not None else None,
                    justification=answer["justification"] if answer is not None else None,
                )
            )
        progress.append(
            StudentProgress(
                student_id=assignment["student_id"],
                student_name=assignment["profile"]["name"],
                assignment_id=assignment_id,
                exercises=exercises,
            )
        )
    return progress
