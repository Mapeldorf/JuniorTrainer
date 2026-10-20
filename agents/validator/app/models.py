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
from typing import Literal

# Contexto de la llamada (change `validador-contexto-generacion`): el alta de
# una tecnologia en el catalogo (`catalog_entry`) comprueba tambien duplicados
# semanticos contra el catalogo; la validacion previa a una generacion
# (`generation`) comprueba unicamente que la entrada es una tecnologia de
# programacion, sin tocar el catalogo. `catalog_entry` es el valor por
# defecto cuando el llamador no lo indica (ver app/input.py) -- es el
# comportamiento mas estricto, asi que ningun llamador se vuelve mas
# permisivo por omision.
ValidationContext = Literal["catalog_entry", "generation"]


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
