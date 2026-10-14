"""Herramienta de busqueda web (Tavily) del agente web.

Requisito de `proposal.md`: "busca documentacion de las tecnologias
indicadas con tavily_search", hasta 5 busquedas por tarea A2A.
"""

from dataclasses import dataclass

from tavily import AsyncTavilyClient


class SearchBudgetExceeded(RuntimeError):
    """Se intento una busqueda por encima del limite de la tarea."""


class SearchBudget:
    """Cuenta las busquedas hechas en una tarea A2A; agota a las 5 (por diseno)."""

    def __init__(self, max_calls: int = 5) -> None:
        self.max_calls = max_calls
        self.used = 0

    def consume(self) -> None:
        if self.used >= self.max_calls:
            raise SearchBudgetExceeded(
                f"se alcanzo el limite de {self.max_calls} busquedas de esta tarea"
            )
        self.used += 1


@dataclass
class Source:
    title: str
    url: str
    snippet: str


async def tavily_search(
    client: AsyncTavilyClient,
    query: str,
    budget: SearchBudget,
    max_results: int = 5,
) -> list[Source]:
    """Busca `query` en Tavily y devuelve titulo/URL/extracto de cada resultado.

    Descuenta una busqueda de `budget` ANTES de llamar a la API, para que un
    budget agotado no haga ninguna llamada de mas aunque la propia llamada
    falle despues.
    """
    budget.consume()
    # timeout explicito (change resiliencia-agentes): el default de
    # `AsyncTavilyClient.search` es 60s, demasiado cercano al limite de
    # 120s de toda la tarea A2A si se encadenan varias busquedas.
    response = await client.search(query, max_results=max_results, timeout=15.0)
    return [
        Source(
            title=item.get("title", ""),
            url=item.get("url", ""),
            snippet=item.get("content", ""),
        )
        for item in response.get("results", [])
    ]
