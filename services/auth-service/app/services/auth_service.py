from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.auth_schema import UsuarioRegistro
from app.utils.security import crear_token_acceso, hashear_contrasena, verificar_contrasena


def registrar_usuario(db: Session, datos: UsuarioRegistro) -> Usuario:
    """Crea una cuenta nueva verificando que el correo no exista aún (RF-01)."""
    existente = db.query(Usuario).filter(Usuario.correo == datos.correo).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")

    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo,
        contrasena_hash=hashear_contrasena(datos.contrasena),
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


def autenticar_usuario(db: Session, correo: str, contrasena: str) -> str:
    """Valida las credenciales y devuelve un JWT firmado (RF-01)."""
    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()
    if not usuario or not verificar_contrasena(contrasena, usuario.contrasena_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos")
    if not usuario.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta inactiva")

    return crear_token_acceso({"sub": str(usuario.id_usuario)})
