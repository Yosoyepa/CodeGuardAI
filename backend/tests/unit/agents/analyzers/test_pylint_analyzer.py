"""
Unit tests for PylintAnalyzer.

Tests cover:
- Initialization
- Severity mapping
- Output parsing
- Analysis execution
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.agents.analyzers.pylint_analyzer import PylintAnalyzer
from src.schemas.finding import Severity


class TestPylintAnalyzerInitialization:
    """Tests for PylintAnalyzer initialization."""

    def test_init_creates_instance(self):
        """Test that PylintAnalyzer can be instantiated."""
        analyzer = PylintAnalyzer()
        assert analyzer is not None

    def test_init_sets_cmd_template(self):
        """Test that command template is set."""
        analyzer = PylintAnalyzer()
        assert hasattr(analyzer, "_cmd_template")
        assert isinstance(analyzer._cmd_template, list)
        assert "pylint" in str(analyzer._cmd_template)


class TestPylintAnalyzerMapSeverity:
    """Tests for severity mapping."""

    def test_map_severity_error_returns_high(self):
        """Test that 'E' (error) maps to HIGH severity."""
        result = PylintAnalyzer._map_severity("E0001")
        assert result == Severity.HIGH

    def test_map_severity_fatal_returns_high(self):
        """Test that 'F' (fatal) maps to HIGH severity."""
        result = PylintAnalyzer._map_severity("F0001")
        assert result == Severity.HIGH

    def test_map_severity_warning_returns_medium(self):
        """Test that 'W' (warning) maps to MEDIUM severity."""
        result = PylintAnalyzer._map_severity("W0612")
        assert result == Severity.MEDIUM

    def test_map_severity_convention_returns_low(self):
        """Test that 'C' (convention) maps to LOW severity."""
        result = PylintAnalyzer._map_severity("C0114")
        assert result == Severity.LOW

    def test_map_severity_refactor_returns_low(self):
        """Test that 'R' (refactor) maps to LOW severity."""
        result = PylintAnalyzer._map_severity("R0903")
        assert result == Severity.LOW

    def test_map_severity_information_returns_low(self):
        """Test that 'I' (information) maps to LOW severity."""
        result = PylintAnalyzer._map_severity("I0001")
        assert result == Severity.LOW

    def test_map_severity_unknown_returns_low(self):
        """Test that unknown types default to LOW severity."""
        assert PylintAnalyzer._map_severity("X9999") == Severity.LOW
        assert PylintAnalyzer._map_severity("") == Severity.LOW

    def test_map_severity_lowercase_works(self):
        """Test that lowercase prefixes work."""
        assert PylintAnalyzer._map_severity("e0001") == Severity.HIGH
        assert PylintAnalyzer._map_severity("w0001") == Severity.MEDIUM


class TestPylintAnalyzerParseOutput:
    """Tests for output parsing."""

    def test_parse_output_empty_returns_empty_list(self):
        """Test parsing empty output."""
        analyzer = PylintAnalyzer()
        result = analyzer._parse_output("", "x = 1", "StyleAgent")
        assert result == []

    def test_parse_output_valid_format(self):
        """Test parsing valid pylint text output."""
        analyzer = PylintAnalyzer()
        code_content = "x = 1\ny = 2\n"
        # Pylint format: {line}:{column}:{msg_id}:{msg}
        output = "1:0:C0114:Missing module docstring"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert len(result) == 1
        assert result[0].line_number == 1
        assert result[0].severity == Severity.LOW
        assert "Missing module docstring" in result[0].message

    def test_parse_output_multiple_issues(self):
        """Test parsing multiple issues."""
        analyzer = PylintAnalyzer()
        code_content = "x = 1\ny = 2\nz = 3\n"
        output = """1:0:E0001:Syntax error
2:0:W0612:Unused variable 'y'
3:0:C0103:Invalid name 'z'"""
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert len(result) == 3
        assert result[0].severity == Severity.HIGH  # E -> HIGH
        assert result[1].severity == Severity.MEDIUM  # W -> MEDIUM
        assert result[2].severity == Severity.LOW  # C -> LOW

    def test_parse_output_invalid_format_skipped(self):
        """Test that invalid format lines are skipped."""
        analyzer = PylintAnalyzer()
        code_content = "x = 1\n"
        output = """1:0:C0114:Missing module docstring
