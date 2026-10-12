from typing import Literal

from pydantic import BaseModel

from app.schemas.generation import ExerciseCandidate, ExerciseType

# Reutiliza ExerciseCandidate (schemas/generation.py): un ejercicio definitivo
# tiene exactamente la misma forma que un candidato (id, type, statement,
# code, expected_answer); lo unico que cambia es el filtro saved/deleted_at
# con el que se consulta `exercise` (tarea 2.1).
SavedExercise = ExerciseCandidate


class ExerciseDeleteRequest(BaseModel):
    """Body de `PATCH /exercises/{id}` (tarea 2.4): este endpoint solo
    expone el borrado logico (`deleted_at`), no una edicion general del
    ejercicio -- `deleted` tiene que venir explicitamente en `true`."""

    deleted: Literal[True]


__all__ = ["SavedExercise", "ExerciseDeleteRequest", "ExerciseType"]
