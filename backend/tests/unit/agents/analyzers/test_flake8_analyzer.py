"""
Unit tests for Flake8Analyzer.

Tests cover:
- Initialization
- Severity mapping
- Output parsing
- Analysis execution
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.agents.analyzers.flake8_analyzer import Flake8Analyzer
from src.schemas.finding import Severity


class TestFlake8AnalyzerInitialization:
    """Tests for Flake8Analyzer initialization."""

    def test_init_creates_instance(self):
        """Test that Flake8Analyzer can be instantiated."""
        analyzer = Flake8Analyzer()
        assert analyzer is not None

    def test_init_sets_cmd_template(self):
        """Test that command template is set."""
        analyzer = Flake8Analyzer()
        assert hasattr(analyzer, "_cmd_template")
        assert isinstance(analyzer._cmd_template, list)
        assert "flake8" in str(analyzer._cmd_template)


class TestFlake8AnalyzerMapSeverity:
    """Tests for severity mapping."""

    def test_map_severity_fatal_returns_high(self):
        """Test that 'F' (pyflakes) errors map to HIGH severity."""
        result = Flake8Analyzer._map_severity("F401")
        assert result == Severity.HIGH

    def test_map_severity_error_returns_medium(self):
        """Test that 'E' (error) maps to MEDIUM severity."""
        result = Flake8Analyzer._map_severity("E501")
        assert result == Severity.MEDIUM

    def test_map_severity_complexity_returns_medium(self):
        """Test that 'C' (complexity) maps to MEDIUM severity."""
        result = Flake8Analyzer._map_severity("C901")
        assert result == Severity.MEDIUM

    def test_map_severity_warning_returns_low(self):
        """Test that 'W' (warning) maps to LOW severity."""
        result = Flake8Analyzer._map_severity("W291")
        assert result == Severity.LOW

    def test_map_severity_naming_returns_low(self):
        """Test that 'N' (naming) maps to LOW severity."""
        result = Flake8Analyzer._map_severity("N801")
        assert result == Severity.LOW

    def test_map_severity_unknown_returns_low(self):
        """Test that unknown types default to LOW severity."""
        assert Flake8Analyzer._map_severity("X999") == Severity.LOW
        assert Flake8Analyzer._map_severity("") == Severity.LOW

    def test_map_severity_lowercase_works(self):
        """Test that lowercase prefixes work."""
        assert Flake8Analyzer._map_severity("f401") == Severity.HIGH
        assert Flake8Analyzer._map_severity("e501") == Severity.MEDIUM


class TestFlake8AnalyzerParseOutput:
    """Tests for output parsing."""

    def test_parse_output_empty_returns_empty_list(self):
        """Test parsing empty output."""
        analyzer = Flake8Analyzer()
        result = analyzer._parse_output("", "x = 1", "StyleAgent")
        assert result == []

    def test_parse_output_valid_line(self):
        """Test parsing valid flake8 output line."""
        analyzer = Flake8Analyzer()
        code_content = "x = 1\n"
        # Flake8 format: {row}:{col}:{code}:{text}
        output = "1:5:E501:line too long (120 > 79 characters)"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert len(result) == 1
        assert result[0].line_number == 1
        assert result[0].severity == Severity.MEDIUM  # E -> MEDIUM
        assert "line too long" in result[0].message

    def test_parse_output_multiple_issues(self):
        """Test parsing multiple issues."""
        analyzer = Flake8Analyzer()
        code_content = "import os\nx = 1\ny = 2\n"
        output = """1:1:F401:'os' imported but unused
2:5:E501:line too long
3:1:W291:trailing whitespace"""
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert len(result) == 3
        assert result[0].severity == Severity.HIGH  # F -> HIGH
        assert result[1].severity == Severity.MEDIUM  # E -> MEDIUM
        assert result[2].severity == Severity.LOW  # W -> LOW

    def test_parse_output_preserves_line_numbers(self):
        """Test that line numbers are correctly preserved."""
        analyzer = Flake8Analyzer()
        code_content = "\n" * 50 + "x = 1\n"
        output = "42:1:W291:trailing whitespace"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert result[0].line_number == 42

    def test_parse_output_invalid_format_skipped(self):
        """Test that invalid format lines are skipped."""
        analyzer = Flake8Analyzer()
        code_content = "x = 1\ny = 2\n"
        output = """1:1:E501:line too long
