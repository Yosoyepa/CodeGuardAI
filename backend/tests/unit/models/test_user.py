"""Tests para UserEntity model."""

from datetime import date, datetime
from unittest.mock import patch

import pytest

from src.models.enums.user_role import UserRole
from src.models.user import UserEntity


class TestUserEntityRepr:
    """Tests para __repr__."""

    def test_repr_returns_readable_string(self):
        """__repr__ retorna representación legible."""
        user = UserEntity(
            id="user_123",
            email="test@example.com",
            role=UserRole.DEVELOPER,
        )

        result = repr(user)

        assert "user_123" in result
        assert "test@example.com" in result
        assert "UserEntity" in result


class TestUserEntityCanAnalyze:
    """Tests para can_analyze (rate limiting RN3)."""

    def test_admin_always_can_analyze(self):
        """Admin siempre puede analizar sin límite."""
        user = UserEntity(
            id="admin_user",
            email="admin@example.com",
            role=UserRole.ADMIN,
            daily_analysis_count=100,  # Muchos análisis
            last_analysis_date=date.today(),
        )

        assert user.can_analyze() is True
        assert user.can_analyze(max_daily=5) is True

    def test_developer_can_analyze_new_day(self):
        """Developer puede analizar si es un nuevo día."""
        yesterday = date(2025, 11, 30)
        user = UserEntity(
            id="dev_user",
            email="dev@example.com",
            role=UserRole.DEVELOPER,
            daily_analysis_count=10,  # Alcanzó límite ayer
            last_analysis_date=yesterday,
        )

        with patch("src.models.user.date") as mock_date:
            mock_date.today.return_value = date(2025, 12, 1)  # Hoy es nuevo día
            assert user.can_analyze() is True

    def test_developer_can_analyze_under_limit(self):
        """Developer puede analizar si está bajo el límite diario."""
        today = date.today()
        user = UserEntity(
            id="dev_user",
            email="dev@example.com",
            role=UserRole.DEVELOPER,
            daily_analysis_count=5,
            last_analysis_date=today,
        )

        assert user.can_analyze(max_daily=10) is True

    def test_developer_cannot_analyze_at_limit(self):
        """Developer NO puede analizar si alcanzó el límite."""
        today = date.today()
        user = UserEntity(
            id="dev_user",
            email="dev@example.com",
            role=UserRole.DEVELOPER,
            daily_analysis_count=10,
            last_analysis_date=today,
        )

        assert user.can_analyze(max_daily=10) is False

    def test_developer_cannot_analyze_over_limit(self):
        """Developer NO puede analizar si está sobre el límite."""
        today = date.today()
        user = UserEntity(
            id="dev_user",
            email="dev@example.com",
            role=UserRole.DEVELOPER,
            daily_analysis_count=15,
            last_analysis_date=today,
        )

        assert user.can_analyze(max_daily=10) is False

    def test_can_analyze_with_no_previous_analysis(self):
        """Usuario sin análisis previos puede analizar."""
        user = UserEntity(
            id="new_user",
            email="new@example.com",
            role=UserRole.DEVELOPER,
            daily_analysis_count=0,
            last_analysis_date=None,
        )

        assert user.can_analyze() is True


class TestUserEntityIncrementAnalysisCount:
    """Tests para increment_analysis_count."""

    def test_increment_resets_on_new_day(self):
        """Contador se reinicia en nuevo día."""
        yesterday = date(2025, 11, 30)
        user = UserEntity(
            id="dev_user",
            email="dev@example.com",
            role=UserRole.DEVELOPER,
            daily_analysis_count=5,
            last_analysis_date=yesterday,
        )

        with patch("src.models.user.date") as mock_date:
            today = date(2025, 12, 1)
            mock_date.today.return_value = today

            user.increment_analysis_count()

            assert user.daily_analysis_count == 1
            assert user.last_analysis_date == today

    def test_increment_same_day(self):
        """Contador se incrementa en el mismo día."""
        today = date.today()
        user = UserEntity(
            id="dev_user",
            email="dev@example.com",
            role=UserRole.DEVELOPER,
            daily_analysis_count=3,
            last_analysis_date=today,
        )

        user.increment_analysis_count()

        assert user.daily_analysis_count == 4
        assert user.last_analysis_date == today

    def test_increment_first_analysis_ever(self):
        """Primer análisis del usuario."""
        user = UserEntity(
            id="new_user",
            email="new@example.com",
            role=UserRole.DEVELOPER,
            daily_analysis_count=0,
            last_analysis_date=None,
        )

        with patch("src.models.user.date") as mock_date:
            today = date(2025, 12, 1)
            mock_date.today.return_value = today

            user.increment_analysis_count()

            assert user.daily_analysis_count == 1
            assert user.last_analysis_date == today
