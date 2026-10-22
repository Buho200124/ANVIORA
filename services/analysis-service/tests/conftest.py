import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("INTERNAL_API_KEY", "clave-interna-de-pruebas")
os.environ.setdefault("PRECARGAR_MODELO", "false")
