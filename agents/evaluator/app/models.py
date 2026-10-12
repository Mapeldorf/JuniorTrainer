"""Dataclasses compartidas por `app/service.py` y `app/executor.py` -- en
un modulo hoja aparte para evitar import circular, mismo motivo que
`app/models.py` del agente de ejercicios.

Ver design.md del change `valoracion-respuestas`, "Contrato de entrada/
salida de los agentes": `EvaluationResult` mapea a `verdict`/
`justification` de `public.answer`.
"""

from dataclasses import dataclass
from typing import Literal

Verdict = Literal["correct", "incomplete", "incorrect"]


@dataclass
class EvaluationResult:
    verdict: Verdict
    justification: str
