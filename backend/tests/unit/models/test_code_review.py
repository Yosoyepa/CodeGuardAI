"""Tests para CodeReviewEntity model."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, PropertyMock

import pytest

from src.models.code_review import CodeReviewEntity
from src.models.enums.review_status import ReviewStatus
from src.models.enums.severity_enum import SeverityEnum


class TestCodeReviewEntityRepr:
    """Tests para __repr__."""

    def test_repr_returns_readable_string(self):
        """__repr__ retorna representación legible."""
        review_id = uuid.uuid4()
        review = CodeReviewEntity(
            id=review_id,
            user_id="user_123",
            filename="test_file.py",
            code_content=b"encrypted_content",
            status=ReviewStatus.COMPLETED,
        )

        result = repr(review)

        assert "CodeReviewEntity" in result
        assert "test_file.py" in result
        assert "COMPLETED" in result or "completed" in result.lower()


class TestCodeReviewEntityCalculateQualityScore:
    """Tests para calculate_quality_score."""

    def test_calculate_quality_score_no_findings(self):
        """Sin findings retorna score 100."""
        review = CodeReviewEntity(
            id=uuid.uuid4(),
            user_id="user_123",
            filename="clean_file.py",
            code_content=b"content",
        )
        # Mock de findings vacío
        review.findings = []

        score = review.calculate_quality_score()

        assert score == 100

    def test_calculate_quality_score_with_findings(self):
        """Con findings calcula penalidades correctamente."""
        review = CodeReviewEntity(
            id=uuid.uuid4(),
            user_id="user_123",
            filename="file_with_issues.py",
            code_content=b"content",
        )
        
        # Mock de findings con penalidades
        finding1 = MagicMock()
        finding1.penalty = 10  # CRITICAL
        finding2 = MagicMock()
        finding2.penalty = 5   # HIGH
        finding3 = MagicMock()
        finding3.penalty = 2   # MEDIUM
        
        review.findings = [finding1, finding2, finding3]

        score = review.calculate_quality_score()

        # 100 - (10 + 5 + 2) = 83
        assert score == 83

    def test_calculate_quality_score_floor_at_zero(self):
        """Score mínimo es 0, no negativo."""
        review = CodeReviewEntity(
            id=uuid.uuid4(),
            user_id="user_123",
            filename="terrible_file.py",
            code_content=b"content",
        )
        
        # Mock de muchos findings críticos
        findings = []
        for _ in range(15):
            f = MagicMock()
            f.penalty = 10  # 15 x 10 = 150
            findings.append(f)
        
        review.findings = findings

        score = review.calculate_quality_score()

        assert score == 0  # max(0, 100 - 150) = 0