not a valid line
2:1:W291:trailing whitespace"""
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert len(result) == 2

    def test_parse_output_extracts_code_snippet(self):
        """Test that code snippet is extracted from code content."""
        analyzer = Flake8Analyzer()
        code_content = "first_line = 1\nsecond_line = 2\nthird_line = 3\n"
        output = "2:1:E501:line too long in this file"  # was "2:1:E501:test"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert result[0].code_snippet == "second_line = 2"

    def test_parse_output_sets_agent_name(self):
        """Test that agent name is set correctly."""
        analyzer = Flake8Analyzer()
        code_content = "x = 1\n"
        output = "1:1:E501:line too long error message"  # was "1:1:E501:test"
        result = analyzer._parse_output(output, code_content, "TestAgent")
        assert result[0].agent_name == "TestAgent"

    def test_parse_output_sets_rule_id(self):
        """Test that rule_id includes FLAKE8 prefix."""
        analyzer = Flake8Analyzer()
        code_content = "x = 1\n"
        output = "1:1:E501:line too long error message"  # was "1:1:E501:test"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert result[0].rule_id == "FLAKE8_E501"

    def test_parse_output_sets_issue_type(self):
        """Test that issue_type is set to style/pep8."""
        analyzer = Flake8Analyzer()
        code_content = "x = 1\n"
        output = "1:1:E501:line too long error message"  # was "1:1:E501:test"
        result = analyzer._parse_output(output, code_content, "StyleAgent")
        assert result[0].issue_type == "style/pep8"


class TestFlake8AnalyzerAnalyze:
    """Tests for analyze method."""

    def test_analyze_with_no_issues(self):
        """Test analysis of clean code."""
        analyzer = Flake8Analyzer()
        code = "x = 1\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            result = analyzer.analyze(code)
            assert result == []

    def test_analyze_returns_findings(self):
        """Test that analyze returns findings for code with issues."""
        analyzer = Flake8Analyzer()
        code = "import os\nx = 1\n"

        flake8_output = "1:1:F401:'os' imported but unused"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=flake8_output, stderr="", returncode=1)
            result = analyzer.analyze(code)
            assert len(result) == 1
            assert "'os' imported but unused" in result[0].message

    def test_analyze_handles_file_not_found(self):
        """Test that FileNotFoundError (flake8 not installed) is handled."""
        analyzer = Flake8Analyzer()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("flake8 not found")
            result = analyzer.analyze("some code")
            assert result == []

    def test_analyze_handles_generic_exception(self):
        """Test that generic exceptions are handled gracefully."""
        analyzer = Flake8Analyzer()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")
            result = analyzer.analyze("some code")
            assert result == []

    def test_analyze_cleans_up_temp_file(self):
        """Test that temporary file is cleaned up after analysis."""
        analyzer = Flake8Analyzer()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            with patch("os.path.exists", return_value=True):
                with patch("os.remove") as mock_remove:
                    analyzer.analyze("x = 1")
                    mock_remove.assert_called()

    def test_analyze_with_agent_name(self):
        """Test analyze with custom agent name."""
        analyzer = Flake8Analyzer()
        code = "import os\n"

        flake8_output = "1:1:F401:unused"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=flake8_output, stderr="", returncode=1)
            result = analyzer.analyze(code, agent_name="CustomAgent")
            assert len(result) == 1
            assert result[0].agent_name == "CustomAgent"

    def test_analyze_default_agent_name(self):
        """Test analyze uses default agent name."""
        analyzer = Flake8Analyzer()
        code = "import os\n"

        flake8_output = "1:1:F401:unused"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=flake8_output, stderr="", returncode=1)
            result = analyzer.analyze(code)
            assert len(result) == 1
            assert result[0].agent_name == "StyleAgent"


class TestFlake8AnalyzerIssueTypes:
    """Tests for issue type categorization by error code."""

    def test_e1_indentation_error(self):
        """Test E1xx indentation errors are parsed."""
        analyzer = Flake8Analyzer()
        code = "x = 1\n"
        output = "1:1:E101:indentation contains mixed spaces and tabs"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1
        assert result[0].severity == Severity.MEDIUM

    def test_e2_whitespace_error(self):
        """Test E2xx whitespace errors are parsed."""
        analyzer = Flake8Analyzer()
        code = "x=1\n"
        output = "1:2:E225:missing whitespace around operator"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1
        assert result[0].severity == Severity.MEDIUM

    def test_e3_blank_line_error(self):
        """Test E3xx blank line errors are parsed."""
        analyzer = Flake8Analyzer()
        code = "def foo():\n    pass\n"
        output = "1:1:E302:expected 2 blank lines, found 1"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1
        assert result[0].severity == Severity.MEDIUM

    def test_e5_line_length_error(self):
        """Test E5xx line length errors are parsed."""
        analyzer = Flake8Analyzer()
        code = "x = 1\n"
        output = "1:80:E501:line too long (120 > 79 characters)"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1
        assert result[0].severity == Severity.MEDIUM

    def test_e7_statement_error(self):
        """Test E7xx statement errors are parsed."""
        analyzer = Flake8Analyzer()
        code = "if x == None: pass\n"
        output = "1:6:E711:comparison to None"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1
        assert result[0].severity == Severity.MEDIUM

    def test_f4_import_error(self):
        """Test F4xx import errors are parsed."""
        analyzer = Flake8Analyzer()
        code = "import os\n"
        output = "1:1:F401:'os' imported but unused"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1
        assert result[0].severity == Severity.HIGH

    def test_f8_name_error(self):
        """Test F8xx name errors are parsed."""
        analyzer = Flake8Analyzer()
        code = "print(foo)\n"
        output = "1:7:F821:undefined name 'foo'"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1
        assert result[0].severity == Severity.HIGH

    def test_w_warning(self):
        """Test W warnings are parsed."""
        analyzer = Flake8Analyzer()
        code = "x = 1  \n"
        output = "1:6:W291:trailing whitespace"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1
        assert result[0].severity == Severity.LOW

    def test_c9_complexity(self):
        """Test C9xx complexity warnings are parsed."""
        analyzer = Flake8Analyzer()
        code = "def complex(): pass\n"
        output = "1:1:C901:'complex' is too complex (15)"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1
        assert result[0].severity == Severity.MEDIUM


class TestFlake8AnalyzerEdgeCases:
    """Tests for edge cases and error handling."""

    def test_analyze_empty_code(self):
        """Test analyzing empty code."""
        analyzer = Flake8Analyzer()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            result = analyzer.analyze("")
            assert result == []

    def test_parse_output_with_special_characters(self):
        """Test parsing output with special characters in message."""
        analyzer = Flake8Analyzer()
        code = "x = 1\n"
        output = "1:1:E501:line too long (contains 'quotes' and \"double quotes\")"
        result = analyzer._parse_output(output, code, "StyleAgent")
        assert len(result) == 1

    def test_analyze_unicode_code(self):
        """Test analyzing code with unicode characters."""
        analyzer = Flake8Analyzer()
        code = '# -*- coding: utf-8 -*-\n"""Módulo con caracteres especiales: áéíóú."""\n'
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            result = analyzer.analyze(code)
            assert isinstance(result, list)

    def test_finding_has_all_required_fields(self):
        """Test that findings have all required fields."""
        analyzer = Flake8Analyzer()
        code = "import os\n"

        flake8_output = "1:1:F401:'os' imported but unused"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=flake8_output, stderr="", returncode=1)
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
