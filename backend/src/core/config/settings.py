"""
Configuración centralizada para CodeGuard AI.

Carga variables de entorno usando pydantic-settings.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración de la aplicación cargada desde variables de entorno.

    Attributes:
        CLERK_SECRET_KEY: Clave secreta de Clerk para validar JWT
        CLERK_PUBLISHABLE_KEY: Clave pública de Clerk
        DATABASE_URL: URL de conexión a PostgreSQL/Supabase
        ENVIRONMENT: Entorno de ejecución (development/production)
        DEBUG: Modo debug
    """

    # Clerk Authentication
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str

    # Database
    DATABASE_URL: str

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "CodeGuard AI"
    APP_VERSION: str = "1.0.0"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Redis (opcional para Sprint 2)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Retorna lista de orígenes permitidos para CORS."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Singleton de configuración
settings = Settings()
