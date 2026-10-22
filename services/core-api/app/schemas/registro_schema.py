from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RegistroEmocionalCrear(BaseModel):
    estado_animo: int = Field(..., ge=1, le=5, description="Escala de ánimo de 1 (muy bajo) a 5 (muy alto)")
    horas_sueno: float = Field(..., ge=0, le=24)
    nivel_estres: int = Field(..., ge=1, le=5, description="Escala de estrés de 1 (muy bajo) a 5 (muy alto)")
    etiquetas_actividades: List[str] = Field(default_factory=list)
    descripcion_texto: Optional[str] = Field(None, max_length=2000)


class RegistroEmocionalRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_registro: int
    fecha_registro: date
    estado_animo: int
    horas_sueno: float
    nivel_estres: int
    etiquetas_actividades: List[str]
    descripcion_texto: Optional[str]
    fecha_creacion: datetime
