from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.exercise import SavedExercise


class BlockCreateRequest(BaseModel):
    """Body de `POST /blocks` (tarea 3.2). `exercise_ids` fija el orden:
    la posicion de cada ejercicio en el bloque es su indice en esta lista
    (requisito "Crear un bloque de ejercicios", 1 a 100 ejercicios)."""

    name: str = Field(min_length=1)
    exercise_ids: list[str] = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("el nombre del bloque no puede estar vacio")
        return value


class BlockUpdateRequest(BaseModel):
    """Body de `PATCH /blocks/{id}` (tarea 3.4). Reemplazo completo, no un
    diff: si se manda `exercise_ids`, sustituye toda la composicion actual
    (ver design.md - Decisions). Al menos uno de los dos campos tiene que
    venir informado."""

    name: str | None = Field(default=None, min_length=1)
    exercise_ids: list[str] | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("el nombre del bloque no puede estar vacio")
        return value


class BlockExerciseItem(BaseModel):
    position: int
    exercise: SavedExercise


class BlockSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    exercise_count: int


class BlockDetail(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    exercises: list[BlockExerciseItem] = Field(default_factory=list)


class AssignBlockRequest(BaseModel):
    """Body de `POST /blocks/{id}/assignments` (tarea 4.2)."""

    student_ids: list[str] = Field(min_length=1)


AssignmentOutcome = Literal["created", "already_assigned"]


class AssignmentResult(BaseModel):
    student_id: str
    status: AssignmentOutcome


class AssignBlockResponse(BaseModel):
    results: list[AssignmentResult]


class ExerciseProgress(BaseModel):
    exercise_id: str
    position: int
    answered: bool


class StudentProgress(BaseModel):
    student_id: str
    student_name: str
    assignment_id: str
    exercises: list[ExerciseProgress] = Field(default_factory=list)
