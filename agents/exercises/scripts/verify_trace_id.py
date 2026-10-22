"""Verificacion manual de la tarea 5.5: trace_id de Langfuse.

El orquestador (grupo 6, todavia no existe) es quien normalmente pondria
`trace_id` en los metadatos del mensaje A2A. Sin el, este script simula
su papel: genera un `trace_id` el mismo y llama directamente a la logica
de negocio (sin pasar por el transporte A2A) exactamente como lo haria
`ExercisesAgentExecutor.execute()` -- ver app/executor.py.

Hace dos llamadas con trace_id distintos:
  - 1a llamada (trace_id_1): tipo `debug`, sin ningun ejercicio guardado
    ni eliminado de ese tipo sembrado -- memory_hit puede ser true si ya
    hay ejercicios `debug` reales en la base de datos, o false si no.
  - 2a llamada (trace_id_2): tipo `knowledge`, con un ejercicio sembrado
    directamente en `public.exercise` justo antes (ver
    scripts/verify_no_repeated_themes.py para el mismo mecanismo de
    siembra) -- debe dar memory_hit=true de forma determinista.

Change `eliminar-memoria-agente-ejercicios`: ya no hay una memoria propia
del agente que garantice memory_hit=false en la primera llamada; la
fuente unica es `search_saved_exercises` sobre `public.exercise`, por
eso el caso 2 siembra explicitamente en vez de depender de dos llamadas
seguidas con el mismo tipo.

Uso (desde agents/exercises/, con las mismas variables que
scripts/verify_no_repeated_themes.py MAS LANGFUSE_PUBLIC_KEY/
LANGFUSE_SECRET_KEY/LANGFUSE_BASE_URL en el .env de la raiz del repo,
LiteLLM corriendo):
    python -m scripts.verify_trace_id
"""

import asyncio
import logging
import uuid
from pathlib import Path

import httpx
from dotenv import dotenv_values

from app.service import generate_exercises
from app.tracing import get_client, init_client, new_trace_id, record_task
from scripts.verify_no_repeated_themes import _delete_seed, _seed_exercise

logging.basicConfig(level=logging.INFO)

_ENV = dotenv_values(Path(__file__).resolve().parent.parent.parent.parent / ".env")
_SUPABASE_URL = _ENV["SUPABASE_URL"]
_SERVICE_ROLE_KEY = _ENV["SUPABASE_SERVICE_ROLE_KEY"]
_HEADERS = {
    "apikey": _SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

_WEB_RESULT = {
    "summary": "## Git\nGit es un sistema de control de versiones distribuido.",
    "sources": [],
    "memory_hit": False,
}


async def main() -> None:
    init_client()
    client = get_client()

    # Caso 1: tipo debug, sin siembra -- memory_hit depende de los
    # ejercicios debug reales que ya hubiera en la base de datos.
    trace_id_1 = new_trace_id()
    result_1 = await generate_exercises("debug", 1, _WEB_RESULT, None, trace_id_1)
    record_task(
        trace_id_1, "debug", 1, memory_hit=result_1.memory_hit, candidates=len(result_1.candidates)
    )
    print(f"sin siembra: trace_id={trace_id_1}, memory_hit={result_1.memory_hit}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id_1)}")

    # Caso 2: tipo knowledge, CON un ejercicio sembrado justo antes --
    # memory_hit=true de forma determinista.
    marker = uuid.uuid4().hex[:8]
    statement = f"[verify-{marker}] Explica que hace range() en Python."
    trace_id_2 = new_trace_id()
    with httpx.Client(base_url=_SUPABASE_URL, headers=_HEADERS, timeout=10.0) as rest:
        gen_id, ex_id = _seed_exercise(rest, statement=statement, saved=True, deleted=False)
        try:
            result_2 = await generate_exercises("knowledge", 1, _WEB_RESULT, None, trace_id_2)
        finally:
            _delete_seed(rest, gen_id, ex_id)
    record_task(
        trace_id_2, "knowledge", 1, memory_hit=result_2.memory_hit, candidates=len(result_2.candidates)
    )
    print(f"con siembra: trace_id={trace_id_2}, memory_hit={result_2.memory_hit}")
    print(f"  URL: {client.get_trace_url(trace_id=trace_id_2)}")

    assert result_2.memory_hit is True, "deberia haber encontrado el ejercicio sembrado"

    client.flush()
    print()
    print("OK: revisa las dos URLs en Langfuse Cloud (puede tardar unos segundos en aparecer):")
    print(f"  - trace_id_1 ({trace_id_1}): span agente-ejercicios + generacion del modelo")
    print(f"  - trace_id_2 ({trace_id_2}): span agente-ejercicios con memory_hit=true + generacion del modelo")


if __name__ == "__main__":
    asyncio.run(main())
