from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import obtener_usuario_actual
from app.models.recomendacion import Recomendacion
from app.models.usuario import Usuario
from app.schemas.recomendacion_schema import RecomendacionRespuesta

router = APIRouter(prefix="/api/recommendations", tags=["Recomendaciones"])


@router.get("", response_model=list[RecomendacionRespuesta])
def listar_recomendaciones(
    solo_no_vistas: bool = Query(False, description="Filtrar solo recomendaciones no vistas"),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    """RF-04: lista las recomendaciones de autocuidado del usuario autenticado."""
    consulta = db.query(Recomendacion).filter(Recomendacion.id_usuario == usuario_actual.id_usuario)
    if solo_no_vistas:
        consulta = consulta.filter(Recomendacion.vista.is_(False))
    return consulta.order_by(Recomendacion.fecha_generacion.desc()).all()


@router.patch("/{id_recomendacion}/marcar-vista", response_model=RecomendacionRespuesta)
def marcar_como_vista(
    id_recomendacion: int,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    """Marca una recomendación como vista por el usuario."""
    recomendacion = (
        db.query(Recomendacion)
        .filter(
            Recomendacion.id_recomendacion == id_recomendacion,
            Recomendacion.id_usuario == usuario_actual.id_usuario,
        )
        .first()
    )
    if not recomendacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recomendación no encontrada")
    recomendacion.vista = True
    db.commit()
    db.refresh(recomendacion)
    return recomendacion
