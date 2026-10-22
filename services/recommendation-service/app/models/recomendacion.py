from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Recomendacion(Base):
    """Modelo ORM de recomendaciones: sugerencias de autocuidado (RF-04)."""

    __tablename__ = "recomendaciones"

    id_recomendacion = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    id_registro = Column(Integer, ForeignKey("registros_emocionales.id_registro", ondelete="SET NULL"), nullable=True)
    tipo_recomendacion = Column(String(50), nullable=False)
    contenido_recomendacion = Column(Text, nullable=False)
    nivel_prioridad = Column(String(10), nullable=False, default="media")
    vista = Column(Boolean, nullable=False, default=False)
    fecha_generacion = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="recomendaciones")
    registro = relationship("RegistroEmocional", back_populates="recomendaciones")

    __table_args__ = (CheckConstraint("nivel_prioridad IN ('baja','media','alta')", name="chk_prioridad"),)
