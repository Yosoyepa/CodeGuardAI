"""
Alembic Environment Configuration for CodeGuard AI.

Este archivo configura Alembic para detectar todos los modelos ORM
y generar migraciones automáticamente contra Supabase PostgreSQL.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ------------------------------------------------------------------------
# 1. Configuración de Rutas (Path)
# ------------------------------------------------------------------------
# Agregamos el directorio padre (backend/) al path de Python
# para que Alembic pueda encontrar la carpeta 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ------------------------------------------------------------------------
# 2. Importación de Modelos y Configuración
# ------------------------------------------------------------------------
# Importamos la Base declarativa y TODOS los modelos
# IMPORTANTE: Cada modelo debe ser importado para que Alembic lo detecte
from src.models import (
    Base,
    UserEntity,
    CodeReviewEntity,
    AgentFindingEntity,
    ReviewStatus,
    SeverityEnum,
    UserRole,
)

# Configuración de la base de datos
# Intentamos cargar desde settings, con fallback a variables de entorno
try:
    from src.core.config.settings import settings
    db_url = settings.DATABASE_URL
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise ValueError(
        "DATABASE_URL no está configurada. "
        "Configúrala en .env o en src/core/config/settings.py"
    )

# ------------------------------------------------------------------------
# 3. Configuración de Alembic
# ------------------------------------------------------------------------
config = context.config

# Interpretar el archivo de configuración para el logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Asignar la metadata de los modelos para que Alembic pueda "ver" las tablas
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Ejecuta migraciones en modo 'offline'.
    
    Configura el contexto con solo una URL, sin crear un Engine.
    Útil para generar scripts SQL sin conexión a la BD.
    """
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Comparar tipos para detectar cambios en columnas
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Ejecuta migraciones en modo 'online'.
    
    Crea un Engine y se conecta a la base de datos Supabase.
    """
    # Obtenemos la configuración de alembic.ini
    configuration = config.get_section(config.config_ini_section)
    
    # Inyectar la URL de la base de datos desde el entorno
    configuration["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Comparar tipos para detectar cambios en columnas
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()