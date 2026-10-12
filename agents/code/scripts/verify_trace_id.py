"""Verificacion manual de la tarea 4.5: trace_id de Langfuse.

El orquestador (grupo 6, todavia no existe) es quien normalmente pondria
`trace_id` en los metadatos del mensaje A2A. Sin el, este script simula
su papel: genera un `trace_id` el mismo y llama directamente a la logica
de negocio (sin pasar por el transporte A2A) exactamente como lo haria
`CodeAgentExecutor.execute()` -- ver app/executor.py.

Hace dos llamadas con el MISMO repo_path y la MISMA tecnologia (una
inventada, unica por ejecucion, para forzar que la primera llamada sea
siempre cache-miss sin importar ejecuciones anteriores) pero trace_id
DISTINTOS:
  - 1a llamada (trace_id_1): cache-miss real -- debe aparecer una traza
    con un span "agente-code" (memory_hit=false) y las generaciones del
    modelo (elegir ficheros + analizar) colgando de esa misma traza.
  - 2a llamada (trace_id_2): cache-hit (gracias a la tarea 4.4, mismo
    repo+tecnologia) -- debe aparecer una traza con un span "agente-code"
    con memory_hit=true, SIN ninguna generacion nueva del modelo.

Uso (desde agents/code/, con las mismas variables que
scripts/verify_memory_cache.py MAS LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY/
LANGFUSE_BASE_URL en el .env de la raiz del repo, LiteLLM corriendo):
    python -m scripts.verify_trace_id <repo_path>

Por ejemplo, con el propio repo de agents/web:
    python -m scripts.verify_trace_id ../web
"""

import asyncio
import logging
import sys
import uuid

from app.service import analyze_repo
from app.tracing import get_client, init_client, new_trace_id, record_task

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.verify_trace_id <repo_path>", file=sys.stderr)
        raise SystemExit(1)

    repo_path = sys.argv[1]
    # Tecnologia inventada y unica: solo importa para la clave de cache
    # (fuerza que la 1a llamada sea cache-miss aunque el script se haya
    # corrido antes), no hace falta que el modelo la detecte de verdad.
    technologies = [f"Tech-{uuid.uuid4().hex[:8]}"]

    init_client()
    client = get_client()

    # Caso 1: cache-miss -- debe generar llamadas reales al modelo
    # (elegir ficheros + analizar), agrupadas bajo trace_id_1.
    trace_id_1 = new_trace_id()
    result_1 = await analyze_repo(repo_path, technologies, trace_id_1)
    record_task(
        trace_id_1, repo_path, technologies, memory_hit=result_1.memory_hit, fragments=len(result_1.fragments)
    )
    print(f"cache-miss: trace_id={trace_id_1}, memory_hit={result_1.memory_hit}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id_1)}")

    # Caso 2: mismo repo_path + misma tecnologia, OTRO trace_id -- debe
    # ser cache-hit (gracias a la tarea 4.4) y la traza debe aparecer
    # igual, con memory_hit=true, SIN relectura de ficheros ni generacion
    # nueva del modelo.
    trace_id_2 = new_trace_id()
    result_2 = await analyze_repo(repo_path, technologies, trace_id_2)
    record_task(
        trace_id_2, repo_path, technologies, memory_hit=result_2.memory_hit, fragments=len(result_2.fragments)
    )
    print(f"cache-hit: trace_id={trace_id_2}, memory_hit={result_2.memory_hit}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id_2)}")

    assert result_1.memory_hit is False, "la primera llamada no deberia venir de memoria"
    assert result_2.memory_hit is True, "la segunda llamada deberia venir de memoria"

    client.flush()
    print()
    print("OK: revisa las dos URLs en Langfuse Cloud (puede tardar unos segundos en aparecer):")
    print(f"  - trace_id_1 ({trace_id_1}): span agente-code con memory_hit=false + generaciones del modelo")
    print(f"  - trace_id_2 ({trace_id_2}): span agente-code con memory_hit=true, SIN generacion nueva")


if __name__ == "__main__":
    asyncio.run(main())
