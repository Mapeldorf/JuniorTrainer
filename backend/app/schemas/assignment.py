"""Schemas de las asignaciones propias del alumno (tareas 2.1/5.4,
capacidades `student-assignments` y `answer-evaluation`)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.generation import ExerciseCodeBlock

Verdict = Literal["correct", "incomplete", "incorrect"]


class AssignmentSummary(BaseModel):
    """Una fila de `GET /assignments` (tarea 2.2, requisito "Listar las
    propias asignaciones")."""

    id: str
    block_name: str
    assigned_at: datetime


class AssignmentExerciseItem(BaseModel):
    """Un ejercicio de la copia de una asignacion, para `GET
    /assignments/{id}` (tarea 2.3, requisito "Ver el detalle de una
    asignacion propia"). No incluye `expected_answer`: ensenarsela al
    alumno antes de responder vaciaria el ejercicio -- decision de
    implementacion, el requisito no dice nada sobre que campos exponer."""

    exercise_id: str
    position: int
    statement: str
    code: list[ExerciseCodeBlock] = Field(default_factory=list)
    answered: bool


class AssignmentDetail(BaseModel):
    id: str
    block_name: str
    assigned_at: datetime
    exercises: list[AssignmentExerciseItem] = Field(default_factory=list)


class AnswerRequest(BaseModel):
    """Body de `POST /assignments/{assignment_id}/exercises/{exercise_id}/answer`
    (tarea 5.4)."""

    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("la respuesta no puede estar vacia")
        return value


class AnswerResult(BaseModel):
    """Resultado persistido de evaluar una respuesta (tarea 5.4)."""

    exercise_id: str
    verdict: Verdict
    justification: str | None = None
    answered_at: datetime
