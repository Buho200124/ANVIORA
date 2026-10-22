"""El texto personal del usuario no debe terminar en los logs cuando falla la validación."""
import logging

import jwt
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from unittest.mock import MagicMock


def test_texto_personal_invalido_no_queda_en_los_logs(caplog):
    usuario = MagicMock(id_usuario=1, activo=True)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = usuario
    app.dependency_overrides[get_db] = lambda: db
    token = jwt.encode({"sub": "1"}, "clave-de-pruebas-no-usar-en-produccion", algorithm="HS256")
    secreto = "MI-DIARIO-PRIVADO " * 200  # supera el máximo de 2000 caracteres

    try:
        with caplog.at_level(logging.INFO):
            r = TestClient(app, raise_server_exceptions=False).post(
                "/api/logs",
                json={"estado_animo": 3, "horas_sueno": 7, "nivel_estres": 2, "descripcion_texto": secreto},
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 422
    assert "MI-DIARIO-PRIVADO" not in " ".join(registro.getMessage() for registro in caplog.records)
