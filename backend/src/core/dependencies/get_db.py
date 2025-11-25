"""
Dependencia para obtener sesión de base de datos.
"""

from typing import Generator

from sqlalchemy.orm import Session

from src.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Crea una sesión de base de datos por request y la cierra al finalizar.

    Yields:
        Session: Sesión de SQLAlchemy para operaciones de base de datos.

    Example:
        @router.post("/items")
        def create_item(db: Session = Depends(get_db)):
            # usar db aquí
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
