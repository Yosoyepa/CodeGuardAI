"""
Entidad ORM para hallazgos de agentes.
Alineado con tabla 'agent_findings' en PostgreSQL (Supabase).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from src.models.base import Base
from src.models.enums.severity_enum import SeverityEnum

if TYPE_CHECKING:
    from src.models.code_review import CodeReviewEntity


class AgentFindingEntity(Base):
    """
    Entidad ORM que representa la tabla 'agent_findings' en la base de datos.

    Attributes:
        id: UUID del hallazgo
        review_id: FK a code_reviews
        agent_type: Nombre del agente (SecurityAgent, QualityAgent, etc.)
        severity: CRITICAL, HIGH, MEDIUM, LOW
        issue_type: Tipo de problema (dangerous_function, sql_injection, etc.)
        line_number: Número de línea donde se encontró
        code_snippet: Fragmento de código problemático
        message: Descripción del problema
        suggestion: Sugerencia de corrección
        metrics: Métricas adicionales (JSONB)
        ai_explanation: Explicación generada por IA - Sprint 3 (JSONB)
        mcp_references: Referencias a servidores MCP - Sprint 3 (TEXT[])
        created_at: Timestamp de creación
    """

    __tablename__ = "agent_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_type = Column(String(100), nullable=False, index=True)
    severity = Column(Enum(SeverityEnum), nullable=False, index=True)
    issue_type = Column(String(200), nullable=False)
    line_number = Column(Integer, nullable=False)
    code_snippet = Column(Text, nullable=True)
    message = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)

    # Campos adicionales
    metrics = Column(JSONB, nullable=True)

    # Sprint 3: IA y MCP
    ai_explanation = Column(JSONB, nullable=True)
    mcp_references = Column(ARRAY(Text), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    code_review: "CodeReviewEntity" = relationship("CodeReviewEntity", back_populates="findings")

    def __repr__(self) -> str:
        return (
            f"<AgentFindingEntity("
            f"id={self.id}, "
            f"agent={self.agent_type}, "
            f"severity={self.severity}, "
            f"line={self.line_number}"
            f")>"
        )

    @property
    def penalty(self) -> int:
        """Retorna la penalización para el quality score según severidad."""
        penalties = {
            SeverityEnum.CRITICAL: 10,
            SeverityEnum.HIGH: 5,
            SeverityEnum.MEDIUM: 2,
            SeverityEnum.LOW: 1,
        }
        return penalties.get(self.severity, 0)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la entidad a diccionario."""
        return {
            "id": str(self.id),
            "review_id": str(self.review_id),
            "agent_type": self.agent_type,
            "severity": self.severity.value if self.severity else None,
            "issue_type": self.issue_type,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "message": self.message,
            "suggestion": self.suggestion,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
