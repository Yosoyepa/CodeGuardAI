"""
SQLAlchemy ORM Models para CodeGuard AI.

Este módulo exporta todas las entidades de base de datos para facilitar imports.
"""

from src.models.base import Base
from src.models.code_review import CodeReviewEntity

# Enums
from src.models.enums.review_status import ReviewStatus
from src.models.enums.severity_enum import SeverityEnum
from src.models.enums.user_role import UserRole
from src.models.finding import AgentFindingEntity
from src.models.user import UserEntity

__all__ = [
    # Base
    "Base",
    # Entities
    "UserEntity",
    "CodeReviewEntity",
    "AgentFindingEntity",
    # Enums
    "ReviewStatus",
    "SeverityEnum",
    "UserRole",
]
