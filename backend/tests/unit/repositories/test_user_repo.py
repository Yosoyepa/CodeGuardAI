"""Tests para UserRepository."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.models.enums.user_role import UserRole
from src.models.user import UserEntity
from src.repositories.user_repo import UserRepository


class TestUserRepository:
    """Tests para UserRepository."""

    @pytest.fixture
    def mock_session(self):
        """Mock de SQLAlchemy Session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def repo(self, mock_session):
        """Instancia de UserRepository con session mockeada."""
        return UserRepository(mock_session)

    @pytest.fixture
    def sample_user_entity(self):
        """Crea una entidad de usuario de prueba."""
        entity = MagicMock(spec=UserEntity)
        entity.id = "user_123"
        entity.email = "test@example.com"
        entity.name = "Test User"
        entity.role = UserRole.DEVELOPER
        entity.daily_analysis_count = 0
        entity.last_analysis_date = None
        entity.created_at = datetime(2025, 1, 1, 12, 0, 0)
        entity.updated_at = datetime(2025, 1, 1, 12, 0, 0)
        return entity


class TestGetById:
    """Tests para get_by_id."""

    @pytest.fixture
    def mock_session(self):
        """Mock de SQLAlchemy Session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def repo(self, mock_session):
        """Instancia de UserRepository."""
        return UserRepository(mock_session)

    @pytest.fixture
    def sample_user_entity(self):
        """Entidad de usuario de prueba."""
        entity = MagicMock(spec=UserEntity)
        entity.id = "user_123"
        entity.email = "test@example.com"
        entity.name = "Test User"
        entity.role = UserRole.DEVELOPER
        return entity

    def test_get_by_id_found(self, repo, mock_session, sample_user_entity):
        """get_by_id retorna usuario si existe."""
        # Arrange
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = sample_user_entity

        # Act
        result = repo.get_by_id("user_123")

        # Assert
        assert result == sample_user_entity
        mock_session.query.assert_called_once_with(UserEntity)

    def test_get_by_id_not_found(self, repo, mock_session):
        """get_by_id retorna None si usuario no existe."""
        # Arrange
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        # Act
        result = repo.get_by_id("nonexistent_user")

        # Assert
        assert result is None


class TestGetByEmail:
    """Tests para get_by_email."""

    @pytest.fixture
    def mock_session(self):
        """Mock de SQLAlchemy Session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def repo(self, mock_session):
        """Instancia de UserRepository."""
        return UserRepository(mock_session)

    @pytest.fixture
    def sample_user_entity(self):
        """Entidad de usuario de prueba."""
        entity = MagicMock(spec=UserEntity)
        entity.id = "user_456"
        entity.email = "found@example.com"
        entity.name = "Found User"
        entity.role = UserRole.DEVELOPER
        return entity

    def test_get_by_email_found(self, repo, mock_session, sample_user_entity):
        """get_by_email retorna usuario si existe."""
        # Arrange
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = sample_user_entity

        # Act
        result = repo.get_by_email("found@example.com")

        # Assert
        assert result == sample_user_entity
        assert result.email == "found@example.com"

    def test_get_by_email_not_found(self, repo, mock_session):
        """get_by_email retorna None si email no existe."""
        # Arrange
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        # Act
        result = repo.get_by_email("notfound@example.com")

        # Assert
        assert result is None


