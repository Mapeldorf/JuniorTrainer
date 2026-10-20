"""Verificacion de `GET /generations/pending/wait` (tareas 2.1/2.2 de la
propuesta `long-polling-generaciones-pendientes`), con un doble del
cliente admin de Supabase (mismo patron que `verify_rate_limit.py`): sin
red, sin agentes A2A, sin Supabase real.

Llama al handler del endpoint directamente (no via `TestClient`/HTTP):
asi la notificacion de un cambio de estado se dispara dentro del MISMO
event loop que la espera, evitando los problemas de seguridad entre hilos
de llamar a un `asyncio.Event` desde fuera de su loop.

Uso (desde backend/, con el venv del backend):
    python -m scripts.verify_pending_wait_endpoint
"""

import asyncio
import time

import app.routers.generations as generations
from app.generation_events import notify_status_change
from app.schemas.profile import Profile

_FAKE_PROFILE = Profile(id="verify-user", email="verify@example.com", name="Verify", role="tech_lead")


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, rows: list[dict]):
        self._rows = rows
        self._in_filters: list[tuple[str, list]] = []

    def select(self, *args, **kwargs):
        return self

    def in_(self, column: str, values: list):
        self._in_filters.append((column, values))
        return self

    def order(self, column: str, desc: bool = False):
        self._rows = sorted(self._rows, key=lambda row: row[column], reverse=desc)
        return self

    def execute(self):
        rows = self._rows
        for column, values in self._in_filters:
            rows = [row for row in rows if row[column] in values]
        return _FakeResult(list(rows))


class _FakeAdminClient:
    def __init__(self, rows: list[dict]):
        self.rows = rows

    def table(self, name: str):
        assert name == "generation", name
        return _FakeQuery(self.rows)


def _row(generation_id: str, status: str, created_at: str) -> dict:
    return {
        "id": generation_id,
        "status": status,
        "technologies": "Git",
        "repo_name": "",
        "kind": "knowledge",
        "error_message": None,
        "created_at": created_at,
    }


async def _check_sin_generaciones_en_curso_responde_ya() -> None:
    rows = [_row("g-ready", "ready", "2026-01-01T00:00:00Z")]
    generations.get_admin_client = lambda: _FakeAdminClient(rows)

    start = time.monotonic()
    result = await generations.wait_for_pending_change(_profile=_FAKE_PROFILE)
    elapsed = time.monotonic() - start

    assert elapsed < 0.1, f"sin generaciones 'generating' no deberia esperar nada, tardo {elapsed:.2f}s"
    assert [g.id for g in result] == ["g-ready"], result


async def _check_cambia_antes_del_timeout() -> None:
    rows = [_row("g-en-curso", "generating", "2026-01-01T00:00:00Z")]
    generations.get_admin_client = lambda: _FakeAdminClient(rows)
    generations.PENDING_WAIT_TIMEOUT_SECONDS = 5.0

    async def _completar_en_breve() -> None:
        await asyncio.sleep(0.1)
        rows[0]["status"] = "ready"
        notify_status_change("g-en-curso")

    start = time.monotonic()
    result, _ = await asyncio.gather(
        generations.wait_for_pending_change(_profile=_FAKE_PROFILE),
        _completar_en_breve(),
    )
    elapsed = time.monotonic() - start

    assert elapsed < 1.0, f"deberia responder en cuanto cambia, no esperar el timeout, tardo {elapsed:.2f}s"
    assert [g.id for g in result] == ["g-en-curso"], result
    assert result[0].status == "ready", result


async def _check_nada_cambia_responde_al_timeout() -> None:
    rows = [_row("g-bloqueada", "generating", "2026-01-01T00:00:00Z")]
    generations.get_admin_client = lambda: _FakeAdminClient(rows)
    generations.PENDING_WAIT_TIMEOUT_SECONDS = 0.2

    start = time.monotonic()
    result = await generations.wait_for_pending_change(_profile=_FAKE_PROFILE)
    elapsed = time.monotonic() - start

    assert elapsed >= 0.18, f"deberia esperar aproximadamente el timeout, tardo {elapsed:.2f}s"
    assert [g.id for g in result] == ["g-bloqueada"], result
    assert result[0].status == "generating", result


async def _check_generacion_en_error_desaparece() -> None:
    rows = [_row("g-falla", "generating", "2026-01-01T00:00:00Z")]
    generations.get_admin_client = lambda: _FakeAdminClient(rows)
    generations.PENDING_WAIT_TIMEOUT_SECONDS = 5.0

    async def _fallar_en_breve() -> None:
        await asyncio.sleep(0.1)
        rows[0]["status"] = "error"
        notify_status_change("g-falla")

    result, _ = await asyncio.gather(
        generations.wait_for_pending_change(_profile=_FAKE_PROFILE),
        _fallar_en_breve(),
    )

    assert result == [], f"una generacion en error no deberia aparecer en el listado de pendientes, {result}"


async def main() -> None:
    await _check_sin_generaciones_en_curso_responde_ya()
    print("OK: sin generaciones en curso, responde de inmediato")

    await _check_cambia_antes_del_timeout()
    print("OK: una generacion que pasa a ready responde antes del timeout, con el listado actualizado")

    await _check_nada_cambia_responde_al_timeout()
    print("OK: si nada cambia, responde al cumplirse el timeout con el listado tal cual estaba")

    await _check_generacion_en_error_desaparece()
    print("OK: una generacion que pasa a error deja de aparecer en la respuesta")


if __name__ == "__main__":
    asyncio.run(main())
