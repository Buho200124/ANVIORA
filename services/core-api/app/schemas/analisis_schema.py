from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class AnalisisIARespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_analisis: int
    id_registro: int
    polaridad_sentimiento: Optional[str]
    puntuacion_confianza: Optional[float]
    palabras_clave: List[str]
    estado_procesamiento: str
    fecha_procesamiento: Optional[datetime]
