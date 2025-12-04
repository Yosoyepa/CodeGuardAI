"""
Configuración centralizada para CodeGuard AI.

Carga variables de entorno usando pydantic-settings.
"""

from typing import Optional

from pydantic import Field
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
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_PUBLISHABLE_KEY: str
    CLERK_JWKS_URL: Optional[str] = Field(
        default=None, description="URL del endpoint JWKS de Clerk para validar tokens RS256"
    )
    CLERK_JWT_SIGNING_KEY: Optional[str] = Field(
        default=None, description="Signing Key para validar Custom JWT Templates (HS256)"
    )

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

    # Redis (opcional)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None

    # ==========================================
    # AI Services - Vertex AI (Sprint 3)
    # ==========================================

    # Google Cloud Platform
    GCP_PROJECT_ID: Optional[str] = Field(default=None)
    GCP_LOCATION: str = Field(default="us-central1")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(default=None)

    # Feature Flag
    AI_ENABLED: bool = Field(default=True)

    # Model Selection
    AI_MODEL_DEV: str = Field(default="gemini-1.5-flash-001")
    AI_MODEL_PROD: str = Field(default="gemini-1.5-pro-001")

    # Model Parameters
    AI_TEMPERATURE: float = Field(default=0.3, ge=0.0, le=1.0)
    AI_MAX_OUTPUT_TOKENS: int = Field(default=2048, ge=100, le=8192)

    # Rate Limiting
    AI_RATE_LIMIT_PER_HOUR: int = Field(default=10, ge=1)

    # Retry Configuration
    AI_MAX_RETRIES: int = Field(default=3, ge=1, le=10)
    AI_BACKOFF_FACTOR: float = Field(default=2.0, ge=1.0, le=5.0)
    AI_INITIAL_BACKOFF: float = Field(default=1.0, ge=0.5, le=10.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Retorna lista de orígenes permitidos para CORS."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def ai_model_name(self) -> str:
        """Selecciona el modelo según el entorno."""
        if self.ENVIRONMENT == "production":
            return self.AI_MODEL_PROD
        return self.AI_MODEL_DEV

    @property
    def is_ai_configured(self) -> bool:
        """Verifica si la IA está configurada correctamente."""
        return bool(self.AI_ENABLED and self.GCP_PROJECT_ID and self.GOOGLE_APPLICATION_CREDENTIALS)


# Singleton de configuración
settings = Settings()
