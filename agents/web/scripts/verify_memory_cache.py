"""Verificacion manual de la tarea 3.4: dos llamadas seguidas con las mismas
tecnologias; la segunda debe venir de memoria (memory_hit=True) y no tocar
tavily_search ni el modelo (mucho mas rapida que la primera).

Uso (desde agents/web/, con TAVILY_API_KEY, LITELLM_MASTER_KEY, AGENTS_PG_*,
AGENTS_MEMORY_PASSWORD y SUPABASE_PROJECT_REF en el .env de la raiz del
repo, LiteLLM corriendo y accesible):
    python -m scripts.verify_memory_cache React
"""

import asyncio
import logging
import sys
import time

from app.service import research

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.verify_memory_cache <tecnologia> [<tecnologia> ...]", file=sys.stderr)
        raise SystemExit(1)

    technologies = sys.argv[1:]

    start = time.monotonic()
    first = await research(technologies)
    first_elapsed = time.monotonic() - start
    print(f"1a llamada: memory_hit={first.memory_hit}, {first_elapsed:.1f}s, {len(first.sources)} fuentes")

    start = time.monotonic()
    second = await research(technologies)
    second_elapsed = time.monotonic() - start
    print(f"2a llamada: memory_hit={second.memory_hit}, {second_elapsed:.1f}s, {len(second.sources)} fuentes")

    assert first.memory_hit is False, "la primera llamada no deberia venir de memoria"
    assert second.memory_hit is True, "la segunda llamada deberia venir de memoria"
    assert second.summary == first.summary, "el resumen cacheado deberia ser identico"
    print(f"OK: la segunda llamada vino de memoria y fue {first_elapsed / max(second_elapsed, 0.001):.0f}x mas rapida.")


if __name__ == "__main__":
    asyncio.run(main())
