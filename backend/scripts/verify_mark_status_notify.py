"""Verificacion de la tarea 1.2 de la propuesta
`long-polling-generaciones-pendientes`: `_mark_status` (`app/orchestrator.py`)
avisa a `app/generation_events.py` al cambiar el estado de una generacion.

No hace falta Supabase real ni los agentes A2A (eso ya lo cubre
`verify_generation_e2e.py`, que requiere los tres servicios en marcha con
credenciales reales): aqui se sustituye el cliente admin por un doble, igual
que `verify_rate_limit.py`, para ejercitar solo `_mark_status` y comprobar
que `wait_for_change` del mismo id se resuelve en cuanto se llama.

Uso (desde backend/, con el venv del backend):
    python -m scripts.verify_mark_status_notify
"""

import asyncio

import app.orchestrator as orchestrator
from app.generation_events import wait_for_change


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def update(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def execute(self):
        return _FakeResult([{"id": "verify-generation-id"}])


class _FakeAdminClient:
    def table(self, name):
        return _FakeQuery()


orchestrator.get_admin_client = lambda: _FakeAdminClient()


async def main() -> None:
    generation_id = "verify-mark-status-notify"

    async def _esperar() -> bool:
        return await wait_for_change(generation_id, timeout=5.0)

    espera = asyncio.create_task(_esperar())
    await asyncio.sleep(0.05)  # deja que la espera se registre antes de avisar
    orchestrator._mark_status(generation_id, "ready")

    resultado = await espera
    assert resultado is True, "wait_for_change deberia resolverse al llamar _mark_status"
    print("OK: _mark_status notifica el cambio de estado a quien lo esta esperando")


if __name__ == "__main__":
    asyncio.run(main())
