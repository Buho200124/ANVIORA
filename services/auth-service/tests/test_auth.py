"""
Pruebas unitarias de autenticación (RF-01, RNF-02).

Cubren el cifrado de contraseñas con bcrypt, la generación y validación
de JWT, y las reglas de negocio de auth_service. La sesión de BD se
reemplaza por un doble de prueba (MagicMock), así estas pruebas no
requieren una base de datos real ni el resto de la aplicación en pie.
"""
import jwt as pyjwt
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from app.models.usuario import Usuario
from app.schemas.auth_schema import UsuarioRegistro
from app.services.auth_service import autenticar_usuario, registrar_usuario
from app.utils.security import crear_token_acceso, decodificar_token, hashear_contrasena, verificar_contrasena


class TestCifradoDeContrasenas:
    def test_el_hash_es_distinto_al_texto_plano(self):
        contrasena = "claveSegura123"
        resultado = hashear_contrasena(contrasena)
        assert resultado != contrasena
        assert resultado.startswith("$2b$")

    def test_verifica_correctamente_la_contrasena_correcta(self):
        contrasena = "claveSegura123"
        hash_guardado = hashear_contrasena(contrasena)
        assert verificar_contrasena(contrasena, hash_guardado) is True

    def test_rechaza_una_contrasena_incorrecta(self):
        hash_guardado = hashear_contrasena("claveSegura123")
        assert verificar_contrasena("otraClave", hash_guardado) is False

    def test_dos_hashes_de_la_misma_contrasena_son_distintos(self):
        # bcrypt aplica un salt aleatorio en cada llamada (RNF-02)
        contrasena = "claveSegura123"
        assert hashear_contrasena(contrasena) != hashear_contrasena(contrasena)


class TestTokenJWT:
    def test_crea_y_decodifica_un_token_valido(self):
        token = crear_token_acceso({"sub": "1"})
        payload = decodificar_token(token)
        assert payload["sub"] == "1"
        assert "exp" in payload

    def test_un_token_invalido_lanza_error(self):
        with pytest.raises(pyjwt.PyJWTError):
            decodificar_token("esto-no-es-un-token-valido")


def _sesion_simulada(usuario_encontrado):
    """Doble de prueba de una sesión de SQLAlchemy que siempre devuelve el mismo resultado."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = usuario_encontrado
    return db


class TestRegistrarUsuario:
    def test_crea_una_cuenta_nueva_con_la_contrasena_cifrada(self):
        db = _sesion_simulada(usuario_encontrado=None)
        datos = UsuarioRegistro(nombre="Búho", correo="buho@example.com", contrasena="claveSegura123")

        usuario_creado = registrar_usuario(db, datos)

        assert usuario_creado.correo == "buho@example.com"
        assert usuario_creado.contrasena_hash != "claveSegura123"
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_rechaza_un_correo_ya_registrado_con_error_400(self):
        usuario_existente = Usuario(id_usuario=1, nombre="Otro", correo="buho@example.com", contrasena_hash="hash")
        db = _sesion_simulada(usuario_encontrado=usuario_existente)
        datos = UsuarioRegistro(nombre="Búho", correo="buho@example.com", contrasena="claveSegura123")

        with pytest.raises(HTTPException) as excepcion:
            registrar_usuario(db, datos)

        assert excepcion.value.status_code == 400


class TestAutenticarUsuario:
    def test_credenciales_correctas_devuelven_un_token_valido(self):
        usuario = Usuario(
            id_usuario=7,
            nombre="Búho",
            correo="buho@example.com",
            contrasena_hash=hashear_contrasena("claveSegura123"),
            activo=True,
        )
        db = _sesion_simulada(usuario_encontrado=usuario)

        token = autenticar_usuario(db, "buho@example.com", "claveSegura123")

        assert decodificar_token(token)["sub"] == "7"

    def test_contrasena_incorrecta_lanza_error_401(self):
        usuario = Usuario(
            id_usuario=7, nombre="Búho", correo="buho@example.com",
            contrasena_hash=hashear_contrasena("claveSegura123"), activo=True,
        )
        db = _sesion_simulada(usuario_encontrado=usuario)

        with pytest.raises(HTTPException) as excepcion:
            autenticar_usuario(db, "buho@example.com", "incorrecta")

        assert excepcion.value.status_code == 401

    def test_correo_inexistente_lanza_error_401(self):
        db = _sesion_simulada(usuario_encontrado=None)

        with pytest.raises(HTTPException) as excepcion:
            autenticar_usuario(db, "nadie@example.com", "cualquierClave")

        assert excepcion.value.status_code == 401

    def test_cuenta_inactiva_lanza_error_403(self):
        usuario = Usuario(
            id_usuario=7, nombre="Búho", correo="buho@example.com",
            contrasena_hash=hashear_contrasena("claveSegura123"), activo=False,
        )
        db = _sesion_simulada(usuario_encontrado=usuario)

        with pytest.raises(HTTPException) as excepcion:
            autenticar_usuario(db, "buho@example.com", "claveSegura123")

        assert excepcion.value.status_code == 403
