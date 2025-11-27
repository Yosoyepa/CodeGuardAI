"""
Entidad ORM para usuarios.
Alineado con tabla 'users' en PostgreSQL (Supabase).
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Date, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from src.models.base import Base
from src.models.enums.user_role import UserRole

if TYPE_CHECKING:
    from src.models.code_review import CodeReviewEntity


class UserEntity(Base):
    """
    Entidad ORM que representa la tabla 'users' en la base de datos.

    Attributes:
        id: Clerk user_id (VARCHAR, PK)
        email: Email único del usuario
        name: Nombre del usuario (opcional)
        avatar_url: URL del avatar (opcional)
        role: DEVELOPER o ADMIN
        daily_analysis_count: Contador de análisis del día
        last_analysis_date: Fecha del último análisis
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
    """

    __tablename__ = "users"

    # Clerk user_id como PK (no es UUID, es string de Clerk)
    id = Column(String(255), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER, nullable=False, index=True)

    # Rate limiting (RN3: 10 análisis/día para developers)
    daily_analysis_count = Column(Integer, default=0, nullable=False)
    last_analysis_date = Column(Date, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    code_reviews: List["CodeReviewEntity"] = relationship(
        "CodeReviewEntity", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<UserEntity(id={self.id}, email={self.email}, role={self.role})>"

    def can_analyze(self, max_daily: int = 10) -> bool:
        """
        Verifica si el usuario puede realizar más análisis hoy.

        Args:
            max_daily: Límite diario para developers (default: 10)

        Returns:
            True si puede analizar, False si alcanzó el límite
        """
        if self.role == UserRole.ADMIN:
            return True

        today = date.today()
        if self.last_analysis_date != today:
            return True

        return self.daily_analysis_count < max_daily

    def increment_analysis_count(self) -> None:
        """Incrementa el contador de análisis del día."""
        today = date.today()
        if self.last_analysis_date != today:
            self.daily_analysis_count = 1
            self.last_analysis_date = today
        else:
            self.daily_analysis_count += 1