not a valid line
another invalid line"""
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert len(result) == 1

    def test_parse_output_preserves_line_numbers(self):
        """Test that line numbers are correctly preserved."""
        analyzer = PylintAnalyzer()
        code_content = "\n" * 50 + "x = 1\n"
        output = "42:0:C0114:Test message"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert result[0].line_number == 42

    def test_parse_output_extracts_code_snippet(self):
        """Test that code snippet is extracted from code content."""
        analyzer = PylintAnalyzer()
        code_content = "first_line = 1\nsecond_line = 2\nthird_line = 3\n"
        output = "2:0:C0114:Test message"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert result[0].code_snippet == "second_line = 2"

    def test_parse_output_sets_agent_name(self):
        """Test that agent name is set correctly."""
        analyzer = PylintAnalyzer()
        code_content = "x = 1\n"
        output = "1:0:C0114:Test message"
        result = analyzer._parse_output(output, code_content, "TestAgent")
        assert result[0].agent_name == "TestAgent"

    def test_parse_output_sets_rule_id(self):
        """Test that rule_id includes PYLINT prefix."""
        analyzer = PylintAnalyzer()
        code_content = "x = 1\n"
        output = "1:0:C0114:Test message"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert result[0].rule_id == "PYLINT_C0114"

    def test_parse_output_sets_issue_type(self):
        """Test that issue_type is set to style/pep8."""
        analyzer = PylintAnalyzer()
        code_content = "x = 1\n"
        output = "1:0:C0114:Test message"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert result[0].issue_type == "style/pep8"


class TestPylintAnalyzerAnalyze:
    """Tests for analyze method."""

    def test_analyze_with_no_issues(self):
        """Test analysis of clean code."""
        analyzer = PylintAnalyzer()
        code = "x = 1\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            result = analyzer.analyze(code)
            assert result == []

    def test_analyze_returns_findings(self):
        """Test that analyze returns findings for code with issues."""
        analyzer = PylintAnalyzer()
        code = "x = 1\n"

        pylint_output = "1:0:C0114:Missing module docstring"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=pylint_output, stderr="", returncode=4)
            result = analyzer.analyze(code)
            assert len(result) == 1
            assert result[0].message == "Missing module docstring"

    def test_analyze_handles_file_not_found(self):
        """Test that FileNotFoundError (pylint not installed) is handled."""
        analyzer = PylintAnalyzer()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("pylint not found")
            result = analyzer.analyze("some code")
            assert result == []

    def test_analyze_handles_generic_exception(self):
        """Test that generic exceptions are handled gracefully."""
        analyzer = PylintAnalyzer()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")
            result = analyzer.analyze("some code")
            assert result == []

    def test_analyze_cleans_up_temp_file(self):
        """Test that temporary file is cleaned up after analysis."""
        analyzer = PylintAnalyzer()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            with patch("os.path.exists", return_value=True):
                with patch("os.remove") as mock_remove:
                    analyzer.analyze("x = 1")
                    # os.remove should be called to clean up temp file
                    mock_remove.assert_called()

    def test_analyze_with_agent_name(self):
        """Test analyze with custom agent name."""
        analyzer = PylintAnalyzer()
        code = "x = 1\n"

        pylint_output = "1:0:C0114:Missing module docstring"

        with patch.object(analyzer, "_cmd_template", []):
            with patch("src.agents.analyzers.pylint_analyzer.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout=pylint_output, stderr="", returncode=4)
                result = analyzer.analyze(code, agent_name="CustomAgent")
                assert len(result) == 1
                assert result[0].agent_name == "CustomAgent"

    def test_analyze_default_agent_name(self):
        """Test analyze uses default agent name."""
        analyzer = PylintAnalyzer()
        code = "x = 1\n"

        pylint_output = "1:0:C0114:Missing module docstring"

        with patch.object(analyzer, "_cmd_template", []):
            with patch("src.agents.analyzers.pylint_analyzer.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout=pylint_output, stderr="", returncode=4)
                result = analyzer.analyze(code)
                assert len(result) == 1
                assert result[0].agent_name == "StyleAgent"


class TestPylintAnalyzerIntegration:
    """Integration-like tests for end-to-end behavior."""

    def test_finding_has_all_required_fields(self):
        """Test that findings have all required fields."""
        analyzer = PylintAnalyzer()
        code = "x = 1\n"

        pylint_output = "1:0:C0114:Missing module docstring"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=pylint_output, stderr="", returncode=4)
            result = analyzer.analyze(code)
            assert len(result) == 1
            finding = result[0]

            # Check all Finding fields
            assert finding.severity is not None
            assert finding.issue_type is not None
            assert finding.message is not None
            assert finding.line_number is not None
            assert finding.agent_name is not None
            assert finding.rule_id is not None

    def test_empty_code_returns_empty_list(self):
        """Test analyzing empty code."""
        analyzer = PylintAnalyzer()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            result = analyzer.analyze("")
            assert result == []
