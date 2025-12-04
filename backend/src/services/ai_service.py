"""
AI Explainer Service

Servicio principal para generar explicaciones de seguridad usando IA generativa.
Integra el cliente de Vertex AI, enriquecimiento de contexto MCP y rate limiting.

Principios de diseño:
- SRP: Solo orquesta la generación de explicaciones
- Acoplamiento débil: Depende de interfaces (AIClient)
- Defensibilidad: Rate limiting y validación de entrada
- Async: Todas las operaciones son asíncronas
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from src.core.config.ai_config import get_ai_settings
from src.external.gemini_client import get_ai_client
from src.external.interfaces import (
    AIClient,
    AIClientError,
    AIRateLimitError,
)
from src.schemas.ai_explanation import AIExplanation, RateLimitInfo
from src.schemas.finding import Finding
from src.services.mcp_context_enricher import (
    EnrichedContext,
    MCPContextEnricher,
    get_mcp_context_enricher,
)

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Excepción cuando el usuario excede su límite de requests."""

    def __init__(self, message: str, rate_limit_info: RateLimitInfo):
        super().__init__(message)
        self.rate_limit_info = rate_limit_info


class AIExplanationError(Exception):
    """Error general en la generación de explicación."""

    pass


class InMemoryRateLimiter:
    """
    Rate limiter en memoria para controlar requests por usuario.

    Esta implementación es para desarrollo. En producción se puede
    reemplazar por un RateLimiter basado en Redis siguiendo el
    patrón Adapter.

    Attributes:
        limit_per_hour: Máximo de requests por hora
        user_requests: Diccionario de requests por usuario
    """

    def __init__(self, limit_per_hour: int = 10):
        """
        Inicializa el rate limiter.

        Args:
            limit_per_hour: Límite de requests por usuario por hora
        """
        self._limit_per_hour = limit_per_hour
        # user_id -> list of timestamps
        self._user_requests: Dict[str, list[datetime]] = defaultdict(list)

    def check_and_consume(self, user_id: str) -> RateLimitInfo:
        """
        Verifica si el usuario puede hacer un request y lo consume.

        Args:
            user_id: ID del usuario

        Returns:
            RateLimitInfo con el estado actual

        Raises:
            RateLimitExceeded: Si el usuario excede su límite
        """
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)

        # Limpiar requests antiguos
        self._user_requests[user_id] = [ts for ts in self._user_requests[user_id] if ts > hour_ago]

        # Calcular info de rate limit
        requests_used = len(self._user_requests[user_id])
        requests_remaining = max(0, self._limit_per_hour - requests_used)

        # Calcular cuando se resetea (1 hora desde el request más antiguo)
        if self._user_requests[user_id]:
            oldest = min(self._user_requests[user_id])
            reset_at = oldest + timedelta(hours=1)
        else:
            reset_at = now + timedelta(hours=1)

        rate_limit_info = RateLimitInfo(
            requests_remaining=requests_remaining - 1 if requests_remaining > 0 else 0,
            requests_limit=self._limit_per_hour,
            reset_at=reset_at,
        )

        # Verificar límite
        if requests_remaining <= 0:
            raise RateLimitExceeded(
                f"Rate limit exceeded. Limit: {self._limit_per_hour}/hour",
                rate_limit_info,
            )

        # Consumir request
        self._user_requests[user_id].append(now)
        return rate_limit_info

    def get_remaining(self, user_id: str) -> RateLimitInfo:
        """
        Obtiene el estado del rate limit sin consumir.

        Args:
            user_id: ID del usuario

        Returns:
            RateLimitInfo con el estado actual
        """
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)

        # Limpiar y contar
        self._user_requests[user_id] = [ts for ts in self._user_requests[user_id] if ts > hour_ago]
        requests_used = len(self._user_requests[user_id])
        requests_remaining = max(0, self._limit_per_hour - requests_used)

        if self._user_requests[user_id]:
            oldest = min(self._user_requests[user_id])
            reset_at = oldest + timedelta(hours=1)
        else:
            reset_at = now + timedelta(hours=1)

        return RateLimitInfo(
            requests_remaining=requests_remaining,
            requests_limit=self._limit_per_hour,
            reset_at=reset_at,
        )


