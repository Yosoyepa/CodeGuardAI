"""Tests para la dependencia de autenticación."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.core.dependencies.auth import get_current_user, get_optional_user
from src.external.clerk_client import ClerkTokenExpiredError, ClerkTokenInvalidError
from src.schemas.user import Role, User


class TestGetCurrentUser:
    """Tests para get_current_user."""

    @pytest.mark.asyncio
    async def test_missing_credentials_raises_401(self):
        """Sin credenciales debe lanzar 401."""
        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials=None)

        assert exc.value.status_code == 401
        assert "requerido" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        """Token válido retorna usuario."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        mock_payload = {
            "sub": "user_abc123",
            "email": "test@example.com",
            "name": "Test User",
        }

        with patch("src.core.dependencies.auth.ClerkClient") as MockClerk:
            mock_client = MockClerk.return_value
            mock_client.verify_token.return_value = mock_payload

            user = await get_current_user(credentials=credentials)

        assert isinstance(user, User)
        assert user.id == "user_abc123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == Role.DEVELOPER

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        """Token expirado debe lanzar 401."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired-token")

        with patch("src.core.dependencies.auth.ClerkClient") as MockClerk:
            mock_client = MockClerk.return_value
            mock_client.verify_token.side_effect = ClerkTokenExpiredError("Token expirado")

            with pytest.raises(HTTPException) as exc:
                await get_current_user(credentials=credentials)

        assert exc.value.status_code == 401
        assert "expirado" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        """Token inválido debe lanzar 401."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

        with patch("src.core.dependencies.auth.ClerkClient") as MockClerk:
            mock_client = MockClerk.return_value
            mock_client.verify_token.side_effect = ClerkTokenInvalidError("Token inválido")

            with pytest.raises(HTTPException) as exc:
                await get_current_user(credentials=credentials)

        assert exc.value.status_code == 401
        assert "inválido" in exc.value.detail.lower()


class TestGetOptionalUser:
    """Tests para get_optional_user."""

    @pytest.mark.asyncio
    async def test_no_credentials_returns_none(self):
        """Sin credenciales retorna None."""
        result = await get_optional_user(credentials=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_credentials_returns_user(self):
        """Con credenciales válidas retorna usuario."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        mock_payload = {
            "sub": "user_optional",
            "email": "optional@test.com",
            "name": "Optional User",
        }

        with patch("src.core.dependencies.auth.ClerkClient") as MockClerk:
            mock_client = MockClerk.return_value
            mock_client.verify_token.return_value = mock_payload

            user = await get_optional_user(credentials=credentials)

        assert user is not None
        assert user.id == "user_optional"

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        """Token inválido en get_optional_user debe lanzar 401."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")

        with patch("src.core.dependencies.auth.ClerkClient") as MockClerk:
            mock_client = MockClerk.return_value
            mock_client.verify_token.side_effect = ClerkTokenInvalidError("Token inválido")

            with pytest.raises(HTTPException) as exc:
                await get_optional_user(credentials=credentials)

        assert exc.value.status_code == 401
