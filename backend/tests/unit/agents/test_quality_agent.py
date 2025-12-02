from unittest.mock import MagicMock, patch

import pytest

from src.agents.quality_agent import QualityAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding, Severity


class TestQualityAgent:
    """Test suite for QualityAgent."""

    @pytest.fixture
    def mock_event_bus(self):
        """Mock the EventBus."""
        return MagicMock()

    @pytest.fixture
    def agent(self, mock_event_bus):
        """Create QualityAgent instance."""
        return QualityAgent(event_bus=mock_event_bus)

    def test_analyze_quality_metrics(self, agent, mock_event_bus):
        """Test detection of all quality metrics (Happy Path)."""
        code = """
def complex_function(x):
    pass
"""
        context = AnalysisContext(code_content=code, filename="quality_test.py")

        # Mock Radon Complexity
        with patch("src.agents.quality_agent.radon_visit") as mock_radon_visit, \
             patch("src.agents.quality_agent.mi_visit") as mock_mi_visit:
            
            mock_func = MagicMock()
            mock_func.name = "complex_function"
            mock_func.complexity = 15
            mock_func.lineno = 2
            mock_radon_visit.return_value = [mock_func]

            # Mock Radon Maintainability
            mock_mi_visit.return_value = 40.0

            findings = agent.analyze(context)

            assert mock_event_bus.publish.called
            issue_types = [f.issue_type for f in findings]
            assert "quality/cyclomatic-complexity" in issue_types
            assert "quality/maintainability-index" in issue_types

    def test_measure_function_length(self, agent):
        """Test specifically function length detection."""
        # Create a valid python code with a long function
        code = "def long_func():\n" + "\n".join([f"    x = {i}" for i in range(105)])
        import ast

        tree = ast.parse(code)
        findings = agent.measure_function_length(tree)
        assert len(findings) == 1
        assert findings[0].issue_type == "quality/function-length"
        assert "105" in findings[0].message or "106" in findings[0].message

    def test_calculate_maintainability_index(self, agent):
        """Test MI calculation."""
        with patch("src.agents.quality_agent.mi_visit") as mock_mi:
            mock_mi.return_value = 30.0
            score = agent.calculate_maintainability_index("some code")
            assert score == 30.0

    def test_syntax_error_handling(self, agent):
        """Test handling of syntax errors in AST parsing."""
        context = AnalysisContext(code_content="def broken_code(", filename="error.py")
        findings = agent.analyze(context)
        assert len(findings) == 0

    def test_complexity_thresholds(self, agent):
        """Test different complexity thresholds (High/Critical)."""
        import ast

        tree = ast.parse("def foo(): pass")

        with patch("src.agents.quality_agent.radon_visit") as mock_radon_visit:
            # Case 1: Critical (> 50)
            mock_crit = MagicMock()
            mock_crit.name = "crit_func"
            mock_crit.complexity = 51
            mock_crit.lineno = 1

            # Case 2: High (> 20)
            mock_high = MagicMock()
            mock_high.name = "high_func"
            mock_high.complexity = 21
            mock_high.lineno = 5

            mock_radon_visit.return_value = [mock_crit, mock_high]

            findings = agent.calculate_complexity(tree)

            assert len(findings) == 2
            severities = [f.severity for f in findings]
            assert Severity.CRITICAL in severities
            assert Severity.HIGH in severities

    def test_maintainability_critical(self, agent):
        """Test critical maintainability index."""
        # Use valid code so AST parsing succeeds
        context = AnalysisContext(code_content="def foo(): pass", filename="test.py")

        with patch("src.agents.quality_agent.mi_visit") as mock_mi, \
             patch("src.agents.quality_agent.radon_visit", return_value=[]):
            
            # Mock MI < 20
            mock_mi.return_value = 10.0

            findings = agent.analyze(context)
            mi_finding = next(
                (f for f in findings if f.issue_type == "quality/maintainability-index"), None
            )
            assert mi_finding is not None
            assert mi_finding.severity == Severity.CRITICAL

    def test_short_file_duplication(self, agent):
        """Test that short files skip duplication check."""
        code = "print('hello')\n" * 2
        findings = agent.detect_code_duplication(code)
        assert len(findings) == 0

    def test_code_duplication_detected(self, agent):
        """Test detection of duplicated code blocks."""
        # Create code with duplication
        # Block size is 4 lines. We need a block of 4 lines repeated.
        block = "x = 1\ny = 2\nz = 3\nw = 4\n"
        code = block + "a = 0\n" + block

        findings = agent.detect_code_duplication(code)
        assert len(findings) > 0
        assert findings[0].issue_type == "quality/duplication"
        assert "Bloque de código duplicado" in findings[0].message

    def test_radon_not_installed(self, agent):
        """Test behavior when radon is not installed."""
        with patch("src.agents.quality_agent.radon_visit", None), \
             patch("src.agents.quality_agent.mi_visit", None):

            findings_cc = agent.calculate_complexity(MagicMock())
            assert len(findings_cc) == 0

            score = agent.calculate_maintainability_index("code")
            assert score == 100.0

    def test_exception_handling_in_analyze(self, agent):
        """Test global exception handling in analyze method."""
        context = AnalysisContext(code_content="code", filename="test.py")
        with patch("ast.parse", side_effect=Exception("Unexpected error")):
            findings = agent.analyze(context)
            assert len(findings) == 0

    def test_exception_in_complexity_calculation(self, agent):
        """Test exception handling inside calculate_complexity."""
        with patch("src.agents.quality_agent.radon_visit") as mock_radon:
            mock_radon.side_effect = Exception("Radon error")
            findings = agent.calculate_complexity(MagicMock())
            assert len(findings) == 0

    def test_mi_visit_exception(self, agent):
        """Test exception inside calculate_maintainability_index."""
        with patch("src.agents.quality_agent.mi_visit") as mock_mi:
            mock_mi.side_effect = Exception("MI Error")
            score = agent.calculate_maintainability_index("code")
            assert score == 100.0

    def test_duplication_with_comments(self, agent):
        """Test that comments are ignored in duplication check."""
        # Block of comments
        comments = "# comment\n" * 5
        findings = agent.detect_code_duplication(comments)
        assert len(findings) == 0
