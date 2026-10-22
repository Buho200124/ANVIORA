"""
Pruebas unitarias del motor de recomendaciones (RF-04).

Validan que las reglas de negocio disparen (o no) las alertas esperadas
según el historial de registros y de análisis de IA. La sesión de BD se
reemplaza por un doble de prueba, así estas pruebas no requieren una
base de datos real: se centran en la lógica de las reglas, no en el
acceso a datos (ya verificado con PostgreSQL real en la integración).
"""
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.models.analisis_ia import AnalisisIA
from app.models.registro_emocional import RegistroEmocional
from app.services.recommendation_engine import evaluar_patrones_y_generar_recomendaciones


def _registro(id_registro, dias_atras, estres, horas_sueno):
    return RegistroEmocional(
        id_registro=id_registro,
        id_usuario=1,
        fecha_registro=date.today() - timedelta(days=dias_atras),
        estado_animo=3,
        horas_sueno=horas_sueno,
        nivel_estres=estres,
        etiquetas_actividades=[],
        descripcion_texto=None,
    )


def _db_simulada(ultimos_registros, analisis_por_registro=None):
    """
    Doble de prueba de la sesión de SQLAlchemy: responde distinto según
    el modelo consultado, igual que lo hace recommendation_engine.py.
    """
    analisis_por_registro = analisis_por_registro or {}
    db = MagicMock()

    query_registros = MagicMock()
    query_registros.filter.return_value.order_by.return_value.all.return_value = ultimos_registros

    query_analisis = MagicMock()
    secuencia = [analisis_por_registro.get(r.id_registro) for r in ultimos_registros]
    query_analisis.filter.return_value.first.side_effect = secuencia

    db.query.side_effect = lambda modelo: query_registros if modelo is RegistroEmocional else query_analisis
    return db


class TestReglaDeEstresYSueno:
    """Regla principal del RF-04: >=3 días continuos con estrés alto y <6h de sueño."""

    def test_tres_dias_de_estres_alto_y_poco_sueno_dispara_la_alerta(self):
        ultimos = [
            _registro(3, 0, estres=5, horas_sueno=4.5),
            _registro(2, 1, estres=4, horas_sueno=5.0),
            _registro(1, 2, estres=5, horas_sueno=5.5),
        ]
        db = _db_simulada(ultimos)

        recomendaciones = evaluar_patrones_y_generar_recomendaciones(db, id_usuario=1, registro_actual=ultimos[0])

        assert len(recomendaciones) == 1
        assert recomendaciones[0].tipo_recomendacion == "autocuidado"
        assert recomendaciones[0].nivel_prioridad == "alta"
        db.commit.assert_called_once()

    def test_solo_dos_dias_de_historial_no_alcanza_para_la_alerta(self):
        ultimos = [
            _registro(2, 0, estres=5, horas_sueno=4.5),
            _registro(1, 1, estres=5, horas_sueno=4.5),
        ]
        db = _db_simulada(ultimos)

        recomendaciones = evaluar_patrones_y_generar_recomendaciones(db, id_usuario=1, registro_actual=ultimos[0])

        assert len(recomendaciones) == 0

    def test_un_dia_con_sueno_suficiente_rompe_el_patron(self):
        ultimos = [
            _registro(3, 0, estres=5, horas_sueno=4.5),
            _registro(2, 1, estres=4, horas_sueno=7.5),  # rompe la racha de poco sueño
            _registro(1, 2, estres=5, horas_sueno=5.0),
        ]
        db = _db_simulada(ultimos)

        recomendaciones = evaluar_patrones_y_generar_recomendaciones(db, id_usuario=1, registro_actual=ultimos[0])

        assert len(recomendaciones) == 0


class TestReglaDeAnalisisDeIA:
    """Enriquecimiento con IA del RF-04: patrón sostenido de sentimiento negativo."""

    def test_tres_dias_de_analisis_negativo_dispara_la_alerta(self):
        ultimos = [
            _registro(3, 0, estres=2, horas_sueno=7.5),
            _registro(2, 1, estres=2, horas_sueno=7.5),
            _registro(1, 2, estres=2, horas_sueno=7.5),
        ]
        analisis = {
            id_reg: AnalisisIA(id_registro=id_reg, polaridad_sentimiento="Negativo", estado_procesamiento="completado")
            for id_reg in (1, 2, 3)
        }
        db = _db_simulada(ultimos, analisis)

        recomendaciones = evaluar_patrones_y_generar_recomendaciones(db, id_usuario=1, registro_actual=ultimos[0])

        assert "estado_de_animo" in [r.tipo_recomendacion for r in recomendaciones]

    def test_analisis_mixto_no_dispara_la_alerta_de_animo(self):
        ultimos = [
            _registro(3, 0, estres=2, horas_sueno=7.5),
            _registro(2, 1, estres=2, horas_sueno=7.5),
            _registro(1, 2, estres=2, horas_sueno=7.5),
        ]
        analisis = {
            3: AnalisisIA(id_registro=3, polaridad_sentimiento="Negativo", estado_procesamiento="completado"),
            2: AnalisisIA(id_registro=2, polaridad_sentimiento="Positivo", estado_procesamiento="completado"),
            1: AnalisisIA(id_registro=1, polaridad_sentimiento="Negativo", estado_procesamiento="completado"),
        }
        db = _db_simulada(ultimos, analisis)

        recomendaciones = evaluar_patrones_y_generar_recomendaciones(db, id_usuario=1, registro_actual=ultimos[0])

        assert "estado_de_animo" not in [r.tipo_recomendacion for r in recomendaciones]


class TestMensajeDeRefuerzoPositivo:
    """Cuando no hay alertas y el día fue bueno, se refuerza el buen hábito."""

    def test_buen_dia_sin_historial_previo_genera_un_mensaje_de_baja_prioridad(self):
        registro_hoy = _registro(1, 0, estres=2, horas_sueno=8.0)
        db = _db_simulada([registro_hoy])

        recomendaciones = evaluar_patrones_y_generar_recomendaciones(db, id_usuario=1, registro_actual=registro_hoy)

        assert len(recomendaciones) == 1
        assert recomendaciones[0].nivel_prioridad == "baja"

    def test_estres_moderado_no_genera_ninguna_recomendacion(self):
        registro_hoy = _registro(1, 0, estres=3, horas_sueno=6.5)
        db = _db_simulada([registro_hoy])

        recomendaciones = evaluar_patrones_y_generar_recomendaciones(db, id_usuario=1, registro_actual=registro_hoy)

        assert len(recomendaciones) == 0
