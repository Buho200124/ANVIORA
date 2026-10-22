from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Provee una sesión de BD por petición y la cierra al finalizar (dependencia de FastAPI)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
