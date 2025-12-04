"""
Interfaz abstracta para clientes de IA generativa.

Define el contrato que deben implementar todos los proveedores de IA
(Google Vertex AI, OpenAI, Anthropic, etc.) siguiendo el patrón Adapter.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

# =============================================================================
# Excepciones personalizadas para clientes de IA
# =============================================================================


class AIClientError(Exception):
    """
    Error base para todos los problemas con clientes de IA.

    Attributes:
        message: Descripción del error
        original_error: Excepción original (si existe)
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class AIRateLimitError(AIClientError):
    """
    Error de límite de tasa de la API de IA.

    Se lanza cuando la API retorna un error 429 (Too Many Requests)
    o ResourceExhausted en el caso de Google Cloud.

    Attributes:
        retry_after: Segundos sugeridos de espera antes de reintentar
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[float] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.retry_after = retry_after


class AIConnectionError(AIClientError):
    """
    Error de conexión con el servicio de IA.

    Se lanza cuando no se puede establecer conexión con la API,
    hay timeout o problemas de red.
    """

    def __init__(
        self,
        message: str = "Failed to connect to AI service",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)


class AIModelError(AIClientError):
    """
    Error relacionado con el modelo de IA.

    Se lanza cuando el modelo no está disponible, el prompt excede
    los límites o hay problemas con la configuración del modelo.
    """

    def __init__(
        self,
        message: str = "AI model error",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)


class AIResponseError(AIClientError):
    """
    Error al procesar la respuesta de la IA.

    Se lanza cuando la respuesta no tiene el formato esperado
    o no se puede parsear correctamente.
    """

    def __init__(
        self,
        message: str = "Invalid AI response",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)


# =============================================================================
# Dataclass para respuesta estructurada
# =============================================================================


@dataclass
class AIResponse:
    """
    Respuesta estructurada de una llamada a la IA.

    Attributes:
        content: Texto generado por el modelo
        model_name: Nombre del modelo usado
        tokens_used: Tokens consumidos (input + output)
        finish_reason: Razón de finalización (stop, length, safety, etc.)
    """

    content: str
    model_name: str
    tokens_used: int = 0
    finish_reason: str = "stop"


# =============================================================================
# Interfaz abstracta (Adapter Pattern)
# =============================================================================


class AIClient(ABC):
    """
    Interfaz abstracta para clientes de IA generativa.

    Define el contrato que deben implementar todos los proveedores
    de IA, permitiendo cambiar entre diferentes servicios sin
    modificar el código del negocio.

    Example:
        ```python
        class VertexAIClient(AIClient):
            async def generate_explanation(self, prompt: str) -> AIResponse:
                # Implementación específica de Vertex AI
                ...

        # Uso
        client: AIClient = VertexAIClient()
        response = await client.generate_explanation("Explica este error...")
        print(response.content)
        ```
    """

    @abstractmethod
    async def generate_explanation(self, prompt: str) -> AIResponse:
        """
        Genera una explicación o respuesta basada en el prompt.

        Este es el método principal que deben implementar todos los
        proveedores de IA.

        Args:
            prompt: Texto del prompt a enviar al modelo

        Returns:
            AIResponse: Respuesta estructurada con el contenido generado

        Raises:
            AIRateLimitError: Si se excede el límite de tasa de la API
            AIConnectionError: Si hay problemas de conexión
            AIModelError: Si hay problemas con el modelo
            AIResponseError: Si la respuesta no es válida
            AIClientError: Para otros errores de la API
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verifica si el cliente de IA está operativo.

        Útil para health checks del sistema y monitoreo.

        Returns:
            bool: True si el servicio está disponible
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Retorna el nombre del modelo configurado.

        Returns:
            str: Identificador del modelo (ej: 'gemini-1.5-flash-001')
        """
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Verifica si el cliente tiene toda la configuración necesaria.

        Returns:
            bool: True si el cliente está correctamente configurado
        """
        pass
