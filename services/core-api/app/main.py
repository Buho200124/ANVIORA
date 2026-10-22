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
from app.routers import analysis_router, dashboard_router, logs_router

app = FastAPI(
    title="ANVIORA - API principal (core)",
    description=(
        "Registros diarios, consulta de análisis y dashboard. Herramienta de autoconocimiento y "
        "seguimiento preventivo: no es un dispositivo médico ni reemplaza la atención psicológica "
        "o psiquiátrica profesional."
    ),
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

app.include_router(logs_router.router)
app.include_router(analysis_router.router)
app.include_router(dashboard_router.router)
instrumentar(app, "core-api", {"base_de_datos": lambda: comprobar_base_de_datos(engine)})
