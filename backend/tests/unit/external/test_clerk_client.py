"""Tests para ClerkClient."""

import time
from unittest.mock import MagicMock, patch

import pytest
from jose import jwt

from src.external.clerk_client import (
    ClerkClient,
    ClerkTokenExpiredError,
    ClerkTokenInvalidError,
)

# Constante para el secret key de tests
TEST_SECRET_KEY = "test-secret-key-12345"


def create_valid_token() -> str:
    """Genera un token JWT válido."""
    now = int(time.time())
    payload = {
        "sub": "user_test123",
        "email": "test@example.com",
        "name": "Test User",
        "exp": now + 3600,
        "iat": now,
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


def create_expired_token() -> str:
    """Genera un token JWT expirado."""
    now = int(time.time())
    payload = {
        "sub": "user_expired",
        "email": "expired@example.com",
        "exp": now - 3600,
        "iat": now - 7200,
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


class TestClerkClient:
    """Tests para ClerkClient."""

    @patch("src.external.clerk_client.settings")
    def test_verify_token_valid(self, mock_settings: MagicMock):
        """Token válido retorna payload correcto."""
        mock_settings.CLERK_JWT_SIGNING_KEY = TEST_SECRET_KEY
        mock_settings.CLERK_SECRET_KEY = None
        mock_settings.CLERK_JWKS_URL = None
        client = ClerkClient()
        token = create_valid_token()

        result = client.verify_token(token)

        # verify_token retorna el payload completo del JWT con 'sub'
        assert result["sub"] == "user_test123"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"

    @patch("src.external.clerk_client.settings")
    def test_verify_token_expired(self, mock_settings: MagicMock):
        """Token expirado lanza ClerkTokenExpiredError."""
        mock_settings.CLERK_JWT_SIGNING_KEY = TEST_SECRET_KEY
        mock_settings.CLERK_SECRET_KEY = None
        mock_settings.CLERK_JWKS_URL = None
        client = ClerkClient()
        token = create_expired_token()

        with pytest.raises(ClerkTokenExpiredError):
            client.verify_token(token)

    @patch("src.external.clerk_client.settings")
    def test_verify_token_invalid(self, mock_settings: MagicMock):
        """Token inválido lanza ClerkTokenInvalidError."""
        mock_settings.CLERK_JWT_SIGNING_KEY = TEST_SECRET_KEY
        mock_settings.CLERK_SECRET_KEY = None
        mock_settings.CLERK_JWKS_URL = None
        client = ClerkClient()

        with pytest.raises(ClerkTokenInvalidError):
            client.verify_token("invalid-token-string")

    @patch("src.external.clerk_client.settings")
    def test_verify_token_malformed(self, mock_settings: MagicMock):
        """Token malformado lanza ClerkTokenInvalidError."""
        mock_settings.CLERK_JWT_SIGNING_KEY = TEST_SECRET_KEY
        mock_settings.CLERK_SECRET_KEY = None
        mock_settings.CLERK_JWKS_URL = None
        client = ClerkClient()

        with pytest.raises(ClerkTokenInvalidError):
            client.verify_token("not.a.valid.jwt.token")

    @patch("src.external.clerk_client.settings")
    def test_get_user_id_from_token(self, mock_settings: MagicMock):
        """get_user_id_from_token retorna el user_id (sub claim)."""
        mock_settings.CLERK_JWT_SIGNING_KEY = TEST_SECRET_KEY
        mock_settings.CLERK_SECRET_KEY = None
        mock_settings.CLERK_JWKS_URL = None
        client = ClerkClient()
        token = create_valid_token()

        user_id = client.get_user_id_from_token(token)

        assert user_id == "user_test123"

    @patch("src.external.clerk_client.settings")
    def test_get_user_id_missing_sub(self, mock_settings: MagicMock):
        """Token sin sub lanza ClerkTokenInvalidError."""
        mock_settings.CLERK_JWT_SIGNING_KEY = TEST_SECRET_KEY
        mock_settings.CLERK_SECRET_KEY = None
        mock_settings.CLERK_JWKS_URL = None
        client = ClerkClient()

        now = int(time.time())
        payload = {
            "email": "nosub@example.com",
            "exp": now + 3600,
        }
        token = jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")

        with pytest.raises(ClerkTokenInvalidError) as exc:
            client.get_user_id_from_token(token)

        # El mensaje ahora menciona 'sub' en lugar de 'user_id'
        assert "sub" in str(exc.value).lower()
