"""
Pruebas del flujo de segundo plano del core-api tras separarlo en microservicios.

Se reemplazan la sesión de BD y los clientes HTTP por dobles de prueba: se valida la
orquestación (analizar -> guardar -> pedir recomendaciones) y la degradación segura
cuando un microservicio remoto falla.
"""
from unittest.mock import AsyncMock, MagicMock, patch

from app.routers import logs_router


def _db_con_analisis():
    analisis = MagicMock()
    analisis.estado_procesamiento = "pendiente"
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = analisis
    return db, analisis


async def test_flujo_exitoso_guarda_analisis_y_pide_recomendaciones():
    db, analisis = _db_con_analisis()
    with patch.object(logs_router, "SessionLocal", return_value=db), patch.object(
        logs_router.clients, "analizar_texto", AsyncMock(return_value=("Negativo", 0.91, ["estres"]))
    ) as analizar, patch.object(
        logs_router.clients, "solicitar_recomendaciones", AsyncMock(return_value={"generadas": 1})
    ) as recomendar:
        await logs_router._procesar_analisis_en_segundo_plano(7, "Día pesado", 3)

    analizar.assert_awaited_once_with("Día pesado")
    recomendar.assert_awaited_once_with(3, 7)
    assert analisis.estado_procesamiento == "completado"
    assert analisis.polaridad_sentimiento == "Negativo"
    assert analisis.palabras_clave == ["estres"]
    db.close.assert_called_once()


async def test_si_el_analysis_service_falla_el_estado_queda_en_error_pero_si_hay_recomendaciones():
    # Las reglas de estrés y sueño no dependen de la IA: una caída del análisis no debe quitarle la alerta al usuario
    db, analisis = _db_con_analisis()
    with patch.object(logs_router, "SessionLocal", return_value=db), patch.object(
        logs_router.clients, "analizar_texto", AsyncMock(side_effect=logs_router.clients.ServicioNoDisponible("caído"))
    ), patch.object(
        logs_router.clients, "solicitar_recomendaciones", AsyncMock(return_value={"generadas": 1})
    ) as recomendar:
        await logs_router._procesar_analisis_en_segundo_plano(7, "texto", 3)

    assert analisis.estado_procesamiento == "error"
    recomendar.assert_awaited_once_with(3, 7)
    db.close.assert_called_once()


async def test_si_el_recommendation_service_falla_el_analisis_igual_queda_completado():
    db, analisis = _db_con_analisis()
    with patch.object(logs_router, "SessionLocal", return_value=db), patch.object(
        logs_router.clients, "analizar_texto", AsyncMock(return_value=("Neutro", 0.5, []))
    ), patch.object(
        logs_router.clients,
        "solicitar_recomendaciones",
        AsyncMock(side_effect=logs_router.clients.ServicioNoDisponible("caído")),
    ):
        await logs_router._procesar_analisis_en_segundo_plano(7, "", 3)

    assert analisis.estado_procesamiento == "completado"
