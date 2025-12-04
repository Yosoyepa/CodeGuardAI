"""
Unit tests for PerformanceAgent.

Refactored to follow robust testing patterns from SecurityAgent and QualityAgent.
Tests cover:
1. Algorithmic complexity (O(n^2), O(n^3)) with thresholds.
2. Inefficient collections with false positive avoidance.
3. Resource leaks with isolation.
4. Robust error handling and edge cases.
"""

import pytest
from unittest.mock import MagicMock, patch
import ast

from src.agents.performance_agent import PerformanceAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Severity


class TestPerformanceAgentInitialization:
    """Test PerformanceAgent initialization and metadata."""

    def test_agent_initialization(self):
        """Test PerformanceAgent is created with correct attributes."""
        agent = PerformanceAgent()

        assert agent.name == "PerformanceAgent"
        assert agent.version == "1.1.0"
        assert agent.category == "performance"
        assert agent.enabled is True

    def test_agent_info(self):
        """Test get_info returns correct metadata."""
        agent = PerformanceAgent()
        info = agent.get_info()
        assert info["name"] == "PerformanceAgent"
        assert info["category"] == "performance"


class TestComplexityDetection:
    """Test detection of algorithmic complexity issues (O(n^2), O(n^3))."""

    @pytest.fixture
    def agent(self):
        return PerformanceAgent()

    def test_detect_nested_loops_high(self, agent):
        """Test detection of double nested loops (O(n^2))."""
        code = """
def process_data(items):
    for i in items:
        for j in items:
            print(i, j)
"""
        context = AnalysisContext(code_content=code, filename="complexity_high.py")
        findings = agent.analyze(context)

        finding = next((f for f in findings if f.issue_type == "performance/complexity"), None)
        assert finding is not None
        # Double nested loop is typically Critical or High depending on strictness
        assert finding.severity in [Severity.HIGH, Severity.CRITICAL]
        assert "O(n^2)" in finding.message
        assert finding.rule_id == "PERF001_NESTED_LOOPS"

    def test_detect_triple_nested_loops_critical(self, agent):
        """Test detection of triple nested loops (O(n^3)) -> CRITICAL severity."""
        code = """
def process_matrix(matrix):
    for i in range(10):
        for j in range(10):
            for k in range(10):
                print(matrix[i][j][k])
"""
        context = AnalysisContext(code_content=code, filename="complexity_critical.py")
        findings = agent.analyze(context)

        finding = next((f for f in findings if f.issue_type == "performance/complexity"), None)
        assert finding is not None
        assert finding.severity == Severity.CRITICAL
        assert "O(n^3)" in finding.message

    def test_ignore_single_loops(self, agent):
        """Test that sequential loops are not flagged."""
        code = """
def linear_process(items):
    for i in items:
        print(i)
    for j in items:
        print(j)
"""
        context = AnalysisContext(code_content=code, filename="linear.py")
        findings = agent.analyze(context)
        complexity_findings = [f for f in findings if f.issue_type == "performance/complexity"]
        assert len(complexity_findings) == 0


class TestInefficientCollections:
    """Test detection of inefficient collection operations and false positives."""

    @pytest.fixture
    def agent(self):
        return PerformanceAgent()

    def test_detect_list_insert_zero(self, agent):
        """Test detection of list.insert(0, item) inside a loop."""
        code = """
def build_list(items):
    result = []
    for item in items:
        result.insert(0, item)
    return result
"""
        context = AnalysisContext(code_content=code, filename="collections.py")
        findings = agent.analyze(context)

        finding = next((f for f in findings if "insert(0)" in f.message or "insert" in f.code_snippet), None)
        assert finding is not None
        assert finding.severity == Severity.HIGH
        assert finding.rule_id == "PERF002_LIST_INSERT"

    def test_detect_search_in_list_in_loop(self, agent):
        """Test detection of 'in list' search inside a loop."""
        code = """
def filter_items(items, whitelist_list):
    result = []
    for item in items:
        if item in whitelist_list:
            result.append(item)
    return result
"""
        context = AnalysisContext(code_content=code, filename="search.py")
        findings = agent.analyze(context)

        finding = next((f for f in findings if "Búsqueda lineal" in f.message), None)
        assert finding is not None
        assert finding.severity == Severity.MEDIUM
        assert finding.rule_id == "PERF002_LINEAR_SEARCH"

    def test_false_positive_set_lookup(self, agent):
        """Test that 'in set' search inside a loop is NOT flagged (O(1))."""
        code = """
def filter_fast(items, whitelist_set):
    # whitelist_set implies it's a set via heuristic
    result = []
    for item in items:
        if item in whitelist_set:
            result.append(item)
    return result
"""
        context = AnalysisContext(code_content=code, filename="fast_search.py")
        findings = agent.analyze(context)
        
        search_findings = [f for f in findings if "Búsqueda lineal" in f.message]
        assert len(search_findings) == 0

    def test_false_positive_dict_lookup(self, agent):
        """Test that 'in dict' search inside a loop is NOT flagged (O(1))."""
        code = """
def check_map(items, user_map):
    for item in items:
        if item in user_map:
            pass
"""
        context = AnalysisContext(code_content=code, filename="dict_search.py")
        findings = agent.analyze(context)
        search_findings = [f for f in findings if "Búsqueda lineal" in f.message]
        assert len(search_findings) == 0


