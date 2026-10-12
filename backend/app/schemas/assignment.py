"""Schemas de las asignaciones propias del alumno (tareas 2.1/5.4,
capacidades `student-assignments` y `answer-evaluation`)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.generation import ExerciseCodeBlock

Verdict = Literal["correct", "incomplete", "incorrect"]


class AssignmentSummary(BaseModel):
    """Una fila de `GET /assignments` (tarea 1.2, capacidad
    `student-assignments`, requisito "Listar las propias asignaciones",
    version modificada: incluye progreso para que el frontend separe
    pendientes de hechos y distinga "Empezar" de "Continuar")."""

    id: str
    block_name: str
    assigned_at: datetime
    answered_count: int
    total_count: int


class AssignmentExerciseItem(BaseModel):
    """Un ejercicio de la copia de una asignacion, para `GET
    /assignments/{id}` (tarea 1.3, capacidad `student-assignments`,
    requisito "Ver el detalle de una asignacion propia", version
    modificada: incluye la respuesta, el verdict y la justificacion de
    cada ejercicio ya respondido, y el router deja de incluir los
    ejercicios posteriores al primero sin responder). No incluye
    `expected_answer`: ensenarsela al alumno antes de responder vaciaria
    el ejercicio -- decision de implementacion, el requisito no dice nada
    sobre ese campo."""

    exercise_id: str
    position: int
    statement: str
    code: list[ExerciseCodeBlock] = Field(default_factory=list)
    answered: bool
    answer_text: str | None = None
    verdict: Verdict | None = None
    justification: str | None = None


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
