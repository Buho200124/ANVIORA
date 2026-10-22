import logging
from datetime import date, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.middleware.auth_middleware import obtener_usuario_actual
from app.models.analisis_ia import AnalisisIA
from app.models.registro_emocional import RegistroEmocional
from app.models.usuario import Usuario
from app.schemas.registro_schema import RegistroEmocionalCrear, RegistroEmocionalRespuesta
from app.services import clients

logger = logging.getLogger("anviora")

router = APIRouter(prefix="/api/logs", tags=["Registros Diarios"])


async def _procesar_analisis_en_segundo_plano(id_registro: int, descripcion_texto: str, id_usuario: int) -> None:
    """
    Tarea en segundo plano (RNF-01). En la versión con microservicios:
      1. llama al analysis-service (anonimiza + sentimiento) por HTTP y guarda el resultado,
      2. pide al recommendation-service evaluar las reglas de autocuidado.
    El paso 2 se intenta SIEMPRE, aunque el 1 falle: las reglas de estrés y sueño no dependen
    de la IA, y en el sistema original una falla del modelo tampoco bloqueaba las recomendaciones
    (degradaba a "Neutro"). Con servicios separados puede haber fallas de red, y no deben dejar al
    usuario sin su alerta de autocuidado (degradación segura).
    Abre su propia sesión de BD porque corre fuera del ciclo de la petición.
    """
    db = SessionLocal()
    try:
        analisis = db.query(AnalisisIA).filter(AnalisisIA.id_registro == id_registro).first()
        if analisis is None:
            return

        analisis.estado_procesamiento = "procesando"
        db.commit()

        try:
            polaridad, confianza, palabras_clave = await clients.analizar_texto(descripcion_texto or "")
            analisis.polaridad_sentimiento = polaridad
            analisis.puntuacion_confianza = confianza
            analisis.palabras_clave = palabras_clave
            analisis.estado_procesamiento = "completado"
            analisis.fecha_procesamiento = datetime.utcnow()
            db.commit()
        except Exception:
            logger.exception("Falló el análisis de IA del registro %s", id_registro)
            db.rollback()
            analisis = db.query(AnalisisIA).filter(AnalisisIA.id_registro == id_registro).first()
            if analisis:
                analisis.estado_procesamiento = "error"
                db.commit()

        try:
            await clients.solicitar_recomendaciones(id_usuario, id_registro)
        except Exception:
            # El análisis ya quedó guardado (o en "error"); solo se pierde la evaluación de este registro.
            logger.exception("No se pudieron generar recomendaciones para el registro %s", id_registro)
    finally:
        db.close()


@router.post("", response_model=RegistroEmocionalRespuesta, status_code=status.HTTP_201_CREATED)
def crear_registro(
    datos: RegistroEmocionalCrear,
    tareas_segundo_plano: BackgroundTasks,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    """RF-02: guarda el registro diario y programa el análisis de IA en segundo plano (RF-03)."""
    existente = (
        db.query(RegistroEmocional)
        .filter(
            RegistroEmocional.id_usuario == usuario_actual.id_usuario,
            RegistroEmocional.fecha_registro == date.today(),
        )
        .first()
    )
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un registro para el día de hoy")

    nuevo_registro = RegistroEmocional(
        id_usuario=usuario_actual.id_usuario,
        estado_animo=datos.estado_animo,
        horas_sueno=datos.horas_sueno,
        nivel_estres=datos.nivel_estres,
        etiquetas_actividades=datos.etiquetas_actividades,
        descripcion_texto=datos.descripcion_texto,
    )
    db.add(nuevo_registro)
    db.commit()
    db.refresh(nuevo_registro)

    analisis_pendiente = AnalisisIA(id_registro=nuevo_registro.id_registro, estado_procesamiento="pendiente")
    db.add(analisis_pendiente)
    db.commit()

    tareas_segundo_plano.add_task(
        _procesar_analisis_en_segundo_plano,
        nuevo_registro.id_registro,
        datos.descripcion_texto,
        usuario_actual.id_usuario,
    )

    return nuevo_registro


@router.get("", response_model=list[RegistroEmocionalRespuesta])
def listar_registros(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    """Lista los registros del usuario autenticado, del más reciente al más antiguo."""
    return (
        db.query(RegistroEmocional)
        .filter(RegistroEmocional.id_usuario == usuario_actual.id_usuario)
        .order_by(RegistroEmocional.fecha_registro.desc())
        .all()
    )
