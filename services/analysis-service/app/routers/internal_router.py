from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.anonymizer_service import anonimizar_texto
from app.services.sentiment_service import analizar_sentimiento
from app.utils.internal_auth import verificar_clave_interna

router = APIRouter(prefix="/internal", tags=["Interno"], dependencies=[Depends(verificar_clave_interna)])


class SolicitudAnalisis(BaseModel):
    texto: str = Field("", max_length=2000)


class RespuestaAnalisis(BaseModel):
    polaridad: str
    confianza: float
    palabras_clave: List[str]


@router.post("/analyze", response_model=RespuestaAnalisis)
async def analizar(datos: SolicitudAnalisis):
    """
    RF-03: anonimiza el texto (correos, URLs, números largos) y analiza su sentimiento.
    El texto original nunca se guarda ni se registra en logs en este servicio.
    """
    texto_anonimizado = anonimizar_texto(datos.texto)
    polaridad, confianza, palabras_clave = await analizar_sentimiento(texto_anonimizado)
    return RespuestaAnalisis(polaridad=polaridad, confianza=confianza, palabras_clave=palabras_clave)
