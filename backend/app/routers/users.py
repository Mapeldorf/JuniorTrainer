from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.deps import require_tech_lead
from app.schemas.profile import InviteStudentRequest, Profile
from app.supabase_client import get_admin_client

router = APIRouter(tags=["users"])


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
