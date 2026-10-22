from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import obtener_usuario_actual
from app.models.usuario import Usuario
from app.schemas.auth_schema import TokenRespuesta, UsuarioLogin, UsuarioRegistro, UsuarioRespuesta
from app.services.auth_service import autenticar_usuario, registrar_usuario

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/register", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
def registrar(datos: UsuarioRegistro, db: Session = Depends(get_db)):
    """RF-01: registro de usuario con contraseña cifrada con bcrypt (RNF-02)."""
    return registrar_usuario(db, datos)


@router.post("/login", response_model=TokenRespuesta)
def iniciar_sesion(datos: UsuarioLogin, db: Session = Depends(get_db)):
    """RF-01: inicio de sesión con generación de JWT."""
    token = autenticar_usuario(db, datos.correo, datos.contrasena)
    return TokenRespuesta(access_token=token)


@router.post("/logout", status_code=status.HTTP_200_OK)
def cerrar_sesion(usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    """
    RF-01: cierre de sesión. Al usar JWT sin estado, la invalidación real ocurre
    cuando el cliente descarta el token; este endpoint queda como punto de
    extensión si más adelante se agrega una lista negra de tokens revocados.
    """
    return {"mensaje": "Sesión cerrada correctamente"}
