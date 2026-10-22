"""Pruebas de los clientes HTTP del core-api (reintentos y propagación de la clave interna)."""
import httpx
import pytest

from app.services import clients


class _RespuestaFalsa:
    def __init__(self, datos, estado=200):
        self._datos, self.status_code = datos, estado

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)

    def json(self):
        return self._datos


def _cliente_falso(respuestas, llamadas):
    class ClienteFalso:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None, headers=None):
            llamadas.append({"url": url, "json": json, "headers": headers})
            resultado = respuestas.pop(0)
            if isinstance(resultado, Exception):
                raise resultado
            return resultado

    return ClienteFalso


async def test_analizar_texto_envia_la_clave_interna_y_parsea_la_respuesta(monkeypatch):
    llamadas = []
    respuestas = [_RespuestaFalsa({"polaridad": "Positivo", "confianza": 0.8, "palabras_clave": ["feliz"]})]
    monkeypatch.setattr(clients.httpx, "AsyncClient", _cliente_falso(respuestas, llamadas))

    resultado = await clients.analizar_texto("estoy feliz")

    assert resultado == ("Positivo", 0.8, ["feliz"])
    assert llamadas[0]["url"].endswith("/internal/analyze")
    assert "X-Internal-Key" in llamadas[0]["headers"]


async def test_reintenta_una_vez_y_se_recupera(monkeypatch):
    llamadas = []
    respuestas = [httpx.ConnectError("sin red"), _RespuestaFalsa({"generadas": 0})]
    monkeypatch.setattr(clients.httpx, "AsyncClient", _cliente_falso(respuestas, llamadas))
    monkeypatch.setattr(clients.asyncio, "sleep", lambda s: _no_dormir())

    assert await clients.solicitar_recomendaciones(1, 2) == {"generadas": 0}
    assert len(llamadas) == 2


async def test_lanza_servicio_no_disponible_si_agota_los_intentos(monkeypatch):
    llamadas = []
    respuestas = [httpx.ConnectError("x"), httpx.ConnectError("y")]
    monkeypatch.setattr(clients.httpx, "AsyncClient", _cliente_falso(respuestas, llamadas))
    monkeypatch.setattr(clients.asyncio, "sleep", lambda s: _no_dormir())

    with pytest.raises(clients.ServicioNoDisponible):
        await clients.solicitar_recomendaciones(1, 2)


async def _no_dormir():
    return None