class AIExplainerService:
    """
    Servicio para generar explicaciones de seguridad con IA.

    Orquesta el proceso completo:
    1. Verifica rate limit del usuario
    2. Enriquece el hallazgo con contexto OWASP
    3. Construye el prompt DevSecOps
    4. Llama al modelo de IA
    5. Parsea y retorna la explicación

    Principios:
        - SRP: Solo orquesta, delega a componentes especializados
        - Acoplamiento débil: Dependencias inyectadas
        - Defensibilidad: Valida entrada, maneja errores
        - Testeabilidad: Fácil de mockear dependencias

    Example:
        service = AIExplainerService()
        explanation = await service.explain_finding(
            finding=my_finding,
            code_context="full source code",
            user_id="user-123"
        )
    """

    # Prompt template DevSecOps
    PROMPT_TEMPLATE = """Eres un experto en DevSecOps y seguridad de aplicaciones.
Tu rol es explicar vulnerabilidades de seguridad a desarrolladores de forma clara,
educativa y accionable.

{context}

## Tu Tarea

Proporciona una explicación completa que incluya:

1. **Explicación del Problema**: Explica qué es esta vulnerabilidad, por qué es peligrosa
   y qué impacto podría tener en la aplicación (1-2 párrafos).

2. **Código Corregido**: Proporciona el código corregido que soluciona el problema.
   Incluye comentarios explicando los cambios.

3. **Ejemplo de Ataque**: Muestra un ejemplo concreto de cómo un atacante podría explotar
   esta vulnerabilidad (código o pasos).

4. **Referencias**: Lista referencias relevantes (OWASP, CWE, etc.).

## Formato de Respuesta

Responde en formato JSON con esta estructura:
```json
{{
    "explanation": "Explicación detallada del problema...",
    "suggested_fix": "Código corregido con comentarios...",
    "attack_example": "Ejemplo de cómo explotar la vulnerabilidad...",
    "references": ["OWASP A03:2021", "CWE-94"]
}}
```

IMPORTANTE:
- Responde SOLO con el JSON, sin texto adicional
- La explicación debe ser en español
- El código debe ser Python válido
- Sé específico sobre el contexto del código analizado
"""

    def __init__(
        self,
        ai_client: Optional[AIClient] = None,
        context_enricher: Optional[MCPContextEnricher] = None,
        rate_limiter: Optional[InMemoryRateLimiter] = None,
    ):
        """
        Inicializa el servicio con dependencias inyectadas.

        Args:
            ai_client: Cliente de IA (default: VertexAIClient)
            context_enricher: Enriquecedor de contexto (default: MCPContextEnricher)
            rate_limiter: Rate limiter (default: InMemoryRateLimiter)
        """
        settings = get_ai_settings()

        self._ai_client = ai_client or get_ai_client()
        self._context_enricher = context_enricher or get_mcp_context_enricher()
        self._rate_limiter = rate_limiter or InMemoryRateLimiter(
            limit_per_hour=settings.AI_RATE_LIMIT_PER_HOUR
        )

    async def explain_finding(
        self,
        finding: Finding,
        code_context: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> Tuple[AIExplanation, RateLimitInfo]:
        """
        Genera una explicación de IA para un hallazgo de seguridad.

        Args:
            finding: El hallazgo a explicar
            code_context: Código fuente completo para contexto (opcional)
            user_id: ID del usuario para rate limiting

        Returns:
            Tupla (AIExplanation, RateLimitInfo)

        Raises:
            RateLimitExceeded: Si el usuario excede su límite
            AIExplanationError: Si hay error en la generación
        """
        # 1. Verificar rate limit
        rate_limit_info = self._rate_limiter.check_and_consume(user_id)

        try:
            # 2. Enriquecer con contexto OWASP
            enriched = await self._context_enricher.enrich(finding)

            # 3. Construir prompt
            prompt = self._build_prompt(enriched, code_context)

            # 4. Llamar a IA
            logger.info(
                f"Generating AI explanation for finding: "
                f"rule_id={finding.rule_id}, user_id={user_id}"
            )

            response = await self._ai_client.generate_explanation(prompt)

            # 5. Parsear respuesta
            explanation = self._parse_response(
                response.content, response.model_name, response.tokens_used
            )

            logger.info(
                f"AI explanation generated successfully. " f"tokens_used={response.tokens_used}"
            )

            return explanation, rate_limit_info

        except AIRateLimitError as e:
            logger.warning(f"AI API rate limit hit: {e}")
            raise AIExplanationError(
                "El servicio de IA está temporalmente sobrecargado. "
                "Intenta de nuevo en unos minutos."
            ) from e

        except AIClientError as e:
            logger.error(f"AI client error: {e}")
            raise AIExplanationError(f"Error al comunicarse con el servicio de IA: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error generating explanation: {e}")
            raise AIExplanationError(f"Error inesperado generando explicación: {e}") from e

    def _build_prompt(self, enriched: EnrichedContext, code_context: Optional[str]) -> str:
        """
        Construye el prompt completo para el modelo de IA.

        Args:
            enriched: Contexto enriquecido con OWASP
            code_context: Código fuente adicional (opcional)

        Returns:
            Prompt formateado
        """
        context_parts = [enriched.formatted_prompt_context]

        # Agregar código fuente completo si está disponible
        if code_context:
            context_parts.append(f"## Código Fuente Completo\n```python\n{code_context}\n```")

        full_context = "\n\n".join(context_parts)
        return self.PROMPT_TEMPLATE.format(context=full_context)

    def _parse_response(self, content: str, model_name: str, tokens_used: int) -> AIExplanation:
        """
        Parsea la respuesta del modelo de IA.

        Args:
            content: Contenido de la respuesta
            model_name: Nombre del modelo usado
            tokens_used: Tokens consumidos

        Returns:
            AIExplanation parseada
        """
        import json

        # Intentar extraer JSON de la respuesta
        try:
            # La respuesta debería ser JSON puro
            # Pero a veces viene con markdown code blocks
            clean_content = content.strip()

            # Remover bloques de código markdown si existen
            if clean_content.startswith("```"):
                lines = clean_content.split("\n")
                # Remover primera y última línea (```json y ```)
                clean_content = "\n".join(lines[1:-1])

            data = json.loads(clean_content)

            return AIExplanation(
                explanation=data.get("explanation", "Sin explicación disponible"),
                suggested_fix=data.get("suggested_fix", "# Sin sugerencia disponible"),
                attack_example=data.get("attack_example"),
                references=data.get("references"),
                model_used=model_name,
                tokens_used=tokens_used,
            )

        except json.JSONDecodeError:
            # Si no es JSON válido, usar el contenido como explicación
            logger.warning("Could not parse AI response as JSON, using raw content")
            return AIExplanation(
                explanation=content,
                suggested_fix="# Ver explicación para sugerencias",
                attack_example=None,
                references=None,
                model_used=model_name,
                tokens_used=tokens_used,
            )

    def get_rate_limit_info(self, user_id: str) -> RateLimitInfo:
        """
        Obtiene el estado del rate limit para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            RateLimitInfo con el estado actual
        """
        return self._rate_limiter.get_remaining(user_id)

    @property
    def is_configured(self) -> bool:
        """Indica si el servicio está configurado correctamente."""
        return self._ai_client.is_configured


# Factory function para inyección de dependencias
_service_instance: Optional[AIExplainerService] = None


def get_ai_explainer_service() -> AIExplainerService:
    """
    Factory function para obtener el servicio de explicaciones.

    Usa singleton para reutilizar el rate limiter en memoria.

    Returns:
        Instancia de AIExplainerService
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = AIExplainerService()
    return _service_instance


def reset_ai_explainer_service() -> None:
    """
    Resetea el singleton (útil para testing).
    """
    global _service_instance
    _service_instance = None
