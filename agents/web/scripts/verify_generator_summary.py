"""Verificacion manual de la tarea 3.3: llama a research() de verdad
(tavily_search + modelo `generator` via LiteLLM) e imprime el resumen.

Uso (desde agents/web/, con TAVILY_API_KEY y AGENT_WEB_LITELLM_KEY en el .env
de la raiz del repo, y el contenedor de LiteLLM corriendo):
    python -m scripts.verify_generator_summary React FastAPI
"""

import asyncio
import sys

from app.service import research


async def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.verify_generator_summary <tecnologia> [<tecnologia> ...]", file=sys.stderr)
        raise SystemExit(1)

    technologies = sys.argv[1:]
    result = await research(technologies)

    print(result.summary)
    print()
    print(f"--- {len(result.sources)} fuentes, memory_hit={result.memory_hit} ---")
    for source in result.sources:
        print(f"- {source.title} ({source.url})")


if __name__ == "__main__":
    asyncio.run(main())
