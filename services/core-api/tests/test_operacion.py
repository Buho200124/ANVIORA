from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_health_responde_vivo():
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json() == {"estado": "vivo", "servicio": "core-api"}


def test_ready_devuelve_503_si_la_bd_no_responde(monkeypatch):
    import app.main as principal

    class MotorCaido:
        def connect(self):
            raise RuntimeError("sin conexión a PostgreSQL")

    monkeypatch.setattr(principal, "engine", MotorCaido())
    r = cliente.get("/ready")
    assert r.status_code == 503
    assert r.json()["comprobaciones"]["base_de_datos"] == "fallo"


def test_las_rutas_privadas_exigen_token():
    assert cliente.get("/api/logs").status_code == 401
    assert cliente.get("/api/dashboard/stats").status_code == 401
