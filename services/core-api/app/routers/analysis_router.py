from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import obtener_usuario_actual
from app.models.analisis_ia import AnalisisIA
from app.models.registro_emocional import RegistroEmocional
from app.models.usuario import Usuario
from app.schemas.analisis_schema import AnalisisIARespuesta

router = APIRouter(prefix="/api/analysis", tags=["Análisis de IA"])


@router.get("/{id_registro}", response_model=AnalisisIARespuesta)
def obtener_analisis(
    id_registro: int,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    """RF-03: consulta el estado/resultado del análisis de IA de un registro propio."""
    registro = (
        db.query(RegistroEmocional)
        .filter(
            RegistroEmocional.id_registro == id_registro,
            RegistroEmocional.id_usuario == usuario_actual.id_usuario,
        )
        .first()
    )
    if not registro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado")

    analisis = db.query(AnalisisIA).filter(AnalisisIA.id_registro == id_registro).first()
    if not analisis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aún no hay análisis para este registro")
    return analisis
