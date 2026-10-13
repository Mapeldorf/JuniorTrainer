from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.exercise import SavedExercise
from app.schemas.generation import ExerciseType


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
    # True si el ejercicio fue eliminado del catalogo (soft-delete via
    # `exercise.deleted_at`) desde que se anadio a este bloque (tarea 1.3,
    # design.md - decision D3). No se anade a `SavedExercise`: esa misma
    # consulta no une con `generation` y se reutiliza en otros sitios.
    exercise_deleted: bool = False


class AssignedStudentSummary(BaseModel):
    """Alumno asignado a un bloque, para el resumen de `BlockSummary`
    (tarea 1.2, design.md - decision D1)."""

    id: str
    name: str


class BlockSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    exercise_count: int
    # Alumnos actualmente asignados a este bloque (tarea 1.2, design.md -
    # decision D1).
    assigned_students: list[AssignedStudentSummary] = Field(default_factory=list)
    # True si alguna asignacion de este bloque tiene al menos una
    # respuesta registrada (tarea 1.2, design.md - decision D2): reusa la
    # misma regla que ya bloquea la edicion en `_block_has_answers`.
    resolved: bool = False


class BlockDetail(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    exercises: list[BlockExerciseItem] = Field(default_factory=list)
    # Mismo significado que en `BlockSummary` (tarea 1.3, design.md -
    # decision D2).
    resolved: bool = False


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
    # Nombre, tipo y enunciado del ejercicio, leidos siempre desde la
    # copia inmutable de esta asignacion (`assignment_exercise`/
    # `exercise`), no desde la composicion actual del bloque (tarea 3.1,
    # design.md - decision D5): un bloque puede haberse editado entre dos
    # asignaciones distintas antes de que existiera ninguna respuesta.
    # `name` se anade en el change `ejercicios-con-nombre`.
    name: str
    type: ExerciseType
    statement: str
    answered: bool
    verdict: Literal["correct", "incomplete", "incorrect"] | None = None
    # Texto de la respuesta y justificacion de la valoracion, solo cuando
    # `answered` es True (tarea 3.1, design.md - decision D5); ya existen
    # en `answer` desde el change archivado "valoracion-respuestas".
    answer_text: str | None = None
    justification: str | None = None


class StudentProgress(BaseModel):
    student_id: str
    student_name: str
    assignment_id: str
    exercises: list[ExerciseProgress] = Field(default_factory=list)


class StudentBlockAssignment(BaseModel):
    """Una asignacion de un alumno, vista desde el alumno (tarea 1.1,
    capacidad `block-assignment`, requisito "Consultar las asignaciones de
    un alumno a traves de sus bloques"): mismo detalle por ejercicio que
    `StudentProgress`, pero el dato que identifica a cada fila es el
    bloque de origen (su nombre), no el alumno -- es la vista simetrica de
    `GET /blocks/{id}/assignments` para `GET /users/{id}/blocks`. Incluye
    asignaciones de bloques ya eliminados (design.md - decision D3)."""

    assignment_id: str
    block_id: str
    block_name: str
    exercises: list[ExerciseProgress] = Field(default_factory=list)