class TestResourceLeaks:
    """Test detection of resource leaks and proper isolation."""

    @pytest.fixture
    def agent(self):
        return PerformanceAgent()

    def test_detect_open_without_with(self, agent):
        """Test detection of open() called without context manager."""
        code = """
def read_file(path):
    f = open(path, 'r')
    content = f.read()
    f.close()
"""
        context = AnalysisContext(code_content=code, filename="leaks.py")
        findings = agent.analyze(context)

        finding = next((f for f in findings if f.issue_type == "performance/resource-leak"), None)
        assert finding is not None
        assert finding.severity == Severity.HIGH
        assert "with" in finding.suggestion
        assert finding.rule_id == "PERF003_RESOURCE_LEAK"

    def test_ignore_open_with_context_manager(self, agent):
        """Test that open() inside with statement is accepted."""
        code = """
def read_safe(path):
    with open(path, 'r') as f:
        return f.read()
"""
        context = AnalysisContext(code_content=code, filename="safe_io.py")
        findings = agent.analyze(context)

        leak_findings = [f for f in findings if f.issue_type == "performance/resource-leak"]
        assert len(leak_findings) == 0

    def test_detect_n_plus_one_query(self, agent):
        """Test detection of N+1 query problem."""
        code = """
def process_users(user_ids):
    for uid in user_ids:
        # N+1 problem: Query inside loop
        db.execute("SELECT * FROM users WHERE id = ?", uid)
"""
        context = AnalysisContext(code_content=code, filename="db_perf.py")
        findings = agent.analyze(context)

        finding = next((f for f in findings if f.issue_type == "performance/database"), None)
        assert finding is not None
        assert finding.severity == Severity.CRITICAL
        assert "N+1 Query" in finding.message
        assert finding.rule_id == "PERF004_N_PLUS_ONE"


class TestErrorHandling:
    """Test robust error handling (Pattern from QualityAgent)."""

    @pytest.fixture
    def agent(self):
        return PerformanceAgent()

    def test_syntax_error_handling(self, agent):
        """Test that syntax errors in code do not crash the agent."""
        code = "def broken_code(:"  # Syntax error
        context = AnalysisContext(code_content=code, filename="broken.py")
        
        # Should not raise exception
        findings = agent.analyze(context)
        
        # Should return empty list or list with syntax error finding
        assert isinstance(findings, list)

    def test_generic_exception_handling(self, agent):
        """Test handling of unexpected exceptions during analysis."""
        context = AnalysisContext(code_content="pass", filename="test.py")
        
        # Mock ast.parse to raise generic exception
        with patch("ast.parse", side_effect=Exception("Unexpected AST failure")):
            findings = agent.analyze(context)
            
            # Should handle gracefully and return empty list
            assert findings == []

    def test_visitor_exception_handling(self, agent):
        """Test exception handling within the visitor traversal."""
        code = "x = 1"
        context = AnalysisContext(code_content=code, filename="test.py")
        
        # Mock the visitor's visit method to raise exception
        with patch("src.agents.performance_agent.PerformanceVisitor.visit", side_effect=Exception("Visitor Error")):
            findings = agent.analyze(context)
            # Should catch and return empty or partial findings
            assert findings == []


class TestOptimizedCode:
    """Test that perfectly optimized code generates zero findings (Pattern from SecurityAgent)."""

    @pytest.fixture
    def agent(self):
        return PerformanceAgent()

    def test_optimized_code_no_findings(self, agent):
        """Test a complex but optimized code block."""
        code = """
import collections

def process_efficiently(data_list, lookup_set):
    # Use deque for O(1) appends on both ends
    queue = collections.deque()
    
    # Single loop O(n)
    for item in data_list:
        # Set lookup O(1)
        if item in lookup_set:
            queue.append(item)
            
    # Context manager for resources
    with open("output.txt", "w") as f:
        while queue:
            f.write(str(queue.popleft()) + "\\n")
            
    return True
"""
        context = AnalysisContext(code_content=code, filename="optimized.py")
        findings = agent.analyze(context)
        
        assert len(findings) == 0
