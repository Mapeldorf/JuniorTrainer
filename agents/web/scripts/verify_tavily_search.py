"""Verificacion manual de la tarea 3.2: llama a tavily_search de verdad y
imprime titulo/URL/extracto de cada resultado.

Uso (desde agents/web/, con TAVILY_API_KEY en el .env de la raiz del repo
o en el entorno):
    python -m scripts.verify_tavily_search "React"
"""

import asyncio
import sys

from tavily import AsyncTavilyClient

from app.config import get_settings
from app.tools.tavily_search import SearchBudget, tavily_search


async def main() -> None:
    if len(sys.argv) != 2:
        print('Uso: python -m scripts.verify_tavily_search "<tecnologia>"', file=sys.stderr)
        raise SystemExit(1)

    query = sys.argv[1]
    settings = get_settings()
    client = AsyncTavilyClient(api_key=settings.tavily_api_key)
    budget = SearchBudget(max_calls=5)

    results = await tavily_search(client, f"{query} documentacion", budget)

    if not results:
        print("Sin resultados.")
        return

    for i, source in enumerate(results, start=1):
        print(f"[{i}] {source.title}")
        print(f"    {source.url}")
        print(f"    {source.snippet[:200]}...")
        print()

    print(f"OK: {len(results)} resultados, {budget.used}/{budget.max_calls} busquedas usadas.")


if __name__ == "__main__":
    asyncio.run(main())
