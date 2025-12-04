"""
Entidad ORM para code reviews.
Alineado con tabla 'code_reviews' en PostgreSQL (Supabase).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base
from src.models.enums.review_status import ReviewStatus

if TYPE_CHECKING:
    from src.models.finding import AgentFindingEntity
    from src.models.user import UserEntity


class CodeReviewEntity(Base):
    """
    Entidad ORM que representa la tabla 'code_reviews' en la base de datos.

    Attributes:
        id: UUID del análisis
        user_id: FK a users (Clerk user_id)
        filename: Nombre del archivo analizado
        code_content: Contenido encriptado con AES-256 (BYTEA)
        quality_score: Puntuación de calidad (0-100)
        status: PENDING, PROCESSING, COMPLETED, FAILED
        total_findings: Número total de hallazgos
        error_message: Mensaje de error si falló
        created_at: Timestamp de creación
        completed_at: Timestamp de finalización
    """

    __tablename__ = "code_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename = Column(String(500), nullable=False)

    # RN16: code_content se almacena como bytes encriptados (BYTEA)
    code_content = Column(LargeBinary, nullable=False)

    quality_score = Column(Integer, nullable=True)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False, index=True)
    total_findings = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user: "UserEntity" = relationship("UserEntity", back_populates="code_reviews")

    findings: List["AgentFindingEntity"] = relationship(
        "AgentFindingEntity",
        back_populates="code_review",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return (
            f"<CodeReviewEntity("
            f"id={self.id}, "
            f"filename={self.filename}, "
            f"status={self.status}"
            f")>"
        )

    def calculate_quality_score(self) -> int:
        """
        Calcula el quality score basado en los findings.

        Formula: score = max(0, 100 - sum(penalties))
        """

        total_penalty = sum(f.penalty for f in self.findings)
        return max(0, 100 - total_penalty)
