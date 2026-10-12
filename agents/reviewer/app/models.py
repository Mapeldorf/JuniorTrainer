"""Dataclass compartida por `app/service.py` y `app/executor.py`.

Ver design.md del change `valoracion-respuestas`, "Contrato de entrada/
salida de los agentes": el revisor SOLO devuelve `justification` -- no
recibe de vuelta ni puede cambiar el `verdict` (decision explicita, ver
design.md - Decisions, "Orquestacion de la evaluacion")."""

from dataclasses import dataclass


@dataclass
class ReviewResult:
    justification: str
