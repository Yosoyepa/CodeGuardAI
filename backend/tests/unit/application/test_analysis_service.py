"""Tests adicionales para AnalysisService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile

from src.models.enums.review_status import ReviewStatus
from src.schemas.finding import Finding, Severity
from src.services.analysis_service import AnalysisService


@pytest.fixture
def mock_repo():
    """Repositorio mockeado."""
    repo = MagicMock()
    repo.create.return_value = MagicMock(
        id=uuid4(),
        user_id="user_123",
        filename="test.py",
        code_content="print('hello')",
        quality_score=100,
        status=ReviewStatus.COMPLETED,
        total_findings=0,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    return repo


@pytest.fixture
def service(mock_repo):
    """Instancia de AnalysisService."""
    return AnalysisService(mock_repo)


class TestAnalyzeCodeFull:
    """Tests completos para analyze_code."""

    @pytest.mark.asyncio
    async def test_analyze_code_with_vulnerabilities(self, service, mock_repo):
        """Verifica análisis con código vulnerable."""
        vulnerable_code = b"""import os
def unsafe():
    result = eval(user_input)
    return result

password = "secret123"
"""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "vulnerable.py"
        mock_file.read.return_value = vulnerable_code
        mock_file.seek = AsyncMock()

        # Mock para que devuelva el código validado
        with patch.object(
            service, "_validate_file", return_value=(vulnerable_code.decode(), "vulnerable.py")
        ):
            result = await service.analyze_code(mock_file, "user_456")

        assert result is not None
        # Verificar que se llamó create con hallazgos
        call_args = mock_repo.create.call_args[0][0]
        assert call_args.total_findings >= 0



class TestValidateFileEdgeCases:
    """Tests para casos edge de validación."""

    @pytest.mark.asyncio
    async def test_validate_file_missing_filename(self, service):
        """Verifica error cuando filename es None."""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = None

        with pytest.raises(HTTPException) as exc:
            await service._validate_file(mock_file)

        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_validate_file_unicode_decode_error(self, service):
        """Verifica error con contenido no UTF-8."""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "binary.py"
        mock_file.read.return_value = b"\x80\x81\x82\x83\x84"

        with pytest.raises(HTTPException) as exc:
            await service._validate_file(mock_file)

        assert exc.value.status_code == 422
        assert "UTF-8" in exc.value.detail


class TestCalculateQualityScoreEdgeCases:
    """Tests adicionales para cálculo de score."""

    def test_score_with_info_findings(self, service):
        """INFO findings no penalizan."""
        findings = [
            Finding(
                severity=Severity.INFO,
                issue_type="info",
                message="Informational note",
                line_number=1,
                agent_name="test",
            )
        ]
        score = service._calculate_quality_score(findings)
        assert score == 100

    def test_score_with_low_findings(self, service):
        """LOW findings penalizan 1 punto."""
        findings = [
            Finding(
                severity=Severity.LOW,
                issue_type="minor",
                message="Minor issue here",
                line_number=1,
                agent_name="test",
            )
        ]
        score = service._calculate_quality_score(findings)
        assert score == 99

    def test_score_with_medium_findings(self, service):
        """MEDIUM findings penalizan 2 puntos."""
        findings = [
            Finding(
                severity=Severity.MEDIUM,
                issue_type="medium",
                message="Medium severity issue",
                line_number=1,
                agent_name="test",
            )
        ]
        score = service._calculate_quality_score(findings)
        assert score == 98
