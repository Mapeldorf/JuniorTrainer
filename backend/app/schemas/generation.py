from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.github_ref import InvalidGitHubRef, validate_owner_or_repo

GenerationKind = Literal["knowledge", "debug", "both"]
GenerationStatus = Literal["generating", "ready", "done", "error"]
ExerciseType = Literal["knowledge", "debug"]


class StartGenerationRequest(BaseModel):
    """Body de `POST /generations` (tarea 6.2, actualizada por el change
    `acceso-repo-github-tool`). Requisitos "Entrada minima de una
    generacion" y "Numero de ejercicios candidatos": `technologies` no
    puede quedar vacia tras normalizar, y `count` tiene que caer en 1-5.
    El repositorio ya no se acepta como ruta local ni URL (`repo_path`):
    se referencia como `owner`/`repo` (requisito "Referencia de entrada
    del repositorio" de `specs/github-repo-access/spec.md`), validados con
    la misma regla que usa la propia API de GitHub para esos nombres.
    Todo esto lo fuerza Pydantic antes de que el endpoint cree ninguna
    fila, asi que una entrada invalida nunca llega a tocar Supabase (422
    de FastAPI, no un 4xx escrito a mano)."""

    technologies: list[str] = Field(min_length=1)
    owner: str | None = None
    repo: str | None = None
    kind: GenerationKind
    count: int = Field(ge=1, le=5)

    @field_validator("technologies")
    @classmethod
    def _normalize_technologies(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item.strip()]
        if not normalized:
            raise ValueError("se necesita al menos una tecnologia")
        return normalized

    @field_validator("owner")
    @classmethod
    def _validate_owner(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return validate_owner_or_repo(value, field="owner")
        except InvalidGitHubRef as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("repo")
    @classmethod
    def _validate_repo(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return validate_owner_or_repo(value, field="repo")
        except InvalidGitHubRef as exc:
            raise ValueError(str(exc)) from exc

    @model_validator(mode="after")
    def _owner_and_repo_together(self) -> "StartGenerationRequest":
        if (self.owner is None) != (self.repo is None):
            raise ValueError("owner y repo se indican juntos, o ninguno de los dos")
        return self

    @model_validator(mode="after")
    def _kind_requires_repo(self) -> "StartGenerationRequest":
        """Requisito "Tipo de ejercicio exige repositorio salvo
        conocimiento" de `specs/exercise-generation/spec.md`: sin
        repositorio, el agente de codigo no se ejecuta, asi que un
        candidato `debug` no tendria fragmento de codigo que depurar."""
        if self.repo is None and self.kind != "knowledge":
            raise ValueError("sin repositorio solo se puede pedir el tipo knowledge")
        return self


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
    repo: str | None = None
    kind: GenerationKind
    error_message: str | None = None
    created_at: str
