from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RegistroEmocional(Base):
    """Modelo ORM de registros_emocionales: registro diario de ánimo, sueño y estrés (RF-02)."""

    __tablename__ = "registros_emocionales"

    id_registro = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    fecha_registro = Column(Date, server_default=func.current_date(), nullable=False)
    estado_animo = Column(SmallInteger, nullable=False)
    horas_sueno = Column(Numeric(4, 2), nullable=False)
    nivel_estres = Column(SmallInteger, nullable=False)
    etiquetas_actividades = Column(ARRAY(String), default=list)
    descripcion_texto = Column(Text)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="registros")
    analisis = relationship("AnalisisIA", back_populates="registro", uselist=False, cascade="all, delete-orphan")
    recomendaciones = relationship("Recomendacion", back_populates="registro")

    __table_args__ = (
        UniqueConstraint("id_usuario", "fecha_registro", name="uq_registro_usuario_fecha"),
        CheckConstraint("estado_animo BETWEEN 1 AND 5", name="chk_estado_animo"),
        CheckConstraint("nivel_estres BETWEEN 1 AND 5", name="chk_nivel_estres"),
        CheckConstraint("horas_sueno BETWEEN 0 AND 24", name="chk_horas_sueno"),
    )
