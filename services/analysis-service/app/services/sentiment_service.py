import asyncio
import logging
import re
from typing import List, Tuple

logger = logging.getLogger("anviora")

_analizador_sentimiento = None  # Carga perezosa (singleton) del modelo de pysentimiento

_CONECTORES_COMUNES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "a",
    "en", "que", "es", "por", "para", "con", "se", "su", "sus", "lo", "le", "me",
    "mi", "yo", "tu", "no", "si", "muy", "más", "pero", "como", "esta", "este",
}


def _obtener_analizador():
    """Carga el analizador de pysentimiento una sola vez para no recargar el modelo en cada petición."""
    global _analizador_sentimiento
    if _analizador_sentimiento is None:
        from pysentimiento import create_analyzer

        _analizador_sentimiento = create_analyzer(task="sentiment", lang="es")
    return _analizador_sentimiento


def modelo_cargado() -> bool:
    """Readiness: True cuando el modelo de pysentimiento ya está en memoria."""
    return _analizador_sentimiento is not None


def precargar_modelo() -> None:
    """Carga el modelo al arrancar para que el primer usuario no espere la descarga/carga."""
    _obtener_analizador()


def _mapear_polaridad(etiqueta: str) -> str:
    """Traduce la etiqueta de pysentimiento (POS/NEU/NEG) al dominio del sistema."""
    return {"POS": "Positivo", "NEU": "Neutro", "NEG": "Negativo"}.get(etiqueta, "Neutro")


# Marcadores que deja el anonimizador ([CORREO_OMITIDO], [URL_OMITIDA], [NUMERO_OMITIDO]):
# no son palabras del usuario, así que no deben aparecer como palabras clave.
_PATRON_MARCADOR = re.compile(r"\[[A-Z_]+_OMITID[AO]\]")


def _extraer_palabras_clave(texto: str, maximo: int = 8) -> List[str]:
    """Extracción simple de palabras clave por frecuencia, descartando conectores comunes en español."""
    texto = _PATRON_MARCADOR.sub(" ", texto)
    palabras = re.findall(r"[a-záéíóúñ]{4,}", texto.lower())
    frecuencias: dict = {}
    for palabra in palabras:
        if palabra in _CONECTORES_COMUNES:
            continue
        frecuencias[palabra] = frecuencias.get(palabra, 0) + 1
    ordenadas = sorted(frecuencias.items(), key=lambda item: item[1], reverse=True)
    return [palabra for palabra, _ in ordenadas[:maximo]]


async def analizar_sentimiento(texto_anonimizado: str) -> Tuple[str, float, List[str]]:
    """
    Ejecuta el análisis de sentimiento de forma asíncrona y no bloqueante (RNF-01),
    delegando el trabajo pesado del modelo a un hilo aparte con run_in_executor.
    Devuelve (polaridad, puntuacion_confianza, palabras_clave).
    """
    if not texto_anonimizado or not texto_anonimizado.strip():
        return "Neutro", 0.0, []

    ciclo = asyncio.get_running_loop()
    polaridad, confianza = "Neutro", 0.0
    try:
        analizador = await ciclo.run_in_executor(None, _obtener_analizador)
        resultado = await ciclo.run_in_executor(None, analizador.predict, texto_anonimizado)
        polaridad = _mapear_polaridad(resultado.output)
        confianza = float(max(resultado.probas.values())) if resultado.probas else 0.0
    except Exception as error:  # Degradación segura si el modelo falla o no está disponible
        logger.error("Fallo el análisis de sentimiento: %s", error)

    palabras_clave = _extraer_palabras_clave(texto_anonimizado)
    return polaridad, confianza, palabras_clave
