"""
Esquemas para explicaciones generadas por IA.

Define las estructuras de datos para las explicaciones de seguridad
generadas por modelos de IA generativa (Gemini/Vertex AI).

Principios de diseño:
- Inmutabilidad: Los esquemas son de solo lectura
- Validación: Pydantic valida todos los campos
- Serialización: Compatible con JSON para almacenamiento en JSONB
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AIExplanationRequest(BaseModel):
    """
    Request para solicitar una explicación de IA.

    Attributes:
        include_attack_example: Si se debe incluir ejemplo de ataque
        include_references: Si se deben incluir referencias
        language: Idioma de la explicación (es/en)
    """

    include_attack_example: bool = Field(
        default=True, description="Incluir ejemplo de ataque potencial"
    )
    include_references: bool = Field(default=True, description="Incluir referencias OWASP/CWE")
    language: str = Field(default="es", description="Idioma de la explicación")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "include_attack_example": True,
                "include_references": True,
                "language": "es",
            }
        }
    )


class AIExplanation(BaseModel):
    """
    Explicación generada por IA para un hallazgo de seguridad.

    Esta estructura se almacena en el campo JSONB 'ai_explanation'
    de AgentFindingEntity para cache persistente.

    Attributes:
        explanation: Explicación detallada del problema de seguridad
        suggested_fix: Código sugerido para corregir el problema
        attack_example: Ejemplo de cómo podría explotarse (opcional)
        references: Lista de referencias OWASP, CWE, etc. (opcional)
        model_used: Nombre del modelo que generó la explicación
        tokens_used: Número de tokens consumidos
        generated_at: Timestamp de generación

    Example:
        explanation = AIExplanation(
            explanation="El uso de eval() permite ejecución de código...",
            suggested_fix="import ast\\nresult = ast.literal_eval(user_input)",
            attack_example="user_input = '__import__(\"os\").system(\"rm -rf /\")'",
            references=["OWASP A03:2021", "CWE-94"],
            model_used="gemini-1.5-flash-001",
            tokens_used=450
        )
    """

    explanation: str = Field(..., min_length=10, description="Explicación detallada del problema")
    suggested_fix: str = Field(..., min_length=5, description="Código sugerido para corregir")
    attack_example: Optional[str] = Field(
        default=None, description="Ejemplo de explotación potencial"
    )
    references: Optional[List[str]] = Field(
        default=None, description="Referencias OWASP, CWE, etc."
    )
    model_used: str = Field(..., description="Modelo de IA usado")
    tokens_used: int = Field(..., ge=0, description="Tokens consumidos")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp de generación",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "explanation": (
                    "El uso de eval() en Python es extremadamente peligroso porque "
                    "permite la ejecución arbitraria de código. Un atacante podría "
                    "inyectar código malicioso que se ejecutaría con los privilegios "
                    "del proceso actual."
                ),
                "suggested_fix": (
                    "import ast\n\n"
                    "# Usar literal_eval para evaluar literales de forma segura\n"
                    "result = ast.literal_eval(user_input)"
                ),
                "attack_example": (
                    "# Un atacante podría enviar:\n"
                    'user_input = \'__import__("os").system("cat /etc/passwd")\''
                ),
                "references": ["OWASP A03:2021 - Injection", "CWE-94: Code Injection"],
                "model_used": "gemini-1.5-flash-001",
                "tokens_used": 450,
                "generated_at": "2024-01-15T10:30:00Z",
            }
        }
    )

    def to_dict(self) -> dict:
        """
        Convierte a diccionario para almacenamiento en JSONB.

        Returns:
            Diccionario serializable
        """
        return {
            "explanation": self.explanation,
            "suggested_fix": self.suggested_fix,
            "attack_example": self.attack_example,
            "references": self.references,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "generated_at": self.generated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AIExplanation":
        """
        Crea instancia desde diccionario (recuperado de JSONB).

        Args:
            data: Diccionario con datos de la explicación

        Returns:
            Instancia de AIExplanation
        """
        # Convertir string ISO a datetime si es necesario
        generated_at = data.get("generated_at")
        if isinstance(generated_at, str):
            data["generated_at"] = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))

        return cls(**data)


class AIExplanationResponse(BaseModel):
    """
    Response con la explicación de IA para el endpoint.

    Attributes:
        finding_id: ID del hallazgo explicado
        explanation: La explicación generada
        cached: Si la explicación viene de cache
    """

    finding_id: int = Field(..., description="ID del hallazgo")
    explanation: AIExplanation = Field(..., description="Explicación generada")
    cached: bool = Field(..., description="Si viene de cache")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "finding_id": 123,
                "explanation": {
                    "explanation": "El uso de eval() es peligroso...",
                    "suggested_fix": "Usar ast.literal_eval()",
                    "attack_example": "user_input = '__import__(\"os\")...'",
                    "references": ["OWASP A03:2021"],
                    "model_used": "gemini-1.5-flash-001",
                    "tokens_used": 450,
                    "generated_at": "2024-01-15T10:30:00Z",
                },
                "cached": False,
            }
        }
    )


class RateLimitInfo(BaseModel):
    """
    Información sobre el rate limit del usuario.

    Attributes:
        requests_remaining: Requests restantes en el período
        requests_limit: Límite total de requests
        reset_at: Cuando se resetea el contador
    """

    requests_remaining: int = Field(..., ge=0, description="Requests restantes")
    requests_limit: int = Field(..., ge=0, description="Límite total")
    reset_at: datetime = Field(..., description="Hora de reset")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "requests_remaining": 8,
                "requests_limit": 10,
                "reset_at": "2024-01-15T11:00:00Z",
            }
        }
    )


class AIExplanationError(BaseModel):
    """
    Error en la generación de explicación.

    Attributes:
        error_type: Tipo de error (rate_limit, ai_error, not_found)
        message: Mensaje descriptivo
        rate_limit_info: Info de rate limit si aplica
    """

    error_type: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje de error")
    rate_limit_info: Optional[RateLimitInfo] = Field(default=None, description="Info de rate limit")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_type": "rate_limit",
                "message": "Has excedido el límite de explicaciones por hora",
                "rate_limit_info": {
                    "requests_remaining": 0,
                    "requests_limit": 10,
                    "reset_at": "2024-01-15T11:00:00Z",
                },
            }
        }
    )
