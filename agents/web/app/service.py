"""Logica de negocio del agente web, separada del transporte A2A.

Progresion por tarea (ver tasks.md del change `generacion-ejercicios-agentes`):
  - 3.1 (este fichero, de momento): firma y tipos; sin busqueda ni modelo
    todavia, para poder levantar el servicio y comprobar su Agent Card.
  - 3.2: `tavily_search`.
  - 3.3: resumen con el modelo `generator` via LiteLLM.
  - 3.4/3.5: memoria larga y corta.
"""

from dataclasses import dataclass, field


@dataclass
class Source:
    title: str
    url: str
    snippet: str


@dataclass
class WebResearchResult:
    summary: str
    sources: list[Source] = field(default_factory=list)
    memory_hit: bool = False


async def research(technologies: list[str]) -> WebResearchResult:
    if not technologies:
        raise ValueError("se necesita al menos una tecnologia")

    # TODO(3.2): tavily_search (hasta 5 busquedas por tarea).
    # TODO(3.3): resumen con el modelo `generator` via LiteLLM.
    # TODO(3.4): memoria larga por tecnologias normalizadas (cache de 30 dias).
    raise NotImplementedError(
        "investigar_tecnologias todavia no esta implementado (tareas 3.2/3.3)"
    )
