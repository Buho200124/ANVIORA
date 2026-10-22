from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import obtener_usuario_actual
from app.models.registro_emocional import RegistroEmocional
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def obtener_estadisticas(
    periodo: Literal["semanal", "mensual"] = Query("semanal", description="Rango de consulta"),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    """RF-05: series de ánimo, sueño y estrés para las gráficas del dashboard, por rango semanal o mensual."""
    dias = 7 if periodo == "semanal" else 30
    desde = date.today() - timedelta(days=dias - 1)

    registros = (
        db.query(RegistroEmocional)
        .filter(RegistroEmocional.id_usuario == usuario_actual.id_usuario, RegistroEmocional.fecha_registro >= desde)
        .order_by(RegistroEmocional.fecha_registro.asc())
        .all()
    )

    return {
        "periodo": periodo,
        "fechas": [r.fecha_registro.isoformat() for r in registros],
        "estado_animo": [r.estado_animo for r in registros],
        "horas_sueno": [float(r.horas_sueno) for r in registros],
        "nivel_estres": [r.nivel_estres for r in registros],
    }
