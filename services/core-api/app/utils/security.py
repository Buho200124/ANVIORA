import jwt

from app.config import settings


def decodificar_token(token: str) -> dict:
    """
    Valida un JWT emitido por el auth-service (misma JWT_SECRET_KEY compartida).
    Lanza jwt.PyJWTError si es inválido o expiró. El core-api no crea ni cifra credenciales.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
