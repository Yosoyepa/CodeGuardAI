"""
Configuración base para los modelos ORM de SQLAlchemy.

Este módulo define la clase base declarativa de la cual deben heredar
todas las entidades de la base de datos para ser reconocidas por el ORM.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Clase base declarativa para todos los modelos ORM del sistema.

    Utiliza el estilo moderno de SQLAlchemy 2.0 (`DeclarativeBase`), lo que
    proporciona mejor soporte para tipado estático y autocompletado en IDEs
    comparado con la función antigua `declarative_base()`.

    Todas las entidades (ej. `CodeReviewEntity`) deben heredar de esta clase.

    __allow_unmapped__ = True permite usar anotaciones de tipo sin Mapped[]
    para mantener compatibilidad con el código existente.
    """

    __allow_unmapped__ = True
