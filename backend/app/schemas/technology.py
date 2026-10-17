from pydantic import BaseModel, field_validator

# Mismo tope de longitud que aplica el backend a las tecnologias de una
# generacion (`app/schemas/generation.py`): el nombre del catalogo alimenta
# esa misma entrada.
_MAX_TECHNOLOGY_LENGTH = 60


class Technology(BaseModel):
    """Fila del catálogo canónico de tecnologías (change `catalogo-tecnologias`,
    capacidad technology-catalog: "Consulta del catálogo por el tech lead").
    `name` es el nombre canónico estable que usa el formulario de generación y
    que alimenta las claves de caché de memoria de los agentes."""

    id: str
    name: str


class NewTechnologyRequest(BaseModel):
    """Body de `POST /technologies` (change `generacion-tecnologias`,
    capacidad technology-catalog: "Alta de tecnologías por el tech lead").
    El nombre se recorta y no puede quedar vacío ni superar el tope de
    longitud; un valor inválido lo rechaza Pydantic (422) antes del endpoint.
    """

    name: str

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("el nombre de la tecnologia no puede estar vacio")
        if len(name) > _MAX_TECHNOLOGY_LENGTH:
            raise ValueError(
                f"el nombre de la tecnologia debe tener como maximo {_MAX_TECHNOLOGY_LENGTH} caracteres"
            )
        return name