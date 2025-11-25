"""
Integration tests for Analysis API Endpoint.

Tests the /api/v1/analyze endpoint with realistic scenarios
covering file validation, security analysis, and response format.
"""

from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.core.dependencies.auth import get_current_user
from src.core.dependencies.get_db import get_db
from src.main import app
from src.schemas.user import Role, User

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> User:
    """Usuario autenticado de prueba."""
    return User(
        id="user_test_123",
        email="developer@codeguard.ai",
        name="Test Developer",
        role=Role.DEVELOPER,
    )


@pytest.fixture
def mock_db_session():
    """Sesión de base de datos mockeada."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def client(mock_user: User, mock_db_session):
    """Cliente de prueba con dependencias mockeadas."""

    def override_get_current_user():
        return mock_user

    def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


# =============================================================================
# Helper Functions
# =============================================================================


def create_python_file(content: str, filename: str = "test_code.py") -> tuple:
    """Crea un archivo Python simulado para upload."""
    file_bytes = BytesIO(content.encode("utf-8"))
    return ("file", (filename, file_bytes, "text/x-python"))


def create_valid_python_code() -> str:
    """Genera código Python válido con al menos 5 líneas."""
    return '''"""Module docstring."""
import os

def hello_world():
    """Print hello world."""
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
'''


def create_vulnerable_code() -> str:
    """Genera código Python con vulnerabilidades de seguridad."""
    return '''"""Vulnerable code for testing."""
import os
import pickle

def unsafe_eval(user_input):
    """Dangerous eval usage."""
    return eval(user_input)

def unsafe_query(user_id):
    """SQL injection vulnerability."""
    query = "SELECT * FROM users WHERE id = " + user_id
    return query

PASSWORD = "super_secret_password_123"
API_KEY = "sk-1234567890abcdef"
'''


# =============================================================================
# Test Classes
# =============================================================================


class TestAnalyzeEndpointValidation:
    """Tests para validación de archivos (RN4)."""

    def test_reject_non_python_file(self, client: TestClient):
        """Rechaza archivos que no son .py."""
        file_data = create_python_file("print('hello')", "script.js")

        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Solo se aceptan archivos .py" in response.json()["detail"]

    def test_reject_file_without_extension(self, client: TestClient):
        """Rechaza archivos sin extensión."""
        file_data = create_python_file("print('hello')", "script")

        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_reject_empty_file(self, client: TestClient):
        """Rechaza archivos vacíos o con menos de 5 líneas."""
        file_data = create_python_file("# just a comment\n", "empty.py")

        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "al menos 5 líneas" in response.json()["detail"]

    def test_reject_file_too_large(self, client: TestClient):
        """Rechaza archivos mayores a 10MB."""
        large_content = "x = 1\n" * (10 * 1024 * 1024 // 6 + 1)
        file_data = create_python_file(large_content, "large.py")

        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    def test_reject_invalid_utf8_encoding(self, client: TestClient):
        """Rechaza archivos con codificación inválida."""
        invalid_bytes = b"\x80\x81\x82\x83\x84"
        file_bytes = BytesIO(invalid_bytes)
        file_data = ("file", ("invalid.py", file_bytes, "text/x-python"))

        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "UTF-8" in response.json()["detail"]


class TestAnalyzeEndpointSuccess:
    """Tests para análisis exitoso."""

    @patch("src.services.analysis_service.AnalysisService.analyze_code")
    def test_analyze_valid_python_file(self, mock_analyze, client: TestClient):
        """Analiza correctamente un archivo Python válido."""
        mock_analyze.return_value = MagicMock(
            id=uuid4(),
            filename="test_code.py",
            status="completed",
            quality_score=95,
            total_findings=2,
            created_at=datetime.utcnow(),
        )

        file_data = create_python_file(create_valid_python_code())
        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] == "completed"
        assert data["quality_score"] == 95

    @patch("src.services.analysis_service.AnalysisService.analyze_code")
    def test_analyze_vulnerable_code_returns_findings(self, mock_analyze, client: TestClient):
        """Detecta vulnerabilidades y retorna findings."""
        mock_analyze.return_value = MagicMock(
            id=uuid4(),
            filename="vulnerable.py",
            status="completed",
            quality_score=45,
            total_findings=5,
            created_at=datetime.utcnow(),
        )

        file_data = create_python_file(create_vulnerable_code(), "vulnerable.py")
        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_findings"] >= 1
        assert data["quality_score"] < 100


class TestAnalyzeEndpointResponseFormat:
    """Tests para formato de respuesta (AnalysisResponse)."""

    @patch("src.services.analysis_service.AnalysisService.analyze_code")
    def test_response_contains_required_fields(self, mock_analyze, client: TestClient):
        """La respuesta contiene todos los campos requeridos."""
        analysis_id = uuid4()
        mock_analyze.return_value = MagicMock(
            id=analysis_id,
            filename="app.py",
            status="completed",
            quality_score=85,
            total_findings=3,
            created_at=datetime.utcnow(),
        )

        file_data = create_python_file(create_valid_python_code(), "app.py")
        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        required_fields = [
            "analysis_id",
            "filename",
            "status",
            "quality_score",
            "total_findings",
            "created_at",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    @patch("src.services.analysis_service.AnalysisService.analyze_code")
    def test_quality_score_within_bounds(self, mock_analyze, client: TestClient):
        """El quality_score está entre 0 y 100."""
        mock_analyze.return_value = MagicMock(
            id=uuid4(),
            filename="test.py",
            status="completed",
            quality_score=75,
            total_findings=5,
            created_at=datetime.utcnow(),
        )

        file_data = create_python_file(create_valid_python_code())
        response = client.post("/api/v1/analyze", files=[file_data])

        data = response.json()
        assert 0 <= data["quality_score"] <= 100


class TestAnalyzeEndpointAuthentication:
    """Tests para autenticación."""

    def test_reject_unauthenticated_request(self):
        """Rechaza requests sin autenticación."""
        app.dependency_overrides.clear()

        client = TestClient(app)
        file_data = create_python_file(create_valid_python_code())

        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestAnalyzeEndpointErrorHandling:
    """Tests para manejo de errores."""

    def test_missing_file_returns_422(self, client: TestClient):
        """Retorna 422 cuando no se envía archivo."""
        response = client.post("/api/v1/analyze")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("src.services.analysis_service.AnalysisService.analyze_code")
    def test_internal_error_returns_500(self, mock_analyze, client: TestClient):
        """Retorna 500 en errores internos."""
        mock_analyze.side_effect = Exception("Database connection failed")

        file_data = create_python_file(create_valid_python_code())
        response = client.post("/api/v1/analyze", files=[file_data])

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
