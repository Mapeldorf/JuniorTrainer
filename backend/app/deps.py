from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.profile import Profile
from app.supabase_client import get_admin_client, get_anon_client

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Profile:
    """Valida el JWT de Supabase del header Authorization y carga el Profile
    (nombre + rol) correspondiente.

    La validacion se delega en Supabase Auth (GET /auth/v1/user) en vez de
    verificar la firma en local: evita depender del algoritmo de firma que
    use el proyecto (HS256 con secreto compartido o las claves asimetricas
    mas nuevas) y de la rotacion de claves. Si el volumen de peticiones lo
    justifica, se puede sustituir por una verificacion JWKS local.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de autenticacion",
        )

    token = credentials.credentials
    try:
        user_response = get_anon_client().auth.get_user(token)
    except Exception as exc:  # token invalido, caducado o malformado
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o caducado",
        ) from exc

    user = user_response.user if user_response else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o caducado",
        )

    # Se lee con el cliente admin (service_role) para no depender de RLS aqui:
    # el propio endpoint decide despues que puede ver cada rol.
    result = (
        get_admin_client()
        .table("profile")
        .select("id, email, name, role")
        .eq("id", user.id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        # El trigger on_auth_user_created crea el Profile al confirmar el alta;
        # si no existe todavia es que el usuario aun no ha completado el alta.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene un perfil asociado todavia",
        )

    return Profile(**rows[0])


async def require_tech_lead(
    profile: Profile = Depends(get_current_profile),
) -> Profile:
    if profile.role != "tech_lead":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere rol tech_lead",
        )
    return profile
