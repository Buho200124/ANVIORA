from app.services.anonymizer_service import anonimizar_texto


def test_enmascara_correos():
    assert "[CORREO_OMITIDO]" in anonimizar_texto("escríbeme a ana.perez@correo.com hoy")
    assert "ana.perez" not in anonimizar_texto("escríbeme a ana.perez@correo.com hoy")


def test_enmascara_urls_y_numeros_largos():
    salida = anonimizar_texto("mira https://ejemplo.com/perfil y llámame al 3001234567")
    assert "[URL_OMITIDA]" in salida
    assert "[NUMERO_OMITIDO]" in salida
    assert "3001234567" not in salida


def test_no_altera_texto_sin_datos_personales():
    texto = "Hoy dormí poco y me sentí estresado en el trabajo"
    assert anonimizar_texto(texto) == texto


def test_texto_vacio_se_devuelve_igual():
    assert anonimizar_texto("") == ""
