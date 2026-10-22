"""Pruebas del endpoint interno /internal/evaluate y de los endpoints de operación."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.routers import internal_router

CLAVE = {"X-Internal-Key": "clave-interna-de-pruebas"}


def _cliente_con_db(db):
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_sin_clave_interna_devuelve_401():
    cliente = _cliente_con_db(MagicMock())
    r = cliente.post("/internal/evaluate", json={"id_usuario": 1, "id_registro": 2})
    assert r.status_code == 401


def test_con_clave_incorrecta_devuelve_401():
    cliente = _cliente_con_db(MagicMock())
    r = cliente.post("/internal/evaluate", json={"id_usuario": 1, "id_registro": 2}, headers={"X-Internal-Key": "mala"})
    assert r.status_code == 401


def test_registro_inexistente_devuelve_404():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    cliente = _cliente_con_db(db)
    r = cliente.post("/internal/evaluate", json={"id_usuario": 1, "id_registro": 2}, headers=CLAVE)
    assert r.status_code == 404


def test_evalua_y_devuelve_cuantas_recomendaciones_se_generaron():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock()
    cliente = _cliente_con_db(db)
    with patch.object(internal_router, "evaluar_patrones_y_generar_recomendaciones", return_value=[object(), object()]):
        r = cliente.post("/internal/evaluate", json={"id_usuario": 1, "id_registro": 2}, headers=CLAVE)
    assert r.status_code == 200
    assert r.json() == {"generadas": 2}


def test_health_y_rutas_privadas():
    cliente = TestClient(app)
    assert cliente.get("/health").json() == {"estado": "vivo", "servicio": "recommendation-service"}
    assert cliente.get("/api/recommendations").status_code == 401
