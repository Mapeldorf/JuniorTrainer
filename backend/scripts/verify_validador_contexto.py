"""Verificacion manual (sin servidor HTTP, sin agentes reales) del change
`validador-contexto-generacion`: cada llamador del validador manda el campo
`context` correcto en el payload A2A.

- `backend/app/routers/technologies.py` (`create_technology`, alta de una
  tecnologia nueva) debe mandar `context="catalog_entry"`.
- `backend/app/orchestrator.py` (`_call_validator`, puerta previa a una
  generacion) debe mandar `context="generation"`.

Se sustituye `send_a2a_task` por un doble que captura el payload recibido,
mismo patron que `verify_technology_catalog_duplicates.py` y
`verify_ejercicios_tech_lead.py`. No necesita el agente validador arrancado,
Supabase, ni ningun servicio real: `technologies.create_technology` necesita
un `admin` de Supabase solo para la comprobacion de duplicado exacto
(`ilike`) ANTES de llegar al validador, asi que este script tambien
sustituye `get_admin_client` por un doble que simula "no existe todavia".

Uso (desde backend/, con el venv del backend activo):
    python -m scripts.verify_validador_contexto
"""

import asyncio

import app.orchestrator as orchestrator
import app.routers.technologies as technologies
from app.schemas.profile import Profile
from app.schemas.technology import NewTechnologyRequest

_captured: dict = {}


async def _capturing_send_a2a_task(url, data, *, trace_id=None):
    _captured["url"] = url
    _captured["data"] = data
    return {"valid": True, "reason": "ok", "invalid_technologies": [], "duplicate_technologies": []}


class _FakeQuery:
    def __init__(self) -> None:
        self._inserted: dict | None = None

    def select(self, *_a, **_kw):
        return self

    def ilike(self, *_a, **_kw):
        return self

    def insert(self, payload: dict, *_a, **_kw):
        self._inserted = {"id": "fake-id", **payload}
        return self

    def limit(self, *_a, **_kw):
        return self

    def execute(self):
        class _Result:
            def __init__(self, data: list) -> None:
                self.data = data

        return _Result([self._inserted] if self._inserted is not None else [])


class _FakeAdmin:
    def table(self, _name):
        return _FakeQuery()


def check_technologies_router_sends_catalog_entry() -> None:
    _captured.clear()
    original_send = technologies.send_a2a_task
    original_admin = technologies.get_admin_client
    technologies.send_a2a_task = _capturing_send_a2a_task
    technologies.get_admin_client = lambda: _FakeAdmin()
    try:
        asyncio.run(
            technologies.create_technology(
                NewTechnologyRequest(name="Verificacion contexto"),
                _profile=Profile(id="t1", email="tech@example.com", name="Tech Lead", role="tech_lead"),
            )
        )
    finally:
        technologies.send_a2a_task = original_send
        technologies.get_admin_client = original_admin

    assert _captured["data"].get("context") == "catalog_entry", (
        f"el alta deberia mandar context='catalog_entry', se mando: {_captured['data']!r}"
    )
    print("technologies.py (alta): OK -> context='catalog_entry'")


def check_orchestrator_sends_generation() -> None:
    _captured.clear()
    original_send = orchestrator.send_a2a_task
    orchestrator.send_a2a_task = _capturing_send_a2a_task
    try:
        asyncio.run(orchestrator._call_validator(["React", "FastAPI"], "trace-verificacion"))
    finally:
        orchestrator.send_a2a_task = original_send

    assert _captured["data"].get("context") == "generation", (
        f"la generacion deberia mandar context='generation', se mando: {_captured['data']!r}"
    )
    print("orchestrator.py (_call_validator): OK -> context='generation'")


def main() -> None:
    check_technologies_router_sends_catalog_entry()
    check_orchestrator_sends_generation()


if __name__ == "__main__":
    main()
