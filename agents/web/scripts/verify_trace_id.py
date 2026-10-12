"""Verificacion manual de la tarea 3.6: trace_id de Langfuse.

El orquestador (grupo 6, todavia no existe) es quien normalmente pondria
`trace_id` en los metadatos del mensaje A2A. Sin el, este script simula
su papel: genera un `trace_id` el mismo y llama directamente a la logica
de negocio (sin pasar por el transporte A2A) exactamente como lo haria
`WebAgentExecutor.execute()` -- ver app/executor.py.

Hace dos llamadas con el MISMO trace_id y tecnologias DISTINTAS (para que
ambas sean cache-miss y se vea la generacion real en la traza), e imprime
la URL de la traza para revisarla a mano en Langfuse Cloud:
  - Debe aparecer UNA traza con ese id.
  - Debe tener al menos un span "agente-web" con memory_hit=false.
  - Debe tener (al menos) una generacion del modelo `generator` colgando
    de esa misma traza (no una traza suelta nueva).

Luego hace una TERCERA llamada con tecnologias ya vistas (cache-hit, otro
trace_id) para comprobar que, aun sin llamar al modelo, tambien aparece
una traza con un span "agente-web" y memory_hit=true.

Uso (desde agents/web/, con las mismas variables que los scripts
anteriores MAS LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY/LANGFUSE_BASE_URL
en el .env de la raiz del repo):
    python -m scripts.verify_trace_id
"""

import asyncio
import logging
import uuid

from app.checkpoint import research_with_checkpoint
from app.tracing import get_client, init_client, new_trace_id, record_task

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    init_client()
    client = get_client()

    # Caso 1: cache-miss -- debe generar una llamada real al modelo,
    # agrupada bajo trace_id_1.
    trace_id_1 = new_trace_id()
    task_id_1 = f"verify-trace-miss-{uuid.uuid4()}"
    tecnologia_1 = f"Vue-{uuid.uuid4().hex[:8]}"  # unica, para forzar cache-miss
    result_1 = await research_with_checkpoint(task_id_1, [tecnologia_1], trace_id_1)
    record_task(trace_id_1, [tecnologia_1], memory_hit=result_1.memory_hit, sources=len(result_1.sources))
    print(f"cache-miss: trace_id={trace_id_1}, memory_hit={result_1.memory_hit}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id_1)}")

    # Caso 2: misma tecnologia otra vez, OTRO trace_id -- debe ser
    # cache-hit (gracias a la tarea 3.4) y la traza debe aparecer igual,
    # con memory_hit=true, SIN ninguna generacion nueva del modelo.
    trace_id_2 = new_trace_id()
    task_id_2 = f"verify-trace-hit-{uuid.uuid4()}"
    result_2 = await research_with_checkpoint(task_id_2, [tecnologia_1], trace_id_2)
    record_task(trace_id_2, [tecnologia_1], memory_hit=result_2.memory_hit, sources=len(result_2.sources))
    print(f"cache-hit: trace_id={trace_id_2}, memory_hit={result_2.memory_hit}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id_2)}")

    assert result_1.memory_hit is False, "la primera llamada no deberia venir de memoria"
    assert result_2.memory_hit is True, "la segunda llamada deberia venir de memoria"

    client.flush()
    print()
    print("OK: revisa las dos URLs en Langfuse Cloud (puede tardar unos segundos en aparecer):")
    print(f"  - trace_id_1 ({trace_id_1}): span agente-web con memory_hit=false + 1 generacion del modelo")
    print(f"  - trace_id_2 ({trace_id_2}): span agente-web con memory_hit=true, SIN generacion nueva")


if __name__ == "__main__":
    asyncio.run(main())
