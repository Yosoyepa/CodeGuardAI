from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models.code_review import CodeReviewEntity
from src.models.enums.review_status import ReviewStatus
from src.repositories.code_review_repository import CodeReviewRepository
from src.schemas.analysis import CodeReview
from src.utils.encryption.aes_encryptor import decrypt_aes256, encrypt_aes256


def test_encrypt_decrypt_cycle():
    """Verifica que lo que se encripta se pueda desencriptar correctamente."""
    original = "Secret Code 123"
    encrypted = encrypt_aes256(original)
    decrypted = decrypt_aes256(encrypted)

    assert original == decrypted
    assert encrypted != original
    assert isinstance(encrypted, bytes)


def test_encrypt_empty_raises_error():
    """Verifica que encriptar vacío lance error."""
    with pytest.raises(ValueError):
        encrypt_aes256("")


def test_decrypt_empty_returns_empty():
    """Verifica que desencriptar bytes vacíos retorne string vacío."""
    assert decrypt_aes256(b"") == ""
    assert decrypt_aes256(None) == ""


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def repo(mock_session):
    return CodeReviewRepository(mock_session)


@pytest.fixture
def sample_review():
    return CodeReview(
        id=uuid4(),
        user_id="user_123",
        filename="test.py",
        code_content="print('Hello')",
        quality_score=100,
        status=ReviewStatus.PENDING,
        total_findings=0,
        created_at=datetime.utcnow(),
    )


def test_create_success(repo, mock_session, sample_review):
    """Verifica creación exitosa y encriptación."""
    result = repo.create(sample_review)

    assert result == sample_review
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

    # Verificar que se guardó encriptado
    args, _ = mock_session.add.call_args
    entity = args[0]
    assert entity.code_content != "print('Hello')"
    assert isinstance(entity.code_content, bytes)


def test_create_db_error(repo, mock_session, sample_review):
    """Verifica manejo de errores de DB al crear."""
    mock_session.commit.side_effect = SQLAlchemyError("DB Error")

    with pytest.raises(SQLAlchemyError):
        repo.create(sample_review)

    mock_session.rollback.assert_called_once()


def test_find_by_id_success(repo, mock_session):
    """Verifica búsqueda exitosa y desencriptación."""
    review_id = uuid4()
    encrypted_content = encrypt_aes256("print('Found')")

    mock_entity = CodeReviewEntity(
        id=review_id,
        user_id="user_1",
        filename="found.py",
        code_content=encrypted_content,
        quality_score=90,
        status=ReviewStatus.COMPLETED,
        total_findings=2,
        created_at=datetime.utcnow(),
    )
    mock_session.get.return_value = mock_entity

    result = repo.find_by_id(review_id)

    assert result is not None
    assert result.id == review_id
    assert result.code_content == "print('Found')"  # Desencriptado
    assert result.status == ReviewStatus.COMPLETED


def test_find_by_id_not_found(repo, mock_session):
    """Verifica retorno None si no existe."""
    mock_session.get.return_value = None
    result = repo.find_by_id(uuid4())
    assert result is None


def test_find_by_id_decryption_error(repo, mock_session):
    """Verifica manejo de error al desencriptar/recuperar."""
    review_id = uuid4()
    mock_entity = CodeReviewEntity(
        id=review_id, code_content=b"invalid_bytes"  # Esto fallará al desencriptar con Fernet
    )
    mock_session.get.return_value = mock_entity

    # Mockear decrypt para forzar error genérico si Fernet no falla con basura
    # O confiar en que Fernet falle. Fernet lanza InvalidToken.
    # Pero el repo captura Exception.

    with pytest.raises(Exception):
        repo.find_by_id(review_id)
