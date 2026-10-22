from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.registro_emocional import RegistroEmocional
from app.services.recommendation_engine import evaluar_patrones_y_generar_recomendaciones
from app.utils.internal_auth import verificar_clave_interna

router = APIRouter(prefix="/internal", tags=["Interno"], dependencies=[Depends(verificar_clave_interna)])


class SolicitudEvaluacion(BaseModel):
    id_usuario: int
    id_registro: int


@router.post("/evaluate")
def evaluar_registro(datos: SolicitudEvaluacion, db: Session = Depends(get_db)):
    """
    Lo llama el core-api cuando termina el análisis de IA de un registro: evalúa las reglas
    (>= 3 días de estrés alto y poco sueño, tono negativo sostenido) y guarda las recomendaciones.
    """
    registro = (
        db.query(RegistroEmocional)
        .filter(
            RegistroEmocional.id_registro == datos.id_registro,
            RegistroEmocional.id_usuario == datos.id_usuario,
        )
        .first()
    )
    if registro is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")

    nuevas = evaluar_patrones_y_generar_recomendaciones(db, datos.id_usuario, registro)
    return {"generadas": len(nuevas)}
