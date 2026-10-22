"""Pruebas de los endpoints de operación del auth-service (health, ready, metrics)."""
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_health_responde_vivo():
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json() == {"estado": "vivo", "servicio": "auth-service"}


def test_ready_devuelve_503_si_la_bd_no_responde(monkeypatch):
    import app.main as principal

    class MotorCaido:
        def connect(self):
            raise RuntimeError("sin conexión a PostgreSQL")

    monkeypatch.setattr(principal, "engine", MotorCaido())
    r = cliente.get("/ready")
    assert r.status_code == 503
    assert r.json()["comprobaciones"]["base_de_datos"] == "fallo"


def test_metrics_expone_formato_prometheus():
    cliente.get("/health")
    r = cliente.get("/metrics")
    assert r.status_code == 200
    assert "anviora_http_requests_total" in r.text or "python_info" in r.text


def test_cada_respuesta_trae_x_request_id():
    r = cliente.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"
