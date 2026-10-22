"""Los logs no deben guardar contraseñas ni otros valores enviados por el usuario."""
import logging

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app, raise_server_exceptions=False)


def test_una_contrasena_rechazada_no_queda_en_los_logs(caplog):
    with caplog.at_level(logging.INFO):
        r = cliente.post(
            "/api/auth/register",
            json={"nombre": "Ana", "correo": "ana@correo.com", "contrasena": "corta"},
        )
    assert r.status_code == 422
    texto_logs = " ".join(registro.getMessage() for registro in caplog.records)
    assert "corta" not in texto_logs
    assert "ana@correo.com" not in texto_logs
    assert "contrasena" in texto_logs  # sí se registra QUÉ campo falló
