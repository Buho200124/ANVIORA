import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("anviora")


async def manejador_errores_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Errores de validación (RNF-04). Se registra solo campo y tipo, nunca el valor recibido:
    aquí el valor es el texto personal del usuario y no debe quedar en los logs.
    """
    resumen = [{"campo": ".".join(str(p) for p in e.get("loc", ())), "tipo": e.get("type")} for e in exc.errors()]
    logger.warning("Error de validación en %s: %s", request.url.path, resumen)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"mensaje": "Datos de entrada inválidos", "campos": [r["campo"] for r in resumen]},
    )


async def manejador_errores_generico(request: Request, exc: Exception) -> JSONResponse:
    """Último recurso (RNF-04), con traza para diagnosticar."""
    logger.error("Error no controlado en %s: %s", request.url.path, type(exc).__name__, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"mensaje": "Ocurrió un error interno en el servidor"},
    )
