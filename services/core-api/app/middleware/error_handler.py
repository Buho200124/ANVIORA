import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("anviora")


def _resumen_validacion(errores: list) -> list:
    """
    Solo campo y tipo de error. NUNCA el valor recibido ("input"): podría ser una contraseña,
    un correo o el texto personal que escribió el usuario, y los logs no deben guardarlo.
    """
    return [{"campo": ".".join(str(p) for p in e.get("loc", ())), "tipo": e.get("type")} for e in errores]


async def manejador_errores_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Centraliza los errores de validación de entradas (RNF-04)."""
    logger.warning("Error de validación en %s: %s", request.url.path, _resumen_validacion(exc.errors()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"mensaje": "Datos de entrada inválidos", "detalles": exc.errors()},
    )


async def manejador_errores_bd(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Centraliza los errores de la base de datos (RNF-04). Se registra el tipo y la primera línea del
    error del motor; el mensaje completo de SQLAlchemy incluye los parámetros de la consulta (datos del usuario).
    """
    causa = str(getattr(exc, "orig", exc)).splitlines()[0] if str(getattr(exc, "orig", exc)) else ""
    logger.error("Error de base de datos en %s: %s: %s", request.url.path, type(exc).__name__, causa)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"mensaje": "Ocurrió un error interno al acceder a la base de datos"},
    )


async def manejador_errores_generico(request: Request, exc: Exception) -> JSONResponse:
    """Último recurso: captura cualquier excepción no controlada (RNF-04), con traza para diagnosticar."""
    logger.error("Error no controlado en %s: %s", request.url.path, type(exc).__name__, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"mensaje": "Ocurrió un error interno en el servidor"},
    )
