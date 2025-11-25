import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base
from src.models.enums.review_status import ReviewStatus


class CodeReviewEntity(Base):
    """
    Entidad ORM que representa la tabla 'code_reviews' en la base de datos.
    """

    __tablename__ = "code_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)

    # RN16: code_content se almacena como bytes encriptados (BYTEA)
    code_content = Column(LargeBinary, nullable=False)

    quality_score = Column(Integer, nullable=False)
    status = Column(Enum(ReviewStatus), nullable=False, index=True)
    total_findings = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
