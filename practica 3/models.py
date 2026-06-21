from pydantic import BaseModel
from typing import Optional

class EstudianteCreate(BaseModel):
    nombre: str
    email: str

class EstudianteUpdate(BaseModel):
    nombre: Optional[str]
    email: Optional[str]

class LoginRequest(BaseModel):
    username: str
    password: str