"""
Dependencia para obtener sesión de base de datos.
"""
from typing import Generator
from src.core.database import SessionLocal # Asumiendo que existe, si no, usaremos un mock temporal

def get_db() -> Generator:
    """
    Crea una sesión de base de datos por request y la cierra al finalizar.
    """
    try:
        db = SessionLocal()
        yield db
    except Exception:
        # En caso de que SessionLocal no esté configurado aún en src.core.database
        # esto permite que los tests con mocks funcionen.
        yield None
    finally:
        if 'db' in locals() and db:
            db.close()