"""
Unit tests for Analysis Schemas
Tests para los esquemas de análisis
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.schemas.analysis import AnalysisContext, AnalysisRequest, AnalysisResponse
from src.schemas.finding import Finding, Severity


class TestAnalysisContext:
    """Tests para AnalysisContext schema."""

    def test_create_valid_context(self):
        """Test crear contexto válido."""
        context = AnalysisContext(
            code_content="def hello():\n    print('Hello')", filename="test.py"
        )

        assert context.code_content == "def hello():\n    print('Hello')"
        assert context.filename == "test.py"
        assert context.language == "python"
        assert context.analysis_id is not None
        assert isinstance(context.created_at, datetime)

    def test_empty_code_raises_error(self):
        """Test que código vacío lanza error."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisContext(code_content="", filename="test.py")

        assert "code_content" in str(exc_info.value).lower()

    def test_whitespace_only_code_raises_error(self):
        """Test que código solo con espacios lanza error."""
        with pytest.raises(ValidationError):
            AnalysisContext(code_content="   \n  ", filename="test.py")

    def test_invalid_filename_extension(self):
        """Test que extensión no .py lanza error."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisContext(code_content="code", filename="test.txt")

        assert "Python files" in str(exc_info.value)

    def test_short_filename_raises_error(self):
        """Test que filename muy corto lanza error."""
        with pytest.raises(ValidationError):
            AnalysisContext(code_content="code", filename=".p")

    def test_line_count_property(self):
        """Test propiedad line_count."""
        context = AnalysisContext(code_content="line1\nline2\nline3", filename="test.py")
        assert context.line_count == 3

    def test_line_count_single_line(self):
        """Test line_count con una línea."""
        context = AnalysisContext(code_content="single line", filename="test.py")
        assert context.line_count == 1

    def test_char_count_property(self):
        """Test propiedad char_count."""
        context = AnalysisContext(code_content="hello world", filename="test.py")
        assert context.char_count == 11

    def test_add_metadata(self):
        """Test agregar metadata."""
        context = AnalysisContext(code_content="code", filename="test.py")

        context.add_metadata("user_id", "123")
        context.add_metadata("project", "CodeGuard")

        assert context.metadata["user_id"] == "123"
        assert context.metadata["project"] == "CodeGuard"

    def test_metadata_persists_after_mutation(self):
        """Test que metadata persiste después de mutación."""
        context = AnalysisContext(code_content="code", filename="test.py")

        context.add_metadata("key1", "value1")
        assert "key1" in context.metadata

        context.add_metadata("key2", "value2")
        assert "key1" in context.metadata  # key1 todavía existe


class TestAnalysisRequest:
    """Tests para AnalysisRequest schema."""

    def test_create_valid_request(self):
        """Test crear request válido."""
        request = AnalysisRequest(filename="app.py", code_content="def main():\n    pass")

        assert request.filename == "app.py"
        assert request.code_content == "def main():\n    pass"
        assert request.agents_config is None

    def test_request_with_agents_config(self):
        """Test request con configuración de agentes."""
        config = {"security": True, "quality": True, "performance": False, "style": True}
        request = AnalysisRequest(filename="app.py", code_content="code", agents_config=config)

        assert request.agents_config == config
        assert request.agents_config["security"] is True
        assert request.agents_config["performance"] is False


class TestAnalysisResponse:
    """Tests para AnalysisResponse schema."""

    def test_create_response(self):
        """Test crear response."""
        from uuid import uuid4

        analysis_id = uuid4()
        response = AnalysisResponse(
            analysis_id=analysis_id,
            filename="app.py",
            status="pending",
            created_at=datetime.utcnow(),
        )

        assert response.analysis_id == analysis_id
        assert response.filename == "app.py"
        assert response.status == "pending"


class TestFinding:
    """Tests para Finding schema."""

    def test_create_valid_finding(self):
        """Test crear finding válido."""
        finding = Finding(
            severity=Severity.CRITICAL,
            issue_type="dangerous_function",
            message="Use of eval detected",
            line_number=10,
            agent_name="SecurityAgent",
        )

        assert finding.severity == Severity.CRITICAL
        assert finding.issue_type == "dangerous_function"
        assert finding.line_number == 10
        assert isinstance(finding.detected_at, datetime)

    def test_invalid_line_number_zero(self):
        """Test que line_number < 1 lanza error."""
        with pytest.raises(ValidationError):
            Finding(
                severity=Severity.CRITICAL,
                issue_type="test",
                message="Test message",
                line_number=0,
                agent_name="TestAgent",
            )

    def test_invalid_line_number_negative(self):
        """Test que line_number negativo lanza error."""
        with pytest.raises(ValidationError):
            Finding(
                severity=Severity.CRITICAL,
                issue_type="test",
                message="Test message",
                line_number=-1,
                agent_name="TestAgent",
            )

    def test_is_critical_property(self):
        """Test propiedad is_critical."""
        critical = Finding(
            severity=Severity.CRITICAL,
            issue_type="test",
            message="Test message",
            line_number=1,
            agent_name="TestAgent",
        )

        assert critical.is_critical is True

        non_critical = Finding(
            severity=Severity.INFO,
            issue_type="test",
            message="Test message",
            line_number=1,
            agent_name="TestAgent",
        )

        assert non_critical.is_critical is False

    def test_is_high_or_critical_property(self):
        """Test propiedad is_high_or_critical."""
        critical = Finding(
            severity=Severity.CRITICAL,
            issue_type="test",
            message="Test message",
            line_number=1,
            agent_name="TestAgent",
        )
        assert critical.is_high_or_critical is True

        high = Finding(
            severity=Severity.HIGH,
            issue_type="test",
            message="Test message",
            line_number=1,
            agent_name="TestAgent",
        )
        assert high.is_high_or_critical is True

        medium = Finding(
            severity=Severity.MEDIUM,
            issue_type="test",
            message="Test message",
            line_number=1,
            agent_name="TestAgent",
        )
        assert medium.is_high_or_critical is False

    def test_is_actionable_property(self):
        """Test propiedad is_actionable."""
        critical = Finding(
            severity=Severity.CRITICAL,
            issue_type="test",
            message="Test message",
            line_number=1,
            agent_name="TestAgent",
        )
        assert critical.is_actionable is True

        info = Finding(
            severity=Severity.INFO,
            issue_type="test",
            message="Test message",
            line_number=1,
            agent_name="TestAgent",
        )
        assert info.is_actionable is False


class TestAnalysisContextHelpers:
    def test_code_is_dedented_and_ast_cached(self):
        context = AnalysisContext(
            code_content="    def foo():\n        return 1",
            filename="foo.py",
        )
        assert context.code_content.startswith("def foo")
        first_ast = context.get_ast()
        assert context.get_ast() is first_ast

    def test_get_ast_invalid_code_raises(self):
        context = AnalysisContext(code_content="def broken(", filename="bad.py")
        with pytest.raises(SyntaxError):
            context.get_ast()

    def test_get_lines_and_snippets(self):
        context = AnalysisContext(code_content="a\nb\nc", filename="file.py")
        assert context.get_line(2) == "b"
        assert context.get_line(99) is None
        assert context.get_code_snippet(1, 2) == "a\nb"

    def test_finding_from_and_to_dict_without_detected_at(self):
        data = {
            "severity": "critical",
            "issue_type": "dangerous_function",
            "message": "Use of eval() detected",
            "line_number": 5,
            "agent_name": "SecurityAgent",
        }
        finding = Finding.from_dict(data)
        serialized = finding.to_dict()
        assert serialized["severity"] == "critical"
        assert "detected_at" in serialized

    def test_calculate_penalty_map(self):
        finding = Finding(
            severity=Severity.HIGH,
            issue_type="test",
            message="Test issue",
            line_number=1,
            agent_name="TestAgent",
        )
        assert finding.calculate_penalty() == 5
