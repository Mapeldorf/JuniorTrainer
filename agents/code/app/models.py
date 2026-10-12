"""Tipos de datos del agente de codigo, sin logica.

Viven en su propio modulo (y no en app/service.py) para que app/memory.py
pueda importarlos sin crear un ciclo service.py <-> memory.py -- el mismo
motivo por el que `Source` vive en app/tools/tavily_search.py en el
agente web, no en su service.py.
"""

from dataclasses import dataclass, field


@dataclass
class CodeFragment:
    file: str
    start_line: int
    code: str
    note: str


@dataclass
class CodeAnalysisResult:
    summary: str
    technologies: list[str] = field(default_factory=list)
    fragments: list[CodeFragment] = field(default_factory=list)
    memory_hit: bool = False
