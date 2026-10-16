"""Dataclasses compartidas por `app/service.py` y `app/executor.py` -- en
un modulo hoja aparte para evitar import circular, mismo patron que
`agents/evaluator/app/models.py`.

`ValidationResult` es el veredicto del juez: si todas las tecnologias son
tecnologias de programacion (`valid`), un motivo legible (`reason`, solo
para logs / mensaje de error de la generacion) y las entradas concretas que
se han considerado invalidas (`invalid_technologies`)."""

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    valid: bool
    reason: str
    invalid_technologies: list[str] = field(default_factory=list)
