"""
Cliente de Google Vertex AI para generación de explicaciones con Gemini.

Implementa el patrón Adapter para abstraer la comunicación con Vertex AI,
con soporte para exponential backoff en caso de rate limiting.

Requiere: pip install google-cloud-aiplatform>=1.40.0
"""

import asyncio
import logging
from typing import Optional

import vertexai
from google.api_core import exceptions as google_exceptions
from vertexai.generative_models import GenerationConfig, GenerativeModel

from src.core.config.ai_config import ai_settings
from src.external.interfaces.ai_client import (
    AIClient,
    AIClientError,
    AIConnectionError,
    AIModelError,
    AIRateLimitError,
    AIResponse,
    AIResponseError,
)

logger = logging.getLogger("agents.VertexAI")


class VertexAIClient(AIClient):
    """
    Cliente para Google Vertex AI (Gemini).

    Utiliza autenticación via Service Account configurada en
    GOOGLE_APPLICATION_CREDENTIALS. Implementa reintentos
    automáticos con exponential backoff para errores transitorios.

    Attributes:
        _model: Instancia del modelo generativo
        _initialized: Flag indicando si Vertex AI fue inicializado
    """

    def __init__(self):
        """
        Inicializa el cliente de Vertex AI.

        La inicialización real se hace de forma lazy en el primer uso
        para evitar errores si las credenciales no están configuradas.
        """
        self._model: Optional[GenerativeModel] = None
        self._initialized: bool = False
        self._generation_config: Optional[GenerationConfig] = None

    def _initialize(self) -> None:
        """
        Inicializa Vertex AI y carga el modelo.

        Se ejecuta de forma lazy en la primera llamada a generate_explanation.

        Raises:
            AIConnectionError: Si no se puede conectar a Vertex AI
            AIModelError: Si el modelo no está disponible
        """
        if self._initialized:
            return

        if not ai_settings.is_configured:
            raise AIClientError(
                "Vertex AI no está configurado. "
                "Verifica GCP_PROJECT_ID y GOOGLE_APPLICATION_CREDENTIALS en .env"
            )

        try:
            # Inicializar Vertex AI con proyecto y ubicación
            vertexai.init(
                project=ai_settings.GCP_PROJECT_ID,
                location=ai_settings.GCP_LOCATION,
            )

            # Cargar el modelo según el entorno (flash para dev, pro para prod)
            self._model = GenerativeModel(ai_settings.model_name)

            # Configuración de generación
            config_dict = ai_settings.get_generation_config()
            self._generation_config = GenerationConfig(**config_dict)

            self._initialized = True
            logger.info(
                f"[VertexAI] Inicializado con modelo {ai_settings.model_name} "
                f"en {ai_settings.GCP_LOCATION}"
            )

        except google_exceptions.PermissionDenied as e:
            raise AIConnectionError(
                "Permisos insuficientes. Verifica que la Service Account "
                "tenga el rol 'Vertex AI User'.",
                original_error=e,
            )
        except google_exceptions.NotFound as e:
            raise AIModelError(
                f"Modelo {ai_settings.model_name} no encontrado. "
                "Verifica el nombre del modelo y la región.",
                original_error=e,
            )
        except Exception as e:
            raise AIConnectionError(
                f"Error inicializando Vertex AI: {str(e)}",
                original_error=e,
            )

    def _parse_response(self, response) -> AIResponse:
        """
        Parsea y valida la respuesta del modelo.

        Args:
            response: Respuesta raw del modelo Vertex AI

        Returns:
            AIResponse: Respuesta estructurada

        Raises:
            AIResponseError: Si la respuesta es inválida o está vacía
        """
        if not response or not response.candidates:
            raise AIResponseError("Respuesta vacía del modelo")

        candidate = response.candidates[0]

        # Verificar si fue bloqueado por safety
        if candidate.finish_reason.name == "SAFETY":
            raise AIResponseError("Contenido bloqueado por filtros de seguridad de Google")

        # Extraer texto
        text = candidate.content.parts[0].text if candidate.content.parts else ""

        if not text:
            raise AIResponseError("No se generó texto en la respuesta")

        # Calcular tokens (aproximado si no está disponible)
        tokens_used = 0
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            tokens_used = getattr(usage, "prompt_token_count", 0) + getattr(
                usage, "candidates_token_count", 0
            )

        logger.info(
            f"[VertexAI] Generación exitosa - "
            f"Tokens: {tokens_used}, "
            f"Finish: {candidate.finish_reason.name}"
        )

        return AIResponse(
            content=text,
            model_name=ai_settings.model_name,
            tokens_used=tokens_used,
            finish_reason=candidate.finish_reason.name,
        )

    async def _handle_retryable_error(
        self, error: Exception, attempt: int, max_retries: int, backoff: float, error_type: str
    ) -> float:
        """
        Maneja errores que permiten reintento con backoff.

        Args:
            error: Excepción capturada
            attempt: Intento actual (0-based)
            max_retries: Máximo de reintentos permitidos
            backoff: Tiempo de espera actual
            error_type: Tipo de error para logging

        Returns:
            float: Nuevo valor de backoff

        Raises:
            AIRateLimitError: Si se agotan reintentos por rate limit
            AIConnectionError: Si se agotan reintentos por servicio no disponible
        """
        if attempt < max_retries:
            logger.warning(
                f"[VertexAI] {error_type}. " f"Reintento {attempt + 1}/{max_retries} en {backoff}s"
            )
            await asyncio.sleep(backoff)
            return backoff * ai_settings.AI_BACKOFF_FACTOR

        # Se agotaron los reintentos
        if error_type == "Rate limit alcanzado":
            raise AIRateLimitError(
                "Límite de tasa excedido después de múltiples reintentos",
                retry_after=backoff,
                original_error=error,
            )
        else:
            raise AIConnectionError(
                "Servicio de Vertex AI no disponible",
                original_error=error,
            )

    async def generate_explanation(self, prompt: str) -> AIResponse:
        """
        Genera una explicación usando Gemini con reintentos automáticos.

        Implementa exponential backoff para manejar rate limits (429)
        y errores transitorios de la API.

        Args:
            prompt: Texto del prompt a enviar al modelo

        Returns:
            AIResponse: Respuesta estructurada con contenido y metadata

        Raises:
            AIRateLimitError: Si se agotan los reintentos por rate limiting
            AIConnectionError: Si hay problemas de conexión
            AIClientError: Para otros errores
        """
        # Inicialización lazy
        self._initialize()

        if not self._model:
            raise AIClientError("Modelo no inicializado")

        # Configuración de reintentos
        max_retries = ai_settings.AI_MAX_RETRIES
        backoff = ai_settings.AI_INITIAL_BACKOFF
        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                # Ejecutar generación en thread pool (Vertex AI SDK es síncrono)
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._model.generate_content(
                        prompt,
                        generation_config=self._generation_config,
                    ),
                )
                return self._parse_response(response)

            except google_exceptions.ResourceExhausted as e:
                last_error = e
                backoff = await self._handle_retryable_error(
                    e, attempt, max_retries, backoff, "Rate limit alcanzado"
                )

            except google_exceptions.ServiceUnavailable as e:
                last_error = e
                backoff = await self._handle_retryable_error(
                    e, attempt, max_retries, backoff, "Servicio no disponible"
                )

            except google_exceptions.InvalidArgument as e:
                raise AIModelError(f"Prompt inválido: {str(e)}", original_error=e)

            except AIResponseError:
                raise

            except Exception as e:
                logger.error(f"[VertexAI] Error inesperado: {str(e)}")
                raise AIClientError(f"Error generando contenido: {str(e)}", original_error=e)

        raise AIClientError("Error después de múltiples reintentos", original_error=last_error)

    async def health_check(self) -> bool:
        """
        Verifica si el cliente de Vertex AI está operativo.

        Intenta inicializar el cliente y verificar que el modelo esté disponible.

        Returns:
            bool: True si el servicio está disponible
        """
        try:
            self._initialize()
            return self._initialized and self._model is not None
        except Exception as e:
            logger.warning(f"[VertexAI] Health check fallido: {str(e)}")
            return False

    @property
    def model_name(self) -> str:
        """Retorna el nombre del modelo configurado."""
        return ai_settings.model_name

    @property
    def is_configured(self) -> bool:
        """Verifica si el cliente está correctamente configurado."""
        return ai_settings.is_configured


# Singleton del cliente (opcional, para inyección de dependencias)
def get_ai_client() -> AIClient:
    """
    Factory function para obtener el cliente de IA.

    Permite cambiar fácilmente la implementación (mock para tests).

    Returns:
        AIClient: Instancia del cliente de IA configurado

    Raises:
        AIClientError: Si la IA está deshabilitada o no hay biblioteca instalada
    """
    if not ai_settings.AI_ENABLED:
        raise AIClientError("Funcionalidad de IA deshabilitada (AI_ENABLED=false)")

    return VertexAIClient()
