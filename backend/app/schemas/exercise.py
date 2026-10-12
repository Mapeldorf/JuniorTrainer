from typing import Literal

from pydantic import BaseModel

from app.schemas.generation import ExerciseCandidate, ExerciseType


# Reutiliza ExerciseCandidate (schemas/generation.py): un ejercicio definitivo
# tiene exactamente la misma forma que un candidato (id, type, statement,
# code, expected_answer); lo unico que cambia es el filtro saved/deleted_at
# con el que se consulta `exercise` (tarea 2.1). Usado tambien por
# `BlockExerciseItem` (schemas/block.py) -- no se le anaden campos nuevos
# aqui para no romper esa consulta, que no une con `generation`.
SavedExercise = ExerciseCandidate


class SavedExerciseListItem(ExerciseCandidate):
    """Fila de `GET /exercises` (tarea 1.5 de frontend-tech-lead-ejercicios,
    capacidad exercise-catalog: "Listar y buscar ejercicios definitivos").
    Solo para ese listado -- anade `technologies` y `repo_path`, propios de
    la generacion de la que proviene el ejercicio, sin filtrar por el
    estado de esa generacion (design.md decision 9), porque la pantalla de
    guardados necesita mostrarlos incluso cuando la generacion ya esta
    `done`. `SavedExercise` (usado por guardar/eliminar y por el detalle
    de un bloque) se deja sin cambios."""

    technologies: list[str]
    repo_path: str | None = None


class SaveExerciseRequest(BaseModel):
    """Body opcional de `POST /exercises/{id}/save` (tarea 1.4 de
    frontend-tech-lead-ejercicios, capacidad exercise-catalog: "Guardar un
    ejercicio candidato como definitivo"). Si `expected_answer` viene
    informado, sustituye a la respuesta esperada generada antes de que el
    ejercicio se vuelva inmutable; si se omite el body entero, el
    comportamiento es el mismo de antes (se guarda la respuesta original)."""

    expected_answer: str | None = None


class ExerciseDeleteRequest(BaseModel):
    """Body de `PATCH /exercises/{id}` (tarea 2.4): este endpoint solo
    expone el borrado logico (`deleted_at`), no una edicion general del
    ejercicio -- `deleted` tiene que venir explicitamente en `true`."""

    deleted: Literal[True]


__all__ = [
    "SavedExercise",
    "SavedExerciseListItem",
    "SaveExerciseRequest",
    "ExerciseDeleteRequest",
    "ExerciseType",
]
