"""Rate limiting del agente (change resiliencia-agentes).

Identico a `agents/evaluator/app/rate_limit.py` (ver su docstring): su
unico llamador legitimo es el backend, identificado por la credencial de
servicio, no por un usuario final. Limitar por IP es aqui el equivalente
correcto; `60/minute` acota un bucle de reintentos sin molestar al uso
legitimo.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

DEFAULT_LIMIT = "60/minute"

limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_LIMIT])
