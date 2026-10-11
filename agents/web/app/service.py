"""Logica de negocio del agente web, separada del transporte A2A.

Progresion por tarea (ver tasks.md del change `generacion-ejercicios-agentes`):
  - 3.1/3.2: scaffold + `tavily_search` (ver app/tools/tavily_search.py).
  - 3.3 (este fichero, ahora): resumen con el modelo `generator` via LiteLLM.
  - 3.4/3.5: memoria larga y corta (todavia no implementadas aqui).
"""

from dataclasses import dataclass, field

from tavily import AsyncTavilyClient

from app.config import get_settings
from app.llm import build_generator_model
from app.tools.tavily_search import SearchBudget, SearchBudgetExceeded, Source, tavily_search

SYSTEM_PROMPT = (
    "Eres un asistente que prepara material de referencia para crear "
    "ejercicios de programacion. Para CADA tecnologia que se te indique, "
    "escribe un resumen breve (3-5 frases) de sus conceptos clave, "
    "basandote unicamente en los fragmentos de busqueda proporcionados. "
    "Organiza la respuesta con un encabezado por tecnologia (## nombre). "
    "Si una tecnologia no tiene fragmentos, dilo explicitamente en vez de "
    "inventar contenido."
)


@dataclass
class WebResearchResult:
    summary: str
    sources: list[Source] = field(default_factory=list)
    memory_hit: bool = False


async def research(technologies: list[str]) -> WebResearchResult:
    if not technologies:
        raise ValueError("se necesita al menos una tecnologia")

    tavily_client = AsyncTavilyClient(api_key=get_settings().tavily_api_key)
    budget = SearchBudget(max_calls=5)

    sources_by_technology: dict[str, list[Source]] = {}
    all_sources: list[Source] = []
    for technology in technologies:
        try:
            found = await tavily_search(tavily_client, f"{technology} documentacion", budget)
        except SearchBudgetExceeded:
            # TODO(3.4): con memoria larga, un acierto de cache no deberia
            # llegar aqui para las tecnologias ya vistas. Para las que si
            # necesitan busqueda nueva y exceden el presupuesto, se
            # resumen igualmente sin fuentes en vez de fallar la tarea
            # entera por una tecnologia tardia en la lista.
            found = []
        sources_by_technology[technology] = found
        all_sources.extend(found)

    summary = await _summarize(technologies, sources_by_technology)
    return WebResearchResult(summary=summary, sources=all_sources, memory_hit=False)


async def _summarize(
    technologies: list[str], sources_by_technology: dict[str, list[Source]]
) -> str:
    model = build_generator_model()

    blocks = []
    for technology in technologies:
        found = sources_by_technology.get(technology, [])
        if not found:
            blocks.append(f"### {technology}\n(sin resultados de busqueda)")
            continue
        snippets = "\n".join(f"- {s.title}: {s.snippet}" for s in found)
        blocks.append(f"### {technology}\n{snippets}")

    human_prompt = "Tecnologias y fragmentos encontrados:\n\n" + "\n\n".join(blocks)

    response = await model.ainvoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": human_prompt},
        ]
    )
    return response.content
