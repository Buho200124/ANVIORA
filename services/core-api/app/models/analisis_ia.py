from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AnalisisIA(Base):
    """Modelo ORM de analisis_ia: resultado del análisis de sentimiento (RF-03)."""

    __tablename__ = "analisis_ia"

    id_analisis = Column(Integer, primary_key=True, index=True)
    id_registro = Column(Integer, ForeignKey("registros_emocionales.id_registro", ondelete="CASCADE"), nullable=False)
    polaridad_sentimiento = Column(String(10))
    puntuacion_confianza = Column(Numeric(5, 4))
    palabras_clave = Column(ARRAY(String), default=list)
    estado_procesamiento = Column(String(20), nullable=False, default="pendiente")
    fecha_procesamiento = Column(DateTime(timezone=True))
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    registro = relationship("RegistroEmocional", back_populates="analisis")

    __table_args__ = (
        UniqueConstraint("id_registro", name="uq_analisis_registro"),
        CheckConstraint("polaridad_sentimiento IN ('Positivo','Neutro','Negativo')", name="chk_polaridad"),
        CheckConstraint(
            "estado_procesamiento IN ('pendiente','procesando','completado','error')",
            name="chk_estado_procesamiento",
        ),
    )
