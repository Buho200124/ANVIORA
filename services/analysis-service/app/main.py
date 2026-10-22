import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.middleware.error_handler import manejador_errores_generico, manejador_errores_validacion
from app.observability import instrumentar
from app.routers import internal_router
from app.services import sentiment_service

logger = logging.getLogger("anviora")


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Al arrancar, carga el modelo en segundo plano; /ready responde 503 hasta que termine."""
    if settings.PRECARGAR_MODELO:

        async def _precargar():
            try:
                await asyncio.get_running_loop().run_in_executor(None, sentiment_service.precargar_modelo)
                logger.info("Modelo de sentimiento cargado y listo")
            except Exception:
                logger.exception("No se pudo precargar el modelo de sentimiento")

        app.state.tarea_precarga = asyncio.create_task(_precargar())
    yield


app = FastAPI(
    title="ANVIORA - Servicio de análisis de IA",
    description="Anonimización de PII y análisis de sentimiento en español (RF-03). Solo uso interno.",
    version="2.0.0",
    lifespan=ciclo_de_vida,
)

app.add_exception_handler(RequestValidationError, manejador_errores_validacion)
app.add_exception_handler(Exception, manejador_errores_generico)

app.include_router(internal_router.router)
# Con la precarga activa el servicio solo está "listo" cuando el modelo ya está en memoria;
# con la precarga apagada (carga perezosa) no se exige, o /ready quedaría en 503 para siempre.
instrumentar(
    app,
    "analysis-service",
    {"modelo_cargado": lambda: sentiment_service.modelo_cargado() or not settings.PRECARGAR_MODELO},
)
