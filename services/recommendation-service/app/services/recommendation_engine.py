from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models.analisis_ia import AnalisisIA
from app.models.recomendacion import Recomendacion
from app.models.registro_emocional import RegistroEmocional

UMBRAL_DIAS_CONSECUTIVOS = 3
UMBRAL_ESTRES_ALTO = 4
UMBRAL_HORAS_SUENO_BAJO = 6


def _obtener_ultimos_registros(db: Session, id_usuario: int, dias: int) -> List[RegistroEmocional]:
    desde = date.today() - timedelta(days=dias - 1)
    return (
        db.query(RegistroEmocional)
        .filter(RegistroEmocional.id_usuario == id_usuario, RegistroEmocional.fecha_registro >= desde)
        .order_by(RegistroEmocional.fecha_registro.desc())
        .all()
    )


def evaluar_patrones_y_generar_recomendaciones(
    db: Session, id_usuario: int, registro_actual: RegistroEmocional
) -> List[Recomendacion]:
    """
    Motor de reglas combinado con el enriquecimiento de IA (RF-04). Regla principal:
    >= 3 días continuos con estrés alto y < 6 horas de sueño activan una alerta
    de autocuidado; un patrón de análisis de IA negativo sostenido suma otra alerta.
    """
    nuevas_recomendaciones: List[Recomendacion] = []
    ultimos = _obtener_ultimos_registros(db, id_usuario, UMBRAL_DIAS_CONSECUTIVOS)

    cumple_patron_estres_sueno = (
        len(ultimos) >= UMBRAL_DIAS_CONSECUTIVOS
        and all(r.nivel_estres >= UMBRAL_ESTRES_ALTO for r in ultimos)
        and all(float(r.horas_sueno) < UMBRAL_HORAS_SUENO_BAJO for r in ultimos)
    )
    if cumple_patron_estres_sueno:
        nuevas_recomendaciones.append(
            Recomendacion(
                id_usuario=id_usuario,
                id_registro=registro_actual.id_registro,
                tipo_recomendacion="autocuidado",
                contenido_recomendacion=(
                    "Llevas varios días con estrés alto y poco descanso. Considera "
                    "priorizar el sueño esta noche y tomar pausas activas durante el día."
                ),
                nivel_prioridad="alta",
            )
        )

    analisis_recientes = [
        db.query(AnalisisIA).filter(AnalisisIA.id_registro == r.id_registro).first() for r in ultimos
    ]
    analisis_recientes = [a for a in analisis_recientes if a is not None]
    if len(analisis_recientes) >= UMBRAL_DIAS_CONSECUTIVOS and all(
        a.polaridad_sentimiento == "Negativo" for a in analisis_recientes
    ):
        nuevas_recomendaciones.append(
            Recomendacion(
                id_usuario=id_usuario,
                id_registro=registro_actual.id_registro,
                tipo_recomendacion="estado_de_animo",
                contenido_recomendacion=(
                    "Tu descripción del día ha reflejado un tono negativo varias veces "
                    "seguidas. Hablar con alguien de confianza o un profesional puede ayudarte."
                ),
                nivel_prioridad="alta",
            )
        )

    if not nuevas_recomendaciones and registro_actual.nivel_estres <= 2 and float(registro_actual.horas_sueno) >= 7:
        nuevas_recomendaciones.append(
            Recomendacion(
                id_usuario=id_usuario,
                id_registro=registro_actual.id_registro,
                tipo_recomendacion="autocuidado",
                contenido_recomendacion="¡Vas muy bien! Mantén tu rutina de sueño y sigue registrando cómo te sientes.",
                nivel_prioridad="baja",
            )
        )

    for recomendacion in nuevas_recomendaciones:
        db.add(recomendacion)
    if nuevas_recomendaciones:
        db.commit()

    return nuevas_recomendaciones
