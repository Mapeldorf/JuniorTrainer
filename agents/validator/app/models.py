"""Dataclasses compartidas por `app/service.py` y `app/executor.py` -- en
un modulo hoja aparte para evitar import circular, mismo patron que
`agents/evaluator/app/models.py`.

`ValidationResult` es el veredicto del juez: si todas las tecnologias son
tecnologias de programacion y ninguna duplica semanticamente una tecnologia
ya existente en el catalogo (`valid`), un motivo legible (`reason`, solo
para logs / mensaje de error de la generacion), las entradas concretas que
se han considerado invalidas (`invalid_technologies`) y las entradas que se
han considerado ya cubiertas por una tecnologia existente del catalogo
(`duplicate_technologies`, change `validador-duplicados-tecnologias`)."""

from dataclasses import dataclass, field


@dataclass
class DuplicateTechnology:
    """Una entrada de entrada (`input`) que el validador considera ya
    cubierta semanticamente por una tecnologia existente del catalogo
    (`matches`, el nombre canonico de esa tecnologia)."""

    input: str
    matches: str


@dataclass
class ValidationResult:
    valid: bool
    reason: str
    invalid_technologies: list[str] = field(default_factory=list)
    duplicate_technologies: list[DuplicateTechnology] = field(default_factory=list)
