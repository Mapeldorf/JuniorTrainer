from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.deps import require_tech_lead
from app.schemas.block import ExerciseProgress, StudentBlockAssignment
from app.schemas.profile import InviteStudentRequest, Profile, StudentSummary
from app.supabase_client import get_admin_client

router = APIRouter(tags=["users"])


def _get_student_or_404(student_id: str) -> dict:
    result = (
        get_admin_client()
        .table("profile")
        .select("id, role")
        .eq("id", student_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows or rows[0]["role"] != "student":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado")
    return rows[0]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def invite_student(
    body: InviteStudentRequest,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> dict[str, str]:
    """Alta de un alumno (seccion 9: POST /users, solo tech lead).

    Da de alta a un alumno invitandolo por email con la Admin API de
    Supabase: Supabase le envia el correo para elegir su contrasena (no hay
    autorregistro ni contrasena temporal) y el trigger on_auth_user_created
    crea su Profile con role='student' al confirmarse el alta."""
    settings = get_settings()
    email = body.email.lower()

    try:
        get_admin_client().auth.admin.invite_user_by_email(
            email,
            {
                "data": {"name": body.name, "role": "student"},
                "redirect_to": f"{settings.frontend_url}/set-password",
            },
        )
    except Exception as exc:
        # La Admin API tambien falla asi para otros errores de validacion;
        # 409 es la lectura mas probable (email ya existente) que pide la spec.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se ha podido invitar a {email}: {exc}",
        ) from exc

    return {"email": email, "status": "invited"}


@router.get("/users")
async def list_students(
    _tech_lead: Profile = Depends(require_tech_lead),
) -> list[StudentSummary]:
    """Listado de alumnos (tarea 7.1, capacidad user-auth modificada,
    requisito "Listar alumnos"): solo tech lead, solo perfiles
    role='student'."""
    rows = (
        get_admin_client()
        .table("profile")
        .select("id, name, email")
        .eq("role", "student")
        .execute()
        .data
        or []
    )
    return [StudentSummary(**row) for row in rows]


@router.get("/users/{student_id}/blocks")
async def get_student_blocks(
    student_id: str,
    _tech_lead: Profile = Depends(require_tech_lead),
) -> list[StudentBlockAssignment]:
    """Asignaciones de un alumno a traves de todos sus bloques (tarea 1.2,
    capacidad `block-assignment`, requisito "Consultar las asignaciones de
    un alumno a traves de sus bloques"): vista simetrica de
    `get_block_progress` (`blocks.py`), pero filtrada por `student_id` en
    vez de por `block_id`. Incluye asignaciones de bloques ya eliminados
    (design.md - decision D3): no se filtra por `block.deleted_at`, y el
    nombre de cada bloque se lee de `assignment.block_name` (la misma
    copia inmutable que ya guarda `assign_block`), no del `block` actual."""
    _get_student_or_404(student_id)

    assignments = (
        get_admin_client()
        .table("assignment")
        .select("id, block_id, block_name")
        .eq("student_id", student_id)
        .order("assigned_at")
        .execute()
        .data
        or []
    )
    if not assignments:
        return []

    assignment_ids = [a["id"] for a in assignments]

    # Mismo patron que get_block_progress (blocks.py, tarea 3.2): tipo y
    # enunciado desde la copia inmutable de la asignacion, nunca desde la
    # composicion actual del bloque.
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
    answer_by_pair: dict[tuple[str, str], dict] = {
        (row["assignment_id"], row["exercise_id"]): row for row in answer_rows
    }

    exercises_by_assignment: dict[str, list[dict]] = {}
    for row in exercise_rows:
        exercises_by_assignment.setdefault(row["assignment_id"], []).append(row)

    results: list[StudentBlockAssignment] = []
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
                    answer_text=answer["text"] if answer is not None else None,
                    justification=answer["justification"] if answer is not None else None,
                )
            )
        results.append(
            StudentBlockAssignment(
                assignment_id=assignment_id,
                block_id=assignment["block_id"],
                block_name=assignment["block_name"],
                exercises=exercises,
            )
        )
    return results
