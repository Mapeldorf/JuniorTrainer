"""Registro en memoria de cambios de estado de una generacion (propuesta
`long-polling-generaciones-pendientes`): permite que el endpoint de espera
larga (`GET /generations/pending/wait`) se despierte en cuanto
`_mark_status` (`app/orchestrator.py`) cambia el estado de una generacion,
en vez de tener que sondearla.

Vive en un `dict` en memoria del propio proceso (design.md decision 1): el
backend corre como un unico proceso uvicorn (`backend/Dockerfile`), igual
que ya asume `BackgroundTasks` para la propia generacion, asi que no hace
falta coordinar el aviso entre procesos. Tampoco hace falta un `Lock`: todo
el acceso ocurre en corutinas del mismo event loop, nunca en threads
distintos.
"""

import asyncio

_events: dict[str, asyncio.Event] = {}


def notify_status_change(generation_id: str) -> None:
    """Avisa a quien este esperando el cambio de estado de `generation_id`.
    Llamarla sin que nadie la este esperando (antes de que empiece una
    espera, o despues de que ya hayan terminado todas) no falla: no hay
    nada que avisar."""
    event = _events.pop(generation_id, None)
    if event is not None:
        event.set()


async def wait_for_change(generation_id: str, timeout: float) -> bool:
    """Espera hasta `timeout` segundos a que se notifique un cambio de
    estado de `generation_id`. Devuelve `True` si ha llegado el aviso,
    `False` si se agoto el tiempo sin novedad.

    El evento NO se retira del registro al agotarse el tiempo (solo lo
    retira `notify_status_change`): varias llamadas sucesivas o
    concurrentes para el mismo id (varias pestañas, o la siguiente
    petición encadenada tras un timeout) deben seguir compartiendo el
    mismo `asyncio.Event` hasta que de verdad llegue el aviso, o una ya
    resuelta por timeout haria que una posterior se creara un evento nuevo
    que el aviso real ya no encontraria (design.md decision 1)."""
    event = _events.setdefault(generation_id, asyncio.Event())
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        return True
    except TimeoutError:
        return False
