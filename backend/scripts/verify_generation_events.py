"""Verificacion de `app/generation_events.py` (tarea 1.1 de la propuesta
`long-polling-generaciones-pendientes`): sin FastAPI ni Supabase de por
medio, solo el registro en memoria de eventos de cambio de estado.

Uso (desde backend/, con el venv del backend):
    python -m scripts.verify_generation_events
"""

import asyncio
import time

from app.generation_events import notify_status_change, wait_for_change


async def _check_notify_sin_nadie_esperando() -> None:
    # No debe lanzar aunque nadie este esperando ese id.
    notify_status_change("sin-esperas")


async def _check_wait_resuelve_al_notificar() -> None:
    start = time.monotonic()

    async def _notificar_en_breve() -> None:
        await asyncio.sleep(0.1)
        notify_status_change("con-aviso")

    resultado, _ = await asyncio.gather(
        wait_for_change("con-aviso", timeout=5.0),
        _notificar_en_breve(),
    )
    elapsed = time.monotonic() - start
    assert resultado is True, "wait_for_change deberia devolver True al recibir el aviso"
    assert elapsed < 1.0, f"la espera deberia resolverse enseguida, no en {elapsed:.2f}s"


async def _check_wait_agota_el_tiempo_sin_aviso() -> None:
    start = time.monotonic()
    resultado = await wait_for_change("sin-aviso", timeout=0.2)
    elapsed = time.monotonic() - start
    assert resultado is False, "wait_for_change deberia devolver False si no llega ningun aviso"
    # Margen de tolerancia sobre el timeout: el scheduler del event loop no
    # garantiza una precision de milisegundos exacta.
    assert elapsed >= 0.18, f"deberia esperar aproximadamente el timeout, tardo {elapsed:.2f}s"


async def _check_varios_esperando_el_mismo_id() -> None:
    # Dos esperas concurrentes del mismo id (dos pestañas) deben
    # resolverse ambas con el mismo aviso.
    async def _notificar_en_breve() -> None:
        await asyncio.sleep(0.1)
        notify_status_change("varias-esperas")

    resultado_a, resultado_b, _ = await asyncio.gather(
        wait_for_change("varias-esperas", timeout=5.0),
        wait_for_change("varias-esperas", timeout=5.0),
        _notificar_en_breve(),
    )
    assert resultado_a is True and resultado_b is True, (resultado_a, resultado_b)


async def _check_timeout_no_rompe_un_aviso_posterior() -> None:
    # Una primera espera que agota el tiempo no debe impedir que una
    # espera posterior para el mismo id reciba el aviso real.
    primero = await wait_for_change("timeout-luego-aviso", timeout=0.2)
    assert primero is False, primero

    async def _notificar_en_breve() -> None:
        await asyncio.sleep(0.1)
        notify_status_change("timeout-luego-aviso")

    segundo, _ = await asyncio.gather(
        wait_for_change("timeout-luego-aviso", timeout=5.0),
        _notificar_en_breve(),
    )
    assert segundo is True, "el aviso posterior al timeout deberia seguir llegando"


async def main() -> None:
    await _check_notify_sin_nadie_esperando()
    print("OK: notify_status_change sin nadie esperando no falla")

    await _check_wait_resuelve_al_notificar()
    print("OK: wait_for_change se resuelve en cuanto llega el aviso, sin esperar al timeout")

    await _check_wait_agota_el_tiempo_sin_aviso()
    print("OK: wait_for_change devuelve False al agotar el tiempo sin aviso")

    await _check_varios_esperando_el_mismo_id()
    print("OK: varias esperas concurrentes del mismo id se resuelven con el mismo aviso")

    await _check_timeout_no_rompe_un_aviso_posterior()
    print("OK: un timeout previo no impide que una espera posterior reciba el aviso")


if __name__ == "__main__":
    asyncio.run(main())