class TestCreate:
    """Tests para create."""

    @pytest.fixture
    def mock_session(self):
        """Mock de SQLAlchemy Session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def repo(self, mock_session):
        """Instancia de UserRepository."""
        return UserRepository(mock_session)

    def test_create_user_success(self, repo, mock_session):
        """create crea usuario y llama add, commit, refresh."""
        # Act
        with patch("src.repositories.user_repo.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 12, 1, 10, 0, 0)
            result = repo.create(
                user_id="new_user_123",
                email="newuser@example.com",
                name="New User",
                avatar_url="https://example.com/avatar.png",
                role=UserRole.DEVELOPER,
            )

        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        # Verificar que el usuario fue creado con los datos correctos
        created_user = mock_session.add.call_args[0][0]
        assert created_user.id == "new_user_123"
        assert created_user.email == "newuser@example.com"
        assert created_user.name == "New User"
        assert created_user.avatar_url == "https://example.com/avatar.png"
        assert created_user.role == UserRole.DEVELOPER

    def test_create_user_with_defaults(self, repo, mock_session):
        """create usa valores por defecto correctamente."""
        # Act
        with patch("src.repositories.user_repo.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 12, 1, 10, 0, 0)
            result = repo.create(
                user_id="minimal_user",
                email="minimal@example.com",
            )

        # Assert
        created_user = mock_session.add.call_args[0][0]
        assert created_user.id == "minimal_user"
        assert created_user.email == "minimal@example.com"
        assert created_user.name is None
        assert created_user.avatar_url is None
        assert created_user.role == UserRole.DEVELOPER
        assert created_user.daily_analysis_count == 0


class TestUpdate:
    """Tests para update."""

    @pytest.fixture
    def mock_session(self):
        """Mock de SQLAlchemy Session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def repo(self, mock_session):
        """Instancia de UserRepository."""
        return UserRepository(mock_session)

    @pytest.fixture
    def existing_user(self):
        """Usuario existente para actualizar."""
        user = MagicMock(spec=UserEntity)
        user.id = "user_to_update"
        user.email = "old@example.com"
        user.name = "Old Name"
        user.avatar_url = "https://old.com/avatar.png"
        user.role = UserRole.DEVELOPER
        return user

    def test_update_all_fields(self, repo, mock_session, existing_user):
        """update actualiza todos los campos proporcionados."""
        # Act
        with patch("src.repositories.user_repo.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 12, 1, 15, 0, 0)
            result = repo.update(
                user=existing_user,
                email="new@example.com",
                name="New Name",
                avatar_url="https://new.com/avatar.png",
            )

        # Assert
        assert existing_user.email == "new@example.com"
        assert existing_user.name == "New Name"
        assert existing_user.avatar_url == "https://new.com/avatar.png"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(existing_user)

    def test_update_partial_fields(self, repo, mock_session, existing_user):
        """update solo actualiza campos proporcionados."""
        original_email = existing_user.email
        original_avatar = existing_user.avatar_url

        # Act
        with patch("src.repositories.user_repo.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 12, 1, 15, 0, 0)
            result = repo.update(
                user=existing_user,
                name="Only Name Changed",
            )

        # Assert
        assert existing_user.name == "Only Name Changed"
        # Email y avatar no deberían cambiar
        mock_session.commit.assert_called_once()

    def test_update_no_fields(self, repo, mock_session, existing_user):
        """update sin campos aún actualiza updated_at y hace commit."""
        # Act
        with patch("src.repositories.user_repo.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 12, 1, 15, 0, 0)
            result = repo.update(user=existing_user)

        # Assert
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()


class TestDelete:
    """Tests para delete."""

    @pytest.fixture
    def mock_session(self):
        """Mock de SQLAlchemy Session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def repo(self, mock_session):
        """Instancia de UserRepository."""
        return UserRepository(mock_session)

    @pytest.fixture
    def user_to_delete(self):
        """Usuario para eliminar."""
        user = MagicMock(spec=UserEntity)
        user.id = "user_to_delete"
        user.email = "delete@example.com"
        return user

    def test_delete_success(self, repo, mock_session, user_to_delete):
        """delete elimina usuario y llama commit."""
        # Act
        repo.delete(user_to_delete)

        # Assert
        mock_session.delete.assert_called_once_with(user_to_delete)
        mock_session.commit.assert_called_once()


class TestIncrementAnalysisCount:
    """Tests para increment_analysis_count."""

    @pytest.fixture
    def mock_session(self):
        """Mock de SQLAlchemy Session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def repo(self, mock_session):
        """Instancia de UserRepository."""
        return UserRepository(mock_session)

    @pytest.fixture
    def user_with_count(self):
        """Usuario con contador de análisis."""
        user = MagicMock(spec=UserEntity)
        user.id = "counting_user"
        user.daily_analysis_count = 5
        return user

    def test_increment_analysis_count_success(self, repo, mock_session, user_with_count):
        """increment_analysis_count llama al método del usuario y hace commit."""
        # Act
        result = repo.increment_analysis_count(user_with_count)

        # Assert
        user_with_count.increment_analysis_count.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(user_with_count)
