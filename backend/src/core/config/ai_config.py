"""
Configuración de Inteligencia Artificial para CodeGuard AI.

Gestiona la configuración de Vertex AI (Gemini), incluyendo:
- Selección dinámica de modelo por entorno (dev/prod)
- Rate limiting por usuario
- Configuración de reintentos con exponential backoff
"""

from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """
    Configuración de IA cargada desde variables de entorno.

    Usa Google Cloud Vertex AI con autenticación via Service Account.
    La variable GOOGLE_APPLICATION_CREDENTIALS debe apuntar al archivo JSON.

    Attributes:
        GCP_PROJECT_ID: ID del proyecto en Google Cloud Platform
        GCP_LOCATION: Región de Vertex AI (us-central1 recomendado)
        GOOGLE_APPLICATION_CREDENTIALS: Ruta al archivo JSON de Service Account
        AI_ENABLED: Habilitar/deshabilitar funcionalidad de IA
        AI_MODEL_DEV: Modelo para desarrollo (flash = rápido/económico)
        AI_MODEL_PROD: Modelo para producción (pro = mejor razonamiento)
        AI_TEMPERATURE: Temperatura del modelo (0.0-1.0, menor = más determinista)
        AI_MAX_OUTPUT_TOKENS: Límite de tokens en respuesta
        AI_RATE_LIMIT_PER_HOUR: Límite de llamadas por usuario por hora
        AI_MAX_RETRIES: Intentos máximos ante errores transitorios
        AI_BACKOFF_FACTOR: Factor de espera exponencial entre reintentos
    """

    # Google Cloud Platform
    GCP_PROJECT_ID: Optional[str] = Field(
        default=None,
        description="ID del proyecto en Google Cloud Platform",
    )
    GCP_LOCATION: str = Field(
        default="us-central1",
        description="Región de Vertex AI",
    )
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(
        default=None,
        description="Ruta al archivo JSON de Service Account",
    )

    # Feature Flag
    AI_ENABLED: bool = Field(
        default=True,
        description="Habilitar funcionalidad de IA",
    )

    # Model Selection (por entorno)
    AI_MODEL_DEV: str = Field(
        default="gemini-1.5-flash-001",
        description="Modelo para desarrollo (optimizado velocidad/costo)",
    )
    AI_MODEL_PROD: str = Field(
        default="gemini-1.5-pro-001",
        description="Modelo para producción (optimizado razonamiento)",
    )

    # Model Parameters
    AI_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperatura del modelo (0.0-1.0)",
    )
    AI_MAX_OUTPUT_TOKENS: int = Field(
        default=2048,
        ge=100,
        le=8192,
        description="Límite de tokens en respuesta",
    )

    # Rate Limiting (para controlar costos)
    AI_RATE_LIMIT_PER_HOUR: int = Field(
        default=10,
        ge=1,
        description="Límite de llamadas por usuario por hora",
    )

    # Retry Configuration (exponential backoff)
    AI_MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Intentos máximos ante errores transitorios",
    )
    AI_BACKOFF_FACTOR: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Factor de espera exponencial (segundos)",
    )
    AI_INITIAL_BACKOFF: float = Field(
        default=1.0,
        ge=0.5,
        le=10.0,
        description="Espera inicial antes del primer reintento (segundos)",
    )

    # Environment (heredado de settings principal)
    ENVIRONMENT: str = Field(
        default="development",
        description="Entorno de ejecución",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def model_name(self) -> str:
        """
        Selecciona el modelo de Gemini según el entorno.

        Returns:
            str: Nombre del modelo (flash para dev, pro para prod)
        """
        if self.ENVIRONMENT == "production":
            return self.AI_MODEL_PROD
        return self.AI_MODEL_DEV

    @computed_field
    @property
    def is_configured(self) -> bool:
        """
        Verifica si la configuración de IA está completa.

        Returns:
            bool: True si GCP_PROJECT_ID y credenciales están configurados
        """
        return bool(self.AI_ENABLED and self.GCP_PROJECT_ID and self.GOOGLE_APPLICATION_CREDENTIALS)

    def get_generation_config(self) -> dict:
        """
        Retorna la configuración de generación para Vertex AI.

        Returns:
            dict: Parámetros de generación del modelo
        """
        return {
            "temperature": self.AI_TEMPERATURE,
            "max_output_tokens": self.AI_MAX_OUTPUT_TOKENS,
            "top_p": 0.95,
            "top_k": 40,
        }


# Singleton de configuración de IA
ai_settings = AISettings()


def get_ai_settings() -> AISettings:
    """
    Factory function para obtener la configuración de IA.

    Returns:
        Instancia singleton de AISettings
    """
    return ai_settings
