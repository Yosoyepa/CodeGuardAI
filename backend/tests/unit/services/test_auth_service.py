"""Tests para AuthService."""

from unittest.mock import MagicMock

import pytest

from src.external.clerk_client import ClerkTokenInvalidError
from src.models.enums.user_role import UserRole
from src.models.user import UserEntity
from src.schemas.user import Role, User
from src.services.auth_service import AuthService


class TestAuthService:
    """Tests para AuthService."""

    @pytest.fixture
    def mock_clerk_client(self):
        """Mock de ClerkClient."""
        return MagicMock()

    @pytest.fixture
    def mock_user_repository(self):
        """Mock de UserRepository."""
        return MagicMock()

    @pytest.fixture
    def auth_service(self, mock_clerk_client, mock_user_repository):
        """Crea instancia de AuthService con mocks."""
        return AuthService(mock_clerk_client, mock_user_repository)

    @pytest.fixture
    def sample_user_entity(self):
        """Crea una entidad de usuario de prueba."""
        entity = MagicMock(spec=UserEntity)
        entity.id = "user_abc123"
        entity.email = "test@example.com"
        entity.name = "Test User"
        entity.role = UserRole.DEVELOPER
        return entity

    def test_login_user_creates_new_user(
        self, auth_service, mock_clerk_client, mock_user_repository, sample_user_entity
    ):
        """login_user crea usuario si no existe."""
        mock_clerk_client.verify_token.return_value = {
            "user_id": "user_new",
            "email": "new@example.com",
            "name": "New User",
        }
        mock_user_repository.get_by_id.return_value = None
        mock_user_repository.create.return_value = sample_user_entity

        result = auth_service.login_user("valid-token")

        assert isinstance(result, User)
        mock_user_repository.get_by_id.assert_called_once_with("user_new")
        mock_user_repository.create.assert_called_once()

    def test_login_user_updates_existing_user(
        self, auth_service, mock_clerk_client, mock_user_repository, sample_user_entity
    ):
        """login_user actualiza usuario si ya existe."""
        mock_clerk_client.verify_token.return_value = {
            "user_id": "user_abc123",
            "email": "updated@example.com",
            "name": "Updated Name",
        }
        mock_user_repository.get_by_id.return_value = sample_user_entity
        mock_user_repository.update.return_value = sample_user_entity

        result = auth_service.login_user("valid-token")

        assert isinstance(result, User)
        mock_user_repository.update.assert_called_once()
        mock_user_repository.create.assert_not_called()

    def test_login_user_invalid_token_raises(
        self, auth_service, mock_clerk_client, mock_user_repository
    ):
        """login_user propaga error si token es inválido."""
        mock_clerk_client.verify_token.side_effect = ClerkTokenInvalidError("Invalid")

        with pytest.raises(ClerkTokenInvalidError):
            auth_service.login_user("invalid-token")

    def test_get_user_from_token(self, auth_service, mock_clerk_client):
        """get_user_from_token retorna User sin sincronizar BD."""
        mock_clerk_client.verify_token.return_value = {
            "user_id": "user_fromtoken",
            "email": "fromtoken@example.com",
            "name": "From Token",
        }

        result = auth_service.get_user_from_token("valid-token")

        assert isinstance(result, User)
        assert result.id == "user_fromtoken"
        assert result.email == "fromtoken@example.com"
        assert result.role == Role.DEVELOPER
