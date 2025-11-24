from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from src.schemas.finding import Finding, Severity
from src.services.analysis_service import AnalysisService


# Fixtures
@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return AnalysisService(mock_repo)


# Tests de Validación de Archivo (RN4)


@pytest.mark.asyncio
async def test_validate_file_success(service):
    """Verifica que un archivo válido pase la validación."""
    content = b"import os\n" * 6  # > 5 líneas
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "valid.py"
    mock_file.read.return_value = content

    result = await service._validate_file(mock_file)
    assert result == content.decode("utf-8")


@pytest.mark.asyncio
async def test_validate_file_extension_error(service):
    """Verifica error 422 con extensión inválida."""
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "script.txt"

    with pytest.raises(HTTPException) as exc:
        await service._validate_file(mock_file)
    assert exc.value.status_code == 422
    assert "Solo se aceptan archivos .py" in exc.value.detail


@pytest.mark.asyncio
async def test_validate_file_size_error(service):
    """Verifica error 413 con archivo muy grande (>10MB)."""
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "big.py"
    # Simular 11MB
    mock_file.read.return_value = b"a" * (11 * 1024 * 1024)

    with pytest.raises(HTTPException) as exc:
        await service._validate_file(mock_file)
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_validate_file_empty_error(service):
    """Verifica error 422 con archivo con pocas líneas (<5)."""
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "empty.py"
    mock_file.read.return_value = b"print('hi')"

    with pytest.raises(HTTPException) as exc:
        await service._validate_file(mock_file)
    assert exc.value.status_code == 422


# Tests de Cálculo de Score (RN8)


def test_calculate_quality_score_mixed(service):
    """Prueba cálculo de score con hallazgos mixtos."""
    findings = [
        Finding(
            severity=Severity.CRITICAL,
            issue_type="security",
            message="Critical vulnerability found",  # > 5 chars
            line_number=1,
            agent_name="test",
        ),  # -10
        Finding(
            severity=Severity.HIGH,
            issue_type="security",
            message="High severity issue found",  # > 5 chars
            line_number=1,
            agent_name="test",
        ),  # -5
    ]
    score = service._calculate_quality_score(findings)
    assert score == 85  # 100 - 15


def test_calculate_quality_score_perfect(service):
    """Prueba score 100 sin hallazgos."""
    score = service._calculate_quality_score([])
    assert score == 100


def test_calculate_quality_score_zero_floor(service):
    """Prueba que el score no baje de 0."""
    # 11 críticos = -110 puntos
    findings = [
        Finding(
            severity=Severity.CRITICAL,
            issue_type="security",
            message="Critical vulnerability found",  # > 5 chars
            line_number=1,
            agent_name="test",
        )
    ] * 11

    score = service._calculate_quality_score(findings)
    assert score == 0
