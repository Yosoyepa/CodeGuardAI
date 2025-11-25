"""Tests para la dependencia de autenticación."""

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from src.core.dependencies.auth import get_current_user
from src.schemas.user import Role, User


class TestGetCurrentUser:
    """Tests para get_current_user."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    async def test_production_requires_valid_token(self):
        """En producción, un token inválido debe lanzar 401."""
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token="invalid-token")

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    async def test_production_missing_token_raises_401(self):
        """En producción, sin token debe lanzar 401."""
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token="")

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"ENVIRONMENT": "development"})
    async def test_development_returns_mock_user(self):
        """En desarrollo, retorna usuario mock."""
        user = await get_current_user(token="any-token")

        assert isinstance(user, User)
        assert user.id == "user_123"
        assert user.role == Role.DEVELOPER

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"ENVIRONMENT": "development"})
    async def test_development_accepts_empty_token(self):
        """En desarrollo, acepta token vacío."""
        user = await get_current_user(token="")

        assert isinstance(user, User)
