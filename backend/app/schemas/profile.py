from typing import Literal

from pydantic import BaseModel, EmailStr

Role = Literal["tech_lead", "student"]


class Profile(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: Role


class InviteStudentRequest(BaseModel):
    name: str
    email: EmailStr


class StudentSummary(BaseModel):
    """Fila de la lista de alumnos (tarea 7.1, capacidad user-auth
    modificada, requisito "Listar alumnos"): solo lo que GET /users debe
    exponer, sin role (siempre 'student' aqui, no aporta nada a quien lo
    consume) ni ningun otro dato del perfil."""

    id: str
    name: str
    email: EmailStr
