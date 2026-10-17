from pydantic import BaseModel


class Technology(BaseModel):
    """Fila del catálogo canónico de tecnologías (change `catalogo-tecnologias`,
    capacidad technology-catalog: "Consulta del catálogo por el tech lead").
    `name` es el nombre canónico estable que usa el formulario de generación y
    que alimenta las claves de caché de memoria de los agentes."""

    id: str
    name: str