"""Verificacion manual de la tarea 5.5: trace_id de Langfuse.

El orquestador (grupo 6, todavia no existe) es quien normalmente pondria
`trace_id` en los metadatos del mensaje A2A. Sin el, este script simula
su papel: genera un `trace_id` el mismo y llama directamente a la logica
de negocio (sin pasar por el transporte A2A) exactamente como lo haria
`ExercisesAgentExecutor.execute()` -- ver app/executor.py.

Hace dos llamadas con el MISMO tipo (uno nuevo, unico por ejecucion, para
que la primera sea siempre memory_hit=false) pero trace_id distintos:
  - 1a llamada (trace_id_1): sin historial -- debe aparecer una traza con
    un span "agente-ejercicios" (memory_hit=false) y la generacion del
    modelo colgando de esa misma traza.
  - 2a llamada (trace_id_2): el enunciado de la 1a ya esta en el
    historial -- debe aparecer una traza con un span "agente-ejercicios"
    con memory_hit=true (aqui SI hay generacion del modelo, a diferencia
    de web/codigo: el agente de ejercicios siempre redacta candidatos
    nuevos, memory_hit solo indica que habia temas que evitar).

Uso (desde agents/exercises/, con las mismas variables que
scripts/verify_no_repeated_themes.py MAS LANGFUSE_PUBLIC_KEY/
LANGFUSE_SECRET_KEY/LANGFUSE_BASE_URL en el .env de la raiz del repo,
LiteLLM corriendo):
    python -m scripts.verify_trace_id
"""

import asyncio
import logging
import uuid

from app.service import generate_exercises
from app.tracing import get_client, init_client, new_trace_id, record_task

logging.basicConfig(level=logging.INFO)

_WEB_RESULT = {
    "summary": "## Git\nGit es un sistema de control de versiones distribuido.",
    "sources": [],
    "memory_hit": False,
}


async def main() -> None:
    init_client()
    client = get_client()

    exercise_type = f"knowledge-verify-{uuid.uuid4().hex[:8]}"

    # Caso 1: sin historial -- debe generar una llamada real al modelo,
    # agrupada bajo trace_id_1.
    trace_id_1 = new_trace_id()
    result_1 = await generate_exercises(exercise_type, 1, _WEB_RESULT, None, trace_id_1)
    record_task(
        trace_id_1, exercise_type, 1, memory_hit=result_1.memory_hit, candidates=len(result_1.candidates)
    )
    print(f"sin historial: trace_id={trace_id_1}, memory_hit={result_1.memory_hit}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id_1)}")

    # Caso 2: mismo tipo, OTRO trace_id -- el enunciado de la 1a llamada ya
    # esta en el historial propio (tarea 5.4), asi que memory_hit=true.
    trace_id_2 = new_trace_id()
    result_2 = await generate_exercises(exercise_type, 1, _WEB_RESULT, None, trace_id_2)
    record_task(
        trace_id_2, exercise_type, 1, memory_hit=result_2.memory_hit, candidates=len(result_2.candidates)
    )
    print(f"con historial: trace_id={trace_id_2}, memory_hit={result_2.memory_hit}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id_2)}")

    assert result_1.memory_hit is False, "la primera llamada no deberia tener historial"
    assert result_2.memory_hit is True, "la segunda deberia ver el historial de la primera"

    client.flush()
    print()
    print("OK: revisa las dos URLs en Langfuse Cloud (puede tardar unos segundos en aparecer):")
    print(f"  - trace_id_1 ({trace_id_1}): span agente-ejercicios con memory_hit=false + generacion del modelo")
    print(f"  - trace_id_2 ({trace_id_2}): span agente-ejercicios con memory_hit=true + generacion del modelo (siempre hay una)")


if __name__ == "__main__":
    asyncio.run(main())
