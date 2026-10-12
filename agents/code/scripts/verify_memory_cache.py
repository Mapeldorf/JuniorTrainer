"""Verificacion manual de la tarea 4.4: dos llamadas seguidas con el mismo
repo y las mismas tecnologias; la segunda debe venir de memoria
(memory_hit=True) sin leer ningun fichero (mucho mas rapida que la
primera).

Uso (desde agents/code/, con las mismas variables que
scripts/verify_code_analysis.py MAS AGENTS_PG_*, AGENTS_MEMORY_PASSWORD y
SUPABASE_PROJECT_REF en el .env de la raiz del repo, LiteLLM corriendo):
    python -m scripts.verify_memory_cache <repo_path> <tecnologia> [<tecnologia> ...]

Por ejemplo, con el propio repo de agents/web (igual que verify_code_analysis.py):
    python -m scripts.verify_memory_cache ../web FastAPI LangChain
"""

import asyncio
import logging
import sys
import time

from app.service import analyze_repo

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Uso: python -m scripts.verify_memory_cache <repo_path> <tecnologia> [<tecnologia> ...]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    repo_path = sys.argv[1]
    technologies = sys.argv[2:]

    start = time.monotonic()
    first = await analyze_repo(repo_path, technologies)
    first_elapsed = time.monotonic() - start
    print(f"1a llamada: memory_hit={first.memory_hit}, {first_elapsed:.1f}s, {len(first.fragments)} fragmentos")

    start = time.monotonic()
    second = await analyze_repo(repo_path, technologies)
    second_elapsed = time.monotonic() - start
    print(f"2a llamada: memory_hit={second.memory_hit}, {second_elapsed:.1f}s, {len(second.fragments)} fragmentos")

    assert first.memory_hit is False, "la primera llamada no deberia venir de memoria"
    assert second.memory_hit is True, "la segunda llamada deberia venir de memoria"
    assert second.summary == first.summary, "el resumen cacheado deberia ser identico"
    print(f"OK: la segunda llamada vino de memoria y fue {first_elapsed / max(second_elapsed, 0.001):.0f}x mas rapida.")


if __name__ == "__main__":
    asyncio.run(main())
