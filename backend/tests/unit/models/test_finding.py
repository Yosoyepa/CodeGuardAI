"""Tests para AgentFindingEntity model."""

import uuid
from datetime import datetime

import pytest

from src.models.enums.severity_enum import SeverityEnum
from src.models.finding import AgentFindingEntity


class TestAgentFindingEntityRepr:
    """Tests para __repr__."""

    def test_repr_returns_readable_string(self):
        """__repr__ retorna representación legible."""
        finding_id = uuid.uuid4()
        review_id = uuid.uuid4()
        finding = AgentFindingEntity(
            id=finding_id,
            review_id=review_id,
            agent_type="SecurityAgent",
            severity=SeverityEnum.HIGH,
            issue_type="sql_injection",
            line_number=42,
            message="SQL injection detected",
        )

        result = repr(finding)

        assert "AgentFindingEntity" in result
        assert "SecurityAgent" in result
        assert "42" in result


class TestAgentFindingEntityPenalty:
    """Tests para penalty property."""

    def test_penalty_critical(self):
        """CRITICAL tiene penalidad de 10."""
        finding = AgentFindingEntity(
            id=uuid.uuid4(),
            review_id=uuid.uuid4(),
            agent_type="SecurityAgent",
            severity=SeverityEnum.CRITICAL,
            issue_type="dangerous_function",
            line_number=1,
            message="Critical issue",
        )

        assert finding.penalty == 10

    def test_penalty_high(self):
        """HIGH tiene penalidad de 5."""
        finding = AgentFindingEntity(
            id=uuid.uuid4(),
            review_id=uuid.uuid4(),
            agent_type="SecurityAgent",
            severity=SeverityEnum.HIGH,
            issue_type="hardcoded_password",
            line_number=10,
            message="High severity issue",
        )

        assert finding.penalty == 5

    def test_penalty_medium(self):
        """MEDIUM tiene penalidad de 2."""
        finding = AgentFindingEntity(
            id=uuid.uuid4(),
            review_id=uuid.uuid4(),
            agent_type="QualityAgent",
            severity=SeverityEnum.MEDIUM,
            issue_type="code_smell",
            line_number=20,
            message="Medium severity issue",
        )

        assert finding.penalty == 2

    def test_penalty_low(self):
        """LOW tiene penalidad de 1."""
        finding = AgentFindingEntity(
            id=uuid.uuid4(),
            review_id=uuid.uuid4(),
            agent_type="StyleAgent",
            severity=SeverityEnum.LOW,
            issue_type="style_violation",
            line_number=30,
            message="Low severity issue",
        )

        assert finding.penalty == 1


class TestAgentFindingEntityToDict:
    """Tests para to_dict."""

    def test_to_dict_complete(self):
        """to_dict retorna diccionario con todos los campos."""
        finding_id = uuid.uuid4()
        review_id = uuid.uuid4()
        created = datetime(2025, 12, 1, 10, 0, 0)

        finding = AgentFindingEntity(
            id=finding_id,
            review_id=review_id,
            agent_type="SecurityAgent",
            severity=SeverityEnum.HIGH,
            issue_type="sql_injection",
            line_number=42,
            code_snippet="cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
            message="Potential SQL injection vulnerability",
            suggestion="Use parameterized queries instead",
            metrics={"confidence": 0.95},
            created_at=created,
        )

        result = finding.to_dict()

        assert result["id"] == str(finding_id)
        assert result["review_id"] == str(review_id)
        assert result["agent_type"] == "SecurityAgent"
        assert result["severity"] == "HIGH"
        assert result["issue_type"] == "sql_injection"
        assert result["line_number"] == 42
        assert "SELECT * FROM users" in result["code_snippet"]
        assert result["message"] == "Potential SQL injection vulnerability"
        assert result["suggestion"] == "Use parameterized queries instead"
        assert result["metrics"] == {"confidence": 0.95}
        assert result["created_at"] == "2025-12-01T10:00:00"

    def test_to_dict_with_none_values(self):
        """to_dict maneja valores None correctamente."""
        finding = AgentFindingEntity(
            id=uuid.uuid4(),
            review_id=uuid.uuid4(),
            agent_type="SecurityAgent",
            severity=SeverityEnum.LOW,
            issue_type="minor_issue",
            line_number=1,
            message="Minor issue found",
            code_snippet=None,
            suggestion=None,
            metrics=None,
            created_at=None,
        )

        result = finding.to_dict()

        assert result["code_snippet"] is None
        assert result["suggestion"] is None
        assert result["metrics"] is None
        assert result["created_at"] is None

    def test_to_dict_severity_none(self):
        """to_dict maneja severity None."""
        finding = AgentFindingEntity(
            id=uuid.uuid4(),
            review_id=uuid.uuid4(),
            agent_type="TestAgent",
            severity=None,
            issue_type="test",
            line_number=1,
            message="Test message",
        )

        result = finding.to_dict()

        assert result["severity"] is None
