"""
Esquemas para hallazgos encontrados en análisis
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, Optional, cast

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    """
    Niveles de severidad de un hallazgo.

    CRITICAL: Riesgo inmediato, debe corregirse
    HIGH: Importante, debe corregirse pronto
    MEDIUM: Moderado, se recomienda corrección
    LOW: Menor, mejora opcional
    INFO: Información, no es un problema
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(BaseModel):
    """
    Hallazgo encontrado durante el análisis de código.

    Attributes:
        severity: Nivel de severidad del hallazgo
        issue_type: Tipo de problema (ej: dangerous_function, sql_injection)
        message: Descripción del problema
        line_number: Número de línea donde se encontró (1-based)
        agent_name: Nombre del agente que detectó el hallazgo
        code_snippet: Fragmento de código problemático (opcional)
        suggestion: Sugerencia de cómo corregir (opcional)
        rule_id: ID de la regla que se violó (opcional)
        detected_at: Timestamp de detección

    Example:
        finding = Finding(
            severity=Severity.CRITICAL,
            issue_type="dangerous_function",
            message="Use of eval() detected",
            line_number=10,
            agent_name="SecurityAgent",
            code_snippet="result = eval(user_input)",
            suggestion="Use ast.literal_eval() instead",
            rule_id="SEC001_EVAL"
        )
    """

    severity: Severity = Field(..., description="Nivel de severidad")
    issue_type: str = Field(..., min_length=1, description="Tipo de problema")
    message: str = Field(..., min_length=5, description="Descripción del problema")
    line_number: int = Field(..., ge=1, description="Número de línea (1-based)")
    agent_name: str = Field(..., min_length=1, description="Nombre del agente")
    code_snippet: Optional[str] = Field(default=None, description="Fragmento de código")
    suggestion: Optional[str] = Field(default=None, description="Sugerencia de corrección")
    rule_id: Optional[str] = Field(default=None, description="ID de la regla")
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de detección"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "severity": "critical",
                "issue_type": "dangerous_function",
                "message": "Use of eval() detected",
                "line_number": 10,
                "agent_name": "SecurityAgent",
                "code_snippet": "result = eval(user_input)",
                "suggestion": "Use ast.literal_eval() instead",
                "rule_id": "SEC001_EVAL",
            }
        }
    )

    PENALTY_BY_SEVERITY: ClassVar[Dict[Severity, int]] = {
        Severity.CRITICAL: 10,
        Severity.HIGH: 5,
        Severity.MEDIUM: 2,
        Severity.LOW: 1,
        Severity.INFO: 0,
    }

    @property
    def is_critical(self) -> bool:
        """Retorna True si el hallazgo es crítico."""
        return self.severity == Severity.CRITICAL

    @property
    def is_high_or_critical(self) -> bool:
        """Retorna True si el hallazgo es HIGH o CRITICAL."""
        return self.severity in (Severity.CRITICAL, Severity.HIGH)

    @property
    def is_actionable(self) -> bool:
        """Retorna True si el hallazgo requiere acción (no INFO)."""
        return self.severity != Severity.INFO

    @classmethod
    def from_dict(cls, data: dict) -> "Finding":
        """
        Crea un Finding desde un diccionario.

        Args:
            data: Diccionario con datos del finding

        Returns:
            Instancia de Finding
        """
        detected_at_str = data.get("detected_at")
        detected_at = (
            datetime.fromisoformat(detected_at_str)
            if detected_at_str
            else datetime.now(timezone.utc)
        )
        return cls(
            severity=Severity(data["severity"]),
            issue_type=data["issue_type"],
            message=data["message"],
            line_number=data["line_number"],
            agent_name=data["agent_name"],
            code_snippet=data.get("code_snippet"),
            suggestion=data.get("suggestion"),
            rule_id=data.get("rule_id"),
            detected_at=detected_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el Finding a diccionario para persistencia.

        Returns:
            Diccionario con todos los campos del finding
        """
        severity_value = cast(Severity, self.severity).value
        detected_at_value = cast(datetime, self.detected_at)

        return {
            "severity": severity_value,
            "issue_type": self.issue_type,
            "message": self.message,
            "line_number": self.line_number,
            "agent_name": self.agent_name,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "rule_id": self.rule_id,
            "detected_at": detected_at_value.isoformat(),
        }

    def calculate_penalty(self) -> int:
        """
        Calcula el penalty para el quality score según severidad.

        Returns:
            Penalty points (CRITICAL=10, HIGH=5, MEDIUM=2, LOW=1, INFO=0)
        """
        return self.PENALTY_BY_SEVERITY.get(self.severity, 0)
