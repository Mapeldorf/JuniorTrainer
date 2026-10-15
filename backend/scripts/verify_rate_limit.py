"""Verificacion del rate limiting estricto (tareas 5.2/5.3 de
rate-limiting-backend) en un entorno sin Supabase real.

El limite estricto se aplica en el decorador `@limiter.limit`, que corre
DESPUES de la dependencia de autenticacion: sin un token valido de Supabase
el endpoint responde 401 antes de llegar al limitador, asi que con las
credenciales dummy de este entorno no se puede forzar el 429 por HTTP.

Este script levanta la app ASGI en memoria (TestClient), sustituye la
autenticacion y los clientes de Supabase por dobles (sin red) y comprueba
que una rafaga supera el limite estricto y recibe 429 con el cuerpo
generico, sin que se invoque la Admin API de Supabase.

Uso (desde backend/, con el venv del backend):
    python -m scripts.verify_rate_limit
"""

from starlette.testclient import TestClient

import app.rate_limit as rate_limit
import app.routers.generations as generations
import app.routers.users as users
from app.deps import require_tech_lead
from app.main import app
from app.schemas.profile import Profile

_FAKE_USER_ID = "verify-rate-limit-user"
_GENERIC_BODY = {"detail": "Demasiadas peticiones, intentalo mas tarde"}


# --- Doble del cliente anon de Supabase, para la key function del limiter ---
class _FakeUser:
    id = _FAKE_USER_ID


class _FakeAuthResponse:
    user = _FakeUser()


class _FakeAnonAuth:
    def get_user(self, token: str) -> _FakeAuthResponse:
        return _FakeAuthResponse()


class _FakeAnonClient:
    auth = _FakeAnonAuth()


# --- Doble del cliente admin de Supabase (registra las llamadas) ---
_calls = {"invite": 0, "generation_insert": 0}


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def insert(self, row):
        _calls["generation_insert"] += 1
        return self

    def select(self, *args, **kwargs):
        return self

    def execute(self):
        return _FakeResult([{"id": "verify-generation-id"}])


class _FakeAdminAuthAdmin:
    def invite_user_by_email(self, email, options=None):
        _calls["invite"] += 1


class _FakeAdminAuth:
    admin = _FakeAdminAuthAdmin()


class _FakeAdminClient:
    auth = _FakeAdminAuth()

    def table(self, name):
        return _FakeQuery()


rate_limit.get_anon_client = lambda: _FakeAnonClient()

_admin = _FakeAdminClient()
users.get_admin_client = lambda: _admin
generations.get_admin_client = lambda: _admin

# La orquestacion en segundo plano no debe correr durante la verificacion.
generations.run_generation = lambda *args, **kwargs: None

# Autenticacion: perfil tech_lead fijo, sin validar token de Supabase.
app.dependency_overrides[require_tech_lead] = lambda: Profile(
    id=_FAKE_USER_ID, email="verify@example.com", name="Verify", role="tech_lead"
)

client = TestClient(app)
_HEADERS = {"Authorization": "Bearer verify-token"}


def _burst(path: str, body: dict, times: int) -> list[int]:
    codes: list[int] = []
    for _ in range(times):
        response = client.post(path, json=body, headers=_HEADERS)
        codes.append(response.status_code)
        if response.status_code == 429:
            assert response.json() == _GENERIC_BODY, response.json()
    return codes


def main() -> None:
    # POST /users: limite estricto 3/minute -> el 4.o en adelante es 429.
    users_codes = _burst("/users", {"name": "Alumno", "email": "verify-student@example.com"}, 5)
    print(f"POST /users       -> {users_codes}")
    assert users_codes[:3] == [201, 201, 201], users_codes
    assert users_codes[3:] == [429, 429], users_codes
    assert _calls["invite"] == 3, f"la Admin API se invoco {_calls['invite']} veces (esperado 3)"

    # POST /generations: limite estricto 5/minute -> el 6.o en adelante es 429.
    gens_body = {"technologies": ["Typescript"], "kind": "knowledge", "count": 1}
    gens_codes = _burst("/generations", gens_body, 7)
    print(f"POST /generations -> {gens_codes}")
    assert gens_codes[:5] == [201] * 5, gens_codes
    assert gens_codes[5:] == [429, 429], gens_codes
    assert _calls["generation_insert"] == 5, f"se inserto {_calls['generation_insert']} veces (esperado 5)"

    print("OK: 429 con cuerpo generico tras superar el limite estricto, sin llamar a la Admin API")


if __name__ == "__main__":
    main()
