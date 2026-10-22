import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_unitario.db")
os.environ.setdefault("JWT_SECRET_KEY", "clave-de-pruebas-no-usar-en-produccion")
os.environ.setdefault("INTERNAL_API_KEY", "clave-interna-de-pruebas")
