from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Usuario(Base):
    """Modelo ORM de la tabla usuarios: cuentas y autenticación (RF-01)."""

    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(150), nullable=False, unique=True, index=True)
    contrasena_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    activo = Column(Boolean, nullable=False, default=True)

    registros = relationship("RegistroEmocional", back_populates="usuario", cascade="all, delete-orphan")
    recomendaciones = relationship("Recomendacion", back_populates="usuario", cascade="all, delete-orphan")
