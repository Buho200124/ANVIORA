from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecomendacionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_recomendacion: int
    tipo_recomendacion: str
    contenido_recomendacion: str
    nivel_prioridad: str
    vista: bool
    fecha_generacion: datetime
