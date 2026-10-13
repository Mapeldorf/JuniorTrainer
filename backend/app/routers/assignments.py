import logging

from postgrest.exceptions import APIError

from fastapi import APIRouter, Depends, HTTPException, status

from app.answer_orchestrator import AnswerEvaluationFailed, evaluate_answer
from app.deps import require_student
from app.schemas.assignment import (
    AnswerRequest,
    AnswerResult,
    AssignmentDetail,
    AssignmentExerciseItem,
    AssignmentSummary,
)
from app.schemas.profile import Profile
from app.supabase_client import get_admin_client
from app.tracing import new_trace_id, record_answer_evaluation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assignments"])

# Codigo de Postgres para "unique_violation" (ver postgrest.exceptions.APIError
# -- PostgREST reenvia el codigo de error real de Postgres tal cual).
_UNIQUE_VIOLATION = "23505"


def _get_own_assignment_or_404(assignment_id: str, student_id: str) -> dict:
    """Carga una asignacion comprobando a la vez que pertenece al alumno
    (tareas 2.3/5.4, requisitos "Ver el detalle de una asignacion propia" y
    "Enviar una respuesta a un ejercicio de la propia asignacion"). Si la
    asignacion existe pero es de otro alumno, responde 404 igual que si no
    existiera -- no se revela que una asignacion de otro alumno existe
    (mismo criterio que `_get_block_or_404` en blocks.py, ver design.md)."""
    result = (
        get_admin_client()
        .table("assignment")
        .select("id, block_id, student_id, block_name, assigned_at")
        .eq("id", assignment_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows or rows[0]["student_id"] != student_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignacion no encontrada")
    return rows[0]


@router.get("/assignments")
async def list_my_assignments(
    student: Profile = Depends(require_student),
) -> list[AssignmentSummary]:
    """Lista las asignaciones del alumno autenticado, con su progreso
    (tarea 1.2, capacidad `student-assignments`, requisito "Listar las
    propias asignaciones", version modificada). El progreso se calcula
    con dos conteos por asignacion -- mismo patron que ya usa
    `get_block_progress` en `blocks.py` para el tech lead -- en vez de
    una subconsulta por fila (ver design.md - Decisions)."""
    rows = (
        get_admin_client()
        .table("assignment")
        .select("id, block_name, assigned_at")
        .eq("student_id", student.id)
        .order("assigned_at", desc=True)
        .execute()
        .data
        or []
    )
    if not rows:
        return []

    assignment_ids = [row["id"] for row in rows]

    total_by_assignment: dict[str, int] = {}
    for row in (
        get_admin_client()
        .table("assignment_exercise")
        .select("assignment_id")
        .in_("assignment_id", assignment_ids)
        .execute()
        .data
        or []
    ):
        total_by_assignment[row["assignment_id"]] = total_by_assignment.get(row["assignment_id"], 0) + 1

    answered_by_assignment: dict[str, int] = {}
    for row in (
        get_admin_client()
        .table("answer")
        .select("assignment_id")
        .in_("assignment_id", assignment_ids)
        .execute()
        .data
        or []
    ):
        answered_by_assignment[row["assignment_id"]] = answered_by_assignment.get(row["assignment_id"], 0) + 1

    return [
        AssignmentSummary(
            **row,
            answered_count=answered_by_assignment.get(row["id"], 0),
            total_count=total_by_assignment.get(row["id"], 0),
        )
        for row in rows
    ]


@router.get("/assignments/{assignment_id}")
async def get_my_assignment_detail(
    assignment_id: str,
    student: Profile = Depends(require_student),
) -> AssignmentDetail:
    """Detalle de una asignacion propia (tarea 1.3, capacidad
    `student-assignments`, requisito "Ver el detalle de una asignacion
    propia", version modificada): los ejercicios de la copia, en orden,
    hasta el primero sin responder inclusive -- nunca los posteriores --
    cada uno con su respuesta, verdict y justificacion si ya la tiene. El
    contenido (enunciado/codigo) se lee via `exercise_id`: la copia en
    `assignment_exercise` no duplica ese contenido, se apoya en que un
    `exercise` guardado es inmutable (ver design.md - Context)."""
    assignment = _get_own_assignment_or_404(assignment_id, student.id)

    exercise_rows = (
        get_admin_client()
        .table("assignment_exercise")
        .select("exercise_id, position")
        .eq("assignment_id", assignment_id)
        .order("position")
        .execute()
        .data
        or []
    )
    exercise_ids = [row["exercise_id"] for row in exercise_rows]

    exercises_by_id: dict[str, dict] = {}
    if exercise_ids:
        exercises_by_id = {
            row["id"]: row
            for row in (
                get_admin_client()
                .table("exercise")
                .select("id, statement, code")
                .in_("id", exercise_ids)
                .execute()
                .data
                or []
            )
        }

    answers_by_exercise: dict[str, dict] = {}
    if exercise_ids:
        answers_by_exercise = {
            row["exercise_id"]: row
            for row in (
                get_admin_client()
                .table("answer")
                .select("exercise_id, text, verdict, justification")
                .eq("assignment_id", assignment_id)
                .execute()
                .data
                or []
            )
        }

    # Al alumno no se le envian los ejercicios posteriores al primero sin
    # responder (seccion 3/9 de la especificacion): se corta la lista nada
    # mas encontrar uno sin respuesta, incluyendolo a el pero ninguno
    # despues. `exercise_rows` ya viene en orden por `position`.
    visible_rows: list[dict] = []
    for row in exercise_rows:
        visible_rows.append(row)
        if row["exercise_id"] not in answers_by_exercise:
            break

    items: list[AssignmentExerciseItem] = []
    for row in visible_rows:
        answer = answers_by_exercise.get(row["exercise_id"])
        items.append(
            AssignmentExerciseItem(
                exercise_id=row["exercise_id"],
                position=row["position"],
                statement=exercises_by_id[row["exercise_id"]]["statement"],
                code=exercises_by_id[row["exercise_id"]]["code"],
                answered=answer is not None,
                answer_text=answer["text"] if answer else None,
                verdict=answer["verdict"] if answer else None,
                justification=answer["justification"] if answer else None,
            )
        )

    return AssignmentDetail(
        id=assignment["id"],
        block_name=assignment["block_name"],
        assigned_at=assignment["assigned_at"],
        exercises=items,
    )


@router.post(
    "/assignments/{assignment_id}/exercises/{exercise_id}/answer",
    status_code=status.HTTP_201_CREATED,
)
async def answer_exercise(
    assignment_id: str,
    exercise_id: str,
    body: AnswerRequest,
    student: Profile = Depends(require_student),
) -> AnswerResult:
    """Envia y evalua la respuesta de un alumno a un ejercicio de una de
    sus propias asignaciones (tareas 5.4/5.5, capacidad `answer-evaluation`,
    requisitos "Enviar una respuesta a un ejercicio de la propia
    asignacion", "Un ejercicio de una asignacion solo se responde una
    vez" y "La evaluacion usa la copia de la asignacion, nunca el
    ejercicio original")."""
    _get_own_assignment_or_404(assignment_id, student.id)

    # El ejercicio tiene que estar en LA COPIA de esta asignacion (no en
    # el `exercise` original en general): requisito "Responder un
    # ejercicio que no esta en la propia asignacion".
    in_assignment = (
        get_admin_client()
        .table("assignment_exercise")
        .select("exercise_id")
        .eq("assignment_id", assignment_id)
        .eq("exercise_id", exercise_id)
        .limit(1)
        .execute()
        .data
    )
    if not in_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ese ejercicio no forma parte de esta asignacion",
        )

    # Pre-check de "ya respondido" (tarea 5.5): evita gastar las dos
    # llamadas A2A si ya hay una respuesta. La condicion de carrera entre
    # dos peticiones simultaneas la cubre el `except APIError` del insert
    # de mas abajo, no solo este pre-check.
    already_answered = (
        get_admin_client()
        .table("answer")
        .select("id")
        .eq("assignment_id", assignment_id)
        .eq("exercise_id", exercise_id)
        .limit(1)
        .execute()
        .data
    )
    if already_answered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este ejercicio ya tiene una respuesta registrada",
        )

    # Contenido a evaluar: SIEMPRE el del `exercise` referenciado por la
    # copia de la asignacion, nunca otra cosa -- un `exercise` guardado es
    # inmutable salvo `deleted_at` (ver design.md - Context), asi que esto
    # sigue siendo la misma copia aunque el ejercicio ya este eliminado.
    exercise_rows = (
        get_admin_client()
        .table("exercise")
        .select("statement, code, expected_answer")
        .eq("id", exercise_id)
        .limit(1)
        .execute()
        .data
    )
    exercise = exercise_rows[0]

    trace_id = new_trace_id()
    try:
        verdict, justification = await evaluate_answer(
            exercise["statement"],
            exercise["code"],
            exercise["expected_answer"],
            body.text,
            trace_id,
        )
    except AnswerEvaluationFailed as exc:
        # answer_evaluation.error_message guarda el detalle completo (tabla
        # interna, no expuesta por API); el detail de la respuesta HTTP no lo
        # incluye (propuesta api-error-handling), se registra aqui ademas.
        logger.exception("Fallo al evaluar la respuesta %s/%s", assignment_id, exercise_id)
        record_answer_evaluation(
            trace_id, assignment_id, exercise_id, status="error", error_message=str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se ha podido evaluar la respuesta",
        ) from exc

    try:
        insert_result = (
            get_admin_client()
            .table("answer")
            .insert(
                {
                    "assignment_id": assignment_id,
                    "exercise_id": exercise_id,
                    "text": body.text,
                    "verdict": verdict,
                    "justification": justification,
                }
            )
            .execute()
        )
    except APIError as exc:
        if exc.code == _UNIQUE_VIOLATION:
            # Carrera (tarea 5.5): otra peticion ha insertado la respuesta
            # entre el pre-check de arriba y este insert. La evaluacion ya
            # hecha se descarta -- no hay un segundo sitio donde guardarla.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este ejercicio ya tiene una respuesta registrada",
            ) from exc
        raise

    row = insert_result.data[0]
    record_answer_evaluation(trace_id, assignment_id, exercise_id, status="ready", verdict=verdict)
    return AnswerResult(
        exercise_id=exercise_id,
        verdict=verdict,
        justification=justification,
        answered_at=row["answered_at"],
    )
