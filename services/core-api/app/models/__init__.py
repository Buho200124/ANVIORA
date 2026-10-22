"""
Importa todos los modelos para que SQLAlchemy resuelva las relaciones entre ellos
(Usuario <-> RegistroEmocional <-> AnalisisIA <-> Recomendacion), aunque un servicio
solo use directamente algunos.
"""
from app.models.analisis_ia import AnalisisIA  # noqa: F401
from app.models.recomendacion import Recomendacion  # noqa: F401
from app.models.registro_emocional import RegistroEmocional  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
