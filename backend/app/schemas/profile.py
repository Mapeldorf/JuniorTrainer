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
