"""
Observabilidad común de los microservicios de ANVIORA (fase Operate).

- Logs en formato JSON, con un ID por petición para rastrearla entre servicios.
- /health  -> liveness: el proceso está vivo.
- /ready   -> readiness: el servicio puede atender tráfico (BD, modelo, etc.).
- /metrics -> métricas en formato Prometheus.
"""
import contextvars
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

request_id_ctx: contextvars.ContextVar = contextvars.ContextVar("request_id", default="-")

PETICIONES = Counter(
    "anviora_http_requests_total", "Total de peticiones HTTP", ["servicio", "metodo", "ruta", "estado"]
)
DURACION = Histogram(
    "anviora_http_request_duration_seconds", "Duración de las peticiones HTTP (s)", ["servicio", "metodo", "ruta"]
)

_RUTAS_SILENCIOSAS = {"/health", "/ready", "/metrics"}


class FormateadorJson(logging.Formatter):
    """Una línea JSON por log: fácil de leer para personas y de procesar para herramientas."""

    def __init__(self, servicio: str):
        super().__init__()
        self.servicio = servicio

    def format(self, record: logging.LogRecord) -> str:
        datos = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "nivel": record.levelname,
            "servicio": self.servicio,
            "logger": record.name,
            "mensaje": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info:
            datos["excepcion"] = self.formatException(record.exc_info)
        return json.dumps(datos, ensure_ascii=False)


def configurar_logging(servicio: str) -> None:
    manejador = logging.StreamHandler()
    manejador.setFormatter(FormateadorJson(servicio))
    raiz = logging.getLogger()
    raiz.handlers = [manejador]
    raiz.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    for nombre in ("uvicorn", "uvicorn.error"):
        registro = logging.getLogger(nombre)
        registro.handlers = []
        registro.propagate = True
    # Cada petición ya se registra abajo con su ID; el access log de uvicorn solo duplicaría ruido.
    logging.getLogger("uvicorn.access").disabled = True


def comprobar_base_de_datos(engine) -> bool:
    """Readiness de la BD: ejecuta un SELECT 1."""
    from sqlalchemy import text

    with engine.connect() as conexion:
        conexion.execute(text("SELECT 1"))
    return True


def instrumentar(
    app: FastAPI,
    servicio: str,
    comprobaciones_ready: Optional[Dict[str, Callable[[], bool]]] = None,
) -> None:
    """Agrega logging JSON, métricas y los endpoints /health, /ready y /metrics a un servicio."""
    configurar_logging(servicio)
    log_http = logging.getLogger("anviora.http")
    log = logging.getLogger("anviora")
    comprobaciones = comprobaciones_ready or {}

    @app.middleware("http")
    async def registrar_peticion(request: Request, call_next):
        id_peticion = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        token = request_id_ctx.set(id_peticion)
        inicio = time.perf_counter()
        estado = 500
        try:
            respuesta = await call_next(request)
            estado = respuesta.status_code
            respuesta.headers["X-Request-ID"] = id_peticion
            return respuesta
        finally:
            if request.url.path not in _RUTAS_SILENCIOSAS:
                ruta = getattr(request.scope.get("route"), "path", "no_encontrada")
                duracion = time.perf_counter() - inicio
                PETICIONES.labels(servicio, request.method, ruta, str(estado)).inc()
                DURACION.labels(servicio, request.method, ruta).observe(duracion)
                log_http.info("%s %s -> %s (%.0f ms)", request.method, request.url.path, estado, duracion * 1000)
            request_id_ctx.reset(token)

    @app.get("/health", tags=["Operación"])
    def health():
        """Liveness: responde si el proceso está vivo. Lo usa Docker para reiniciar contenedores caídos."""
        return {"estado": "vivo", "servicio": servicio}

    @app.get("/ready", tags=["Operación"])
    def ready():
        """Readiness: responde 200 solo si las dependencias del servicio (BD, modelo) están disponibles."""
        detalle = {}
        for nombre, comprobar in comprobaciones.items():
            try:
                detalle[nombre] = "ok" if comprobar() else "fallo"
            except Exception as error:
                log.error("Comprobación '%s' fallida: %s", nombre, error)
                detalle[nombre] = "fallo"
        listo = all(valor == "ok" for valor in detalle.values())
        return JSONResponse(
            status_code=200 if listo else 503,
            content={"estado": "listo" if listo else "no_listo", "servicio": servicio, "comprobaciones": detalle},
        )

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
