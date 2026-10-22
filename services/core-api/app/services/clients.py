"""
Clientes HTTP hacia los otros microservicios (analysis-service y recommendation-service).

Cada llamada reintenta una vez y propaga el X-Request-ID para poder seguir una
misma operación a través de los logs de todos los servicios.
"""
import asyncio
import logging
from typing import List, Tuple

import httpx

from app.config import settings
from app.observability import request_id_ctx

logger = logging.getLogger("anviora")

TIMEOUT_ANALISIS_S = 60.0  # el primer análisis puede tardar mientras el modelo termina de cargar
TIMEOUT_RECOMENDACIONES_S = 15.0


class ServicioNoDisponible(Exception):
    """El microservicio remoto no respondió correctamente tras los reintentos."""


async def _post_interno(url: str, cuerpo: dict, timeout: float, intentos: int = 2) -> dict:
    cabeceras = {"X-Internal-Key": settings.INTERNAL_API_KEY, "X-Request-ID": request_id_ctx.get()}
    ultimo_error: Exception = RuntimeError("sin intentos")
    for intento in range(1, intentos + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as cliente:
                respuesta = await cliente.post(url, json=cuerpo, headers=cabeceras)
                respuesta.raise_for_status()
                return respuesta.json()
        except httpx.HTTPError as error:
            ultimo_error = error
            logger.warning("Intento %s/%s fallido hacia %s: %s", intento, intentos, url, error)
            if intento < intentos:
                await asyncio.sleep(1)
    raise ServicioNoDisponible(f"No se pudo completar la llamada a {url}") from ultimo_error


async def analizar_texto(texto: str) -> Tuple[str, float, List[str]]:
    """Pide al analysis-service anonimizar y analizar el texto. Devuelve (polaridad, confianza, palabras_clave)."""
    datos = await _post_interno(
        f"{settings.ANALYSIS_SERVICE_URL}/internal/analyze", {"texto": texto}, TIMEOUT_ANALISIS_S
    )
    return datos["polaridad"], float(datos["confianza"]), list(datos["palabras_clave"])


async def solicitar_recomendaciones(id_usuario: int, id_registro: int) -> dict:
    """Pide al recommendation-service evaluar las reglas para un registro recién analizado."""
    return await _post_interno(
        f"{settings.RECOMMENDATION_SERVICE_URL}/internal/evaluate",
        {"id_usuario": id_usuario, "id_registro": id_registro},
        TIMEOUT_RECOMENDACIONES_S,
    )
