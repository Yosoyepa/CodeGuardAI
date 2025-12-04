"""Tests de integración para auth router."""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from src.main import app
from src.models.enums.user_role import UserRole
from src.models.user import UserEntity

# Test secret key
TEST_SECRET_KEY = "test-secret-key-for-router-tests"


def create_valid_token(user_id: str = "user_123", email: str = "test@example.com") -> str:
    """Genera un token JWT válido para tests."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
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
        "exp": now - 3600,  # Expirado hace 1 hora
        "iat": now - 7200,
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


@pytest.fixture
def client():
    """TestClient de FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_user_entity():
    """UserEntity mockeado."""
    entity = MagicMock(spec=UserEntity)
    entity.id = "user_123"
    entity.email = "test@example.com"
    entity.name = "Test User"
    entity.role = UserRole.DEVELOPER
    return entity


class TestLoginEndpoint:
    """Tests para POST /api/v1/auth/login."""

    @patch("src.routers.auth.ClerkClient")
    @patch("src.routers.auth.UserRepository")
    @patch("src.routers.auth.get_db")
    def test_login_success_new_user(
        self, mock_get_db, mock_repo_class, mock_clerk_class, client, mock_user_entity
    ):
        """Login exitoso crea usuario nuevo."""
        # Arrange
        mock_clerk = MagicMock()
        mock_clerk.verify_token.return_value = {
            "sub": "user_123",
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_clerk_class.return_value = mock_clerk

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None  # Usuario no existe
        mock_repo.create.return_value = mock_user_entity
        mock_repo_class.return_value = mock_repo

        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])

        token = create_valid_token()

        # Act
        response = client.post(
            "/api/v1/auth/login",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user_123"
        assert data["email"] == "test@example.com"

    @patch("src.routers.auth.ClerkClient")
    @patch("src.routers.auth.UserRepository")
    @patch("src.routers.auth.get_db")
    def test_login_success_existing_user(
        self, mock_get_db, mock_repo_class, mock_clerk_class, client, mock_user_entity
    ):
        """Login exitoso actualiza usuario existente."""
        # Arrange
        mock_clerk = MagicMock()
        mock_clerk.verify_token.return_value = {
            "sub": "user_123",
            "email": "updated@example.com",
            "name": "Updated Name",
        }
        mock_clerk_class.return_value = mock_clerk

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_user_entity  # Usuario existe
        mock_repo.update.return_value = mock_user_entity
        mock_repo_class.return_value = mock_repo

        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])

        token = create_valid_token()

        # Act
        response = client.post(
            "/api/v1/auth/login",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200

    @patch("src.routers.auth.ClerkClient")
    @patch("src.routers.auth.get_db")
    def test_login_token_expired(self, mock_get_db, mock_clerk_class, client):
        """Token expirado retorna 401."""
        # Arrange
        from src.external.clerk_client import ClerkTokenExpiredError

        mock_clerk = MagicMock()
        mock_clerk.verify_token.side_effect = ClerkTokenExpiredError("Token expirado")
        mock_clerk_class.return_value = mock_clerk

        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])

        token = create_expired_token()

        # Act
        response = client.post(
            "/api/v1/auth/login",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 401
        assert "expirado" in response.json()["detail"].lower()

    @patch("src.routers.auth.ClerkClient")
    @patch("src.routers.auth.get_db")
    def test_login_token_invalid(self, mock_get_db, mock_clerk_class, client):
        """Token inválido retorna 401."""
        # Arrange
        from src.external.clerk_client import ClerkTokenInvalidError

        mock_clerk = MagicMock()
        mock_clerk.verify_token.side_effect = ClerkTokenInvalidError("Token inválido")
        mock_clerk_class.return_value = mock_clerk

        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])

        # Act
        response = client.post(
            "/api/v1/auth/login",
            headers={"Authorization": f"Bearer invalid-token"},
        )

        # Assert
        assert response.status_code == 401
        assert "inválido" in response.json()["detail"].lower()

    def test_login_missing_token(self, client):
        """Sin token retorna 401 o 403 (depende de versión FastAPI)."""
        response = client.post("/api/v1/auth/login")

        # 401 en versiones nuevas de Starlette, 403 en anteriores
        assert response.status_code in (401, 403)


class TestGetMeEndpoint:
    """Tests para GET /api/v1/auth/me."""

    @patch("src.routers.auth.ClerkClient")
    def test_get_me_success(self, mock_clerk_class, client):
        """Token válido retorna datos del usuario."""
        # Arrange
        mock_clerk = MagicMock()
        mock_clerk.verify_token.return_value = {
            "user_id": "user_me",
            "email": "me@example.com",
            "name": "Current User",
        }
        mock_clerk_class.return_value = mock_clerk

        token = create_valid_token(user_id="user_me", email="me@example.com")

        # Act
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user_me"
        assert data["email"] == "me@example.com"

    @patch("src.routers.auth.ClerkClient")
    def test_get_me_token_expired(self, mock_clerk_class, client):
        """Token expirado retorna 401."""
        # Arrange
        from src.external.clerk_client import ClerkTokenExpiredError

        mock_clerk = MagicMock()
        mock_clerk.verify_token.side_effect = ClerkTokenExpiredError("Token expirado")
        mock_clerk_class.return_value = mock_clerk

        token = create_expired_token()

        # Act
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Assert
        assert response.status_code == 401
        assert "expirado" in response.json()["detail"].lower()

    @patch("src.routers.auth.ClerkClient")
    def test_get_me_token_invalid(self, mock_clerk_class, client):
        """Token inválido retorna 401."""
        # Arrange
        from src.external.clerk_client import ClerkTokenInvalidError

        mock_clerk = MagicMock()
        mock_clerk.verify_token.side_effect = ClerkTokenInvalidError("Token inválido")
        mock_clerk_class.return_value = mock_clerk

        # Act
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer bad-token"},
        )

        # Assert
        assert response.status_code == 401
        assert "inválido" in response.json()["detail"].lower()

    def test_get_me_missing_token(self, client):
        """Sin token retorna 401 o 403 (depende de versión FastAPI)."""
        response = client.get("/api/v1/auth/me")

        # 401 en versiones nuevas de Starlette, 403 en anteriores
        assert response.status_code in (401, 403)
