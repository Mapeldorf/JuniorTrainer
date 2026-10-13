"""Rate limiting del backend (propuesta rate-limiting-backend).

Limita la frecuencia de peticiones por usuario autenticado, no por IP:
las rutas afectadas ya exigen un JWT de Supabase, asi que identificar al
llamante por el `id` de usuario evita que compartir IP/NAT comparta
cuota y evita esquivar el limite cambiando de IP.

La key function revalida el token con el cliente anon de Supabase, igual
que `get_current_profile` (`app/deps.py`): slowapi llama a `key_func` de
forma sincrona (no soporta corutinas), y el cliente de supabase-py ya es
sincrono, asi que no hace falta duplicar logica async. Las peticiones sin
token valido (rutas publicas, o un JWT invalido que de todos modos sera
rechazado con 401 mas adelante) caen al limite por IP.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.supabase_client import get_anon_client

# Limites deliberadamente estrictos: ningun uso legitimo necesita mas que
# esto, y limites bajos reducen el margen de abuso (fuerza bruta, gasto de
# LLM) mas que limites holgados. Ver design.md de la propuesta.
DEFAULT_LIMIT = "30/minute"
INVITE_STUDENT_LIMIT = "3/minute"
START_GENERATION_LIMIT = "5/minute"

_BEARER_PREFIX = "bearer "


def get_rate_limit_key(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith(_BEARER_PREFIX):
        return get_remote_address(request)

    token = auth_header[len(_BEARER_PREFIX) :].strip()
    try:
        user_response = get_anon_client().auth.get_user(token)
    except Exception:
        return get_remote_address(request)

    user = user_response.user if user_response else None
    if user is None:
        return get_remote_address(request)
    return user.id


limiter = Limiter(key_func=get_rate_limit_key, default_limits=[DEFAULT_LIMIT])
