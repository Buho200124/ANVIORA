import re

# Patrones básicos de Datos Personales Identificables (PII) a enmascarar
# antes de enviar cualquier texto al motor de análisis de IA (RF-03, RNF-02).
_PATRON_CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PATRON_URL = re.compile(r"https?://\S+")
_PATRON_NUMERO_ID = re.compile(r"\b\d{6,15}\b")  # Teléfonos, cédulas u otros números identificatorios


def anonimizar_texto(texto: str) -> str:
    """
    Elimina/enmascara Datos Personales Identificables del texto libre antes de
    enviarlo a la IA (RF-03). Cubre los patrones más comunes: correos, URLs y
    números largos que suelen corresponder a teléfonos o documentos de identidad.
    No sustituye una anonimización forense completa, pero es suficiente para el
    alcance de este prototipo académico.
    """
    if not texto:
        return texto

    texto_anonimizado = _PATRON_CORREO.sub("[CORREO_OMITIDO]", texto)
    texto_anonimizado = _PATRON_URL.sub("[URL_OMITIDA]", texto_anonimizado)
    texto_anonimizado = _PATRON_NUMERO_ID.sub("[NUMERO_OMITIDO]", texto_anonimizado)
    return texto_anonimizado
