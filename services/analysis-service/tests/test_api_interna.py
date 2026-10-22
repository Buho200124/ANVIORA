"""Pruebas de la API interna del analysis-service (sin cargar el modelo real)."""
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.routers import internal_router
from app.services import sentiment_service

cliente = TestClient(app)
CLAVE = {"X-Internal-Key": "clave-interna-de-pruebas"}


def test_exige_clave_interna():
    assert cliente.post("/internal/analyze", json={"texto": "hola"}).status_code == 401


def test_anonimiza_antes_de_analizar_y_devuelve_el_resultado():
    simulado = AsyncMock(return_value=("Negativo", 0.93, ["estres"]))
    with patch.object(internal_router, "analizar_sentimiento", simulado):
        r = cliente.post(
            "/internal/analyze",
            json={"texto": "Estoy agotado, escríbeme a juan@correo.com"},
            headers=CLAVE,
        )
    assert r.status_code == 200
    assert r.json() == {"polaridad": "Negativo", "confianza": 0.93, "palabras_clave": ["estres"]}
    texto_enviado_al_modelo = simulado.await_args.args[0]
    assert "juan@correo.com" not in texto_enviado_al_modelo
    assert "[CORREO_OMITIDO]" in texto_enviado_al_modelo


def test_texto_vacio_devuelve_neutro_sin_tocar_el_modelo():
    r = cliente.post("/internal/analyze", json={"texto": ""}, headers=CLAVE)
    assert r.status_code == 200
    assert r.json() == {"polaridad": "Neutro", "confianza": 0.0, "palabras_clave": []}


def test_rechaza_textos_demasiado_largos():
    r = cliente.post("/internal/analyze", json={"texto": "a" * 2001}, headers=CLAVE)
    assert r.status_code == 422


def test_ready_es_503_hasta_que_el_modelo_este_cargado(monkeypatch):
    monkeypatch.setattr(settings, "PRECARGAR_MODELO", True)
    monkeypatch.setattr(sentiment_service, "_analizador_sentimiento", None)
    r = cliente.get("/ready")
    assert r.status_code == 503
    assert r.json()["comprobaciones"]["modelo_cargado"] == "fallo"

    monkeypatch.setattr(sentiment_service, "_analizador_sentimiento", object())
    r = cliente.get("/ready")
    assert r.status_code == 200


def test_ready_no_exige_el_modelo_si_la_precarga_esta_apagada(monkeypatch):
    # Carga perezosa: el modelo se baja en la primera petición, así que no puede bloquear /ready
    monkeypatch.setattr(settings, "PRECARGAR_MODELO", False)
    monkeypatch.setattr(sentiment_service, "_analizador_sentimiento", None)
    assert cliente.get("/ready").status_code == 200


def test_los_marcadores_de_anonimizacion_no_son_palabras_clave():
    texto = "Estoy estresado por el examen [CORREO_OMITIDO] [NUMERO_OMITIDO] [URL_OMITIDA] examen"
    claves = sentiment_service._extraer_palabras_clave(texto)
    assert claves[0] == "examen"
    for basura in ("omitido", "omitida", "correo", "numero"):
        assert basura not in claves


def test_health_siempre_responde():
    assert cliente.get("/health").json() == {"estado": "vivo", "servicio": "analysis-service"}


def test_un_texto_rechazado_no_se_escribe_en_los_logs(caplog):
    import logging

    secreto = "TEXTO-PRIVADO " * 300  # > 2000 caracteres
    with caplog.at_level(logging.INFO):
        r = cliente.post("/internal/analyze", json={"texto": secreto}, headers=CLAVE)
    assert r.status_code == 422
    assert "TEXTO-PRIVADO" not in " ".join(registro.getMessage() for registro in caplog.records)
