from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from src.models.enums.review_status import ReviewStatus
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
    # _validate_file returns tuple (content, filename)
    assert result == (content.decode("utf-8"), "valid.py")


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


@pytest.mark.asyncio
async def test_validate_file_no_filename_error(service):
    """Verifica error 422 cuando no hay nombre de archivo."""
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = None

    with pytest.raises(HTTPException) as exc:
        await service._validate_file(mock_file)
    assert exc.value.status_code == 422
    assert "nombre del archivo es requerido" in exc.value.detail


@pytest.mark.asyncio
async def test_validate_file_unicode_error(service):
    """Verifica error 422 con contenido no UTF-8."""
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "binary.py"
    mock_file.read.return_value = b"\x80\x81\x82"  # Invalid UTF-8

    with pytest.raises(HTTPException) as exc:
        await service._validate_file(mock_file)
    assert exc.value.status_code == 422
    assert "codificación UTF-8" in exc.value.detail


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


def test_calculate_quality_score_all_severities(service):
    """Prueba cálculo con todas las severidades."""
    findings = [
        Finding(
            severity=Severity.CRITICAL,
            issue_type="x",
            message="message",
            line_number=1,
            agent_name="x",
        ),  # -10
        Finding(
            severity=Severity.HIGH, issue_type="x", message="message", line_number=1, agent_name="x"
        ),  # -5
        Finding(
            severity=Severity.MEDIUM,
            issue_type="x",
            message="message",
            line_number=1,
            agent_name="x",
        ),  # -2
        Finding(
            severity=Severity.LOW, issue_type="x", message="message", line_number=1, agent_name="x"
        ),  # -1
        Finding(
            severity=Severity.INFO, issue_type="x", message="message", line_number=1, agent_name="x"
        ),  # -0
    ]
    score = service._calculate_quality_score(findings)
    assert score == 100 - (10 + 5 + 2 + 1 + 0)  # 82


# Tests de analyze_code (Integración de servicio)


@pytest.mark.asyncio
async def test_analyze_code_success(service, mock_repo):
    """Prueba el flujo completo de analyze_code."""
    content = b"import os\n" * 6
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "valid.py"
    mock_file.read.return_value = content

    # Mock all three agents used in analysis_service
    with patch("src.services.analysis_service.SecurityAgent") as MockSecurityAgent, patch(
        "src.services.analysis_service.StyleAgent"
    ) as MockStyleAgent, patch("src.services.analysis_service.QualityAgent") as MockQualityAgent:

        mock_sec_instance = MockSecurityAgent.return_value
        mock_sec_instance.analyze.return_value = []

        mock_style_instance = MockStyleAgent.return_value
        mock_style_instance.analyze.return_value = []

        mock_qual_instance = MockQualityAgent.return_value
        mock_qual_instance.analyze.return_value = []

        mock_repo.create.return_value = MagicMock(status=ReviewStatus.COMPLETED)

        result = await service.analyze_code(mock_file, "user_123")

        assert result.status == ReviewStatus.COMPLETED
        mock_repo.create.assert_called_once()
        mock_sec_instance.analyze.assert_called_once()
        mock_style_instance.analyze.assert_called_once()
        mock_qual_instance.analyze.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_code_agent_failure(service, mock_repo):
    """Prueba que el análisis continúe si un agente falla."""
    content = b"import os\n" * 6
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "valid.py"
    mock_file.read.return_value = content

    with patch("src.services.analysis_service.SecurityAgent") as MockSecurityAgent, patch(
        "src.services.analysis_service.StyleAgent"
    ) as MockStyleAgent, patch("src.services.analysis_service.QualityAgent") as MockQualityAgent:

        # Security agent fails (along with StyleAgent in same try block)
        mock_sec_instance = MockSecurityAgent.return_value
        mock_sec_instance.analyze.side_effect = Exception("Security Agent Failed")

        mock_style_instance = MockStyleAgent.return_value
        mock_style_instance.analyze.return_value = []

        # Quality agent succeeds
        mock_qual_instance = MockQualityAgent.return_value
        mock_qual_instance.analyze.return_value = []

        mock_repo.create.return_value = MagicMock(status=ReviewStatus.COMPLETED)

        result = await service.analyze_code(mock_file, "user_123")

        assert result.status == ReviewStatus.COMPLETED
        mock_repo.create.assert_called_once()
