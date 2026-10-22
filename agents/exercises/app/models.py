"""Dataclasses compartidas por `app/service.py` y
`app/tools/saved_exercises.py` -- en un modulo hoja aparte para evitar
import circular, mismo motivo que `app/models.py` del agente de codigo.

Ver design.md "Contrato de entrada/salida del agente de ejercicios":
`CandidateExercise` mapea 1:1 a las columnas de `public.exercise`
(name/type/statement/code/expected_answer) que el orquestador movera a
esa tabla cuando el tech lead guarde un candidato (fuera de alcance de
ese change).

Change `ejercicios-con-nombre` (ver design.md, decision 1): `name` es un
campo corto y distinto de `statement`, pensado como identificador visual
(listados, selectores), no como el enunciado que resuelve el alumno.
"""

from dataclasses import dataclass, field


@dataclass
class ExerciseCodeBlock:
    file: str | None
    code: str


@dataclass
class CandidateExercise:
    type: str
    name: str
    statement: str
    code: list[ExerciseCodeBlock] = field(default_factory=list)
    expected_answer: str = ""


@dataclass
class ExerciseGenerationResult:
    candidates: list[CandidateExercise] = field(default_factory=list)
    # Informativo/trazabilidad (ver design.md): True si habia algun
    # ejercicio guardado o eliminado de ese tipo (search_saved_exercises)
    # al redactar los candidatos. A diferencia de web/codigo, nunca salta
    # el trabajo entero -- cada generacion redacta candidatos nuevos siempre.
    memory_hit: bool = False
