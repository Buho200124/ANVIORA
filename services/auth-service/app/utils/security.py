from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings

# Factor de costo 12 (>= 10 exigido por RNF-02)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hashear_contrasena(contrasena: str) -> str:
    """Cifra la contraseña con bcrypt antes de guardarla (RNF-02)."""
    return pwd_context.hash(contrasena)


def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    """Compara una contraseña en texto plano contra su hash bcrypt almacenado."""
    return pwd_context.verify(contrasena_plana, contrasena_hash)


def crear_token_acceso(datos: dict) -> str:
    """Genera un JWT firmado con expiración (RF-01)."""
    a_codificar = datos.copy()
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    a_codificar["exp"] = expiracion
    return jwt.encode(a_codificar, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Decodifica y valida un JWT; lanza jwt.PyJWTError si es inválido o expiró."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
