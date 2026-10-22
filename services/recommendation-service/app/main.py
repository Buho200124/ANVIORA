from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import engine
from app.middleware.error_handler import (
    manejador_errores_bd,
    manejador_errores_generico,
    manejador_errores_validacion,
)
from app.observability import comprobar_base_de_datos, instrumentar
from app.routers import internal_router, recommendations_router

app = FastAPI(
    title="ANVIORA - Servicio de recomendaciones",
    description="Motor de reglas de autocuidado (RF-04). No reemplaza la atención profesional.",
    version="2.0.0",
)

_origenes = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origenes,
    allow_credentials=_origenes != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, manejador_errores_validacion)
app.add_exception_handler(SQLAlchemyError, manejador_errores_bd)
app.add_exception_handler(Exception, manejador_errores_generico)

app.include_router(recommendations_router.router)
app.include_router(internal_router.router)
instrumentar(app, "recommendation-service", {"base_de_datos": lambda: comprobar_base_de_datos(engine)})
