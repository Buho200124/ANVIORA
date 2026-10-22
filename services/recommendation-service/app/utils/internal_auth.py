import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


def verificar_clave_interna(x_internal_key: str = Header(default="")) -> None:
    """
    Protege los endpoints /internal/*: solo otros servicios de ANVIORA (que conocen
    INTERNAL_API_KEY) pueden llamarlos. Además, el gateway bloquea /internal desde afuera.
    """
    if not secrets.compare_digest(x_internal_key.encode(), settings.INTERNAL_API_KEY.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clave interna inválida")
