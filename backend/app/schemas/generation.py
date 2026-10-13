from typing import Literal

from pydantic import BaseModel, Field, field_validator

GenerationKind = Literal["knowledge", "debug", "both"]
GenerationStatus = Literal["generating", "ready", "done", "error"]
ExerciseType = Literal["knowledge", "debug"]


class StartGenerationRequest(BaseModel):
    """Body de `POST /generations` (tarea 6.2). Requisitos "Entrada minima
    de una generacion" y "Numero de ejercicios candidatos": `technologies`
    no puede quedar vacia tras normalizar, y `count` tiene que caer en
    1-5 -- ambas cosas ya las fuerza Pydantic antes de que el endpoint
    cree ninguna fila, asi que una entrada invalida nunca llega a tocar
    Supabase (422 de FastAPI, no un 4xx escrito a mano)."""

    technologies: list[str] = Field(min_length=1)
    repo_path: str | None = None
    kind: GenerationKind
    count: int = Field(ge=1, le=5)

    @field_validator("technologies")
    @classmethod
    def _normalize_technologies(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item.strip()]
        if not normalized:
            raise ValueError("se necesita al menos una tecnologia")
        return normalized

    @field_validator("repo_path")
    @classmethod
    def _normalize_repo_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class StartGenerationResponse(BaseModel):
    id: str


class ExerciseCodeBlock(BaseModel):
    file: str | None = None
    code: str


class ExerciseCandidate(BaseModel):
    id: str
    type: ExerciseType
    # Etiqueta corta (hasta 8 palabras), distinta del enunciado, pensada
    # como identificador visual en listados y selectores (change
    # `ejercicios-con-nombre`); el enunciado sigue siendo el texto que
    # resuelve el alumno.
    name: str
    statement: str
    code: list[ExerciseCodeBlock] = Field(default_factory=list)
    expected_answer: str | None = None


class GenerationStatusResponse(BaseModel):
    """Respuesta de `GET /generations/{id}` (tarea 6.3). `candidates` solo
    se rellena cuando `status == "ready"` -- en curso o error no tienen
    candidatos todavia (requisito "Estado de la generacion")."""

    id: str
    status: GenerationStatus
    error_message: str | None = None
    candidates: list[ExerciseCandidate] = Field(default_factory=list)


class GenerationSummary(BaseModel):
    """Fila de `GET /generations` (tarea 1.2 de frontend-tech-lead-ejercicios,
    capacidad exercise-generation: "Listar las generaciones pendientes").
    Sin `candidates` -- el listado es solo para que el tech lead vea y actue
    sobre sus generaciones no cerradas, no para revisar candidatos (eso sigue
    siendo `GET /generations/{id}`)."""

    id: str
    status: GenerationStatus
    technologies: list[str]
    repo_path: str | None = None
    kind: GenerationKind
    error_message: str | None = None
    created_at: str
