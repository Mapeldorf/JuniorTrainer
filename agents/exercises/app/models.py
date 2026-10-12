"""Dataclasses compartidas por `app/service.py`, `app/memory.py` y
`app/tools/saved_exercises.py` -- en un modulo hoja aparte para evitar
import circular, mismo motivo que `app/models.py` del agente de codigo.

Ver design.md "Contrato de entrada/salida del agente de ejercicios":
`CandidateExercise` mapea 1:1 a las columnas de `public.exercise`
(type/statement/code/expected_answer) que el orquestador movera a esa
tabla cuando el tech lead guarde un candidato (fuera de alcance de este
change).
"""

from dataclasses import dataclass, field


@dataclass
class ExerciseCodeBlock:
    file: str | None
    code: str


@dataclass
class CandidateExercise:
    type: str
    statement: str
    code: list[ExerciseCodeBlock] = field(default_factory=list)
    expected_answer: str = ""


@dataclass
class ExerciseGenerationResult:
    candidates: list[CandidateExercise] = field(default_factory=list)
    # Informativo/trazabilidad (ver design.md): True si se uso algun
    # enunciado previo (guardado y/o propuesto antes) al redactar los
    # candidatos. A diferencia de web/codigo, nunca salta el trabajo
    # entero -- cada generacion redacta candidatos nuevos siempre.
    memory_hit: bool = False
