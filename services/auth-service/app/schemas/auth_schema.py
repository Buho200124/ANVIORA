from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioRegistro(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    correo: EmailStr
    contrasena: str = Field(..., min_length=8, max_length=72)  # bcrypt limita a 72 bytes


class UsuarioLogin(BaseModel):
    correo: EmailStr
    contrasena: str


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    nombre: str
    correo: EmailStr
    fecha_registro: datetime


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"
