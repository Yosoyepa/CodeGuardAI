"""
Unit tests for PerformanceAgent.

Tests cover detection of:
1. Algorithmic complexity issues (Nested loops O(n^2))
2. Inefficient collection operations (list.insert(0), in list inside loop)
3. Resource management issues (open without with)
"""

import pytest
from unittest.mock import MagicMock

from src.agents.performance_agent import PerformanceAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Severity


class TestPerformanceAgentInitialization:
    """Test PerformanceAgent initialization."""

    def test_agent_initialization(self):
        """Test PerformanceAgent is created with correct attributes."""
        agent = PerformanceAgent()

        assert agent.name == "PerformanceAgent"
        assert agent.version == "1.1.0"
        assert agent.category == "performance"
        assert agent.enabled is True


class TestComplexityDetection:
    """Test detection of algorithmic complexity issues (O(n^2))."""

    @pytest.fixture
    def agent(self):
        return PerformanceAgent()

    def test_detect_nested_loops_critical(self, agent):
        """Test detection of double nested loops (O(n^2))."""
        code = """
def process_data(items):
    for i in items:
        for j in items:
            print(i, j)
"""
        context = AnalysisContext(code_content=code, filename="complexity.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        finding = next(f for f in findings if f.issue_type == "performance/complexity")
        assert finding.severity == Severity.CRITICAL
        assert "complejidad O(n^2)" in finding.message
        assert finding.rule_id == "PERF001_NESTED_LOOPS"

    def test_detect_nested_loops_in_function(self, agent):
        """Test detection of nested loops inside a function."""
        code = """
class DataProcessor:
    def analyze(self, data):
        results = []
        for x in data:
            # Some comment
            for y in data:
                results.append(x + y)
        return results
"""
        context = AnalysisContext(code_content=code, filename="processor.py")
        findings = agent.analyze(context)

        finding = next(f for f in findings if f.issue_type == "performance/complexity")
        # The finding points to the inner loop (the one causing the nesting)
        # Line 1: empty, 2: class, 3: def, 4: results, 5: for x, 6: comment, 7: for y
        assert finding.line_number == 7
        assert "O(n^2)" in finding.message

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
    """Test detection of inefficient collection operations."""

    @pytest.fixture
    def agent(self):
        return PerformanceAgent()

    def test_detect_list_insert_zero(self, agent):
        """Test detection of list.insert(0, item) inside a loop."""
        code = """
def build_list(items):
    result = []
    for item in items:
        result.insert(0, item)  # Inefficient O(n) inside loop -> O(n^2)
    return result
"""
        context = AnalysisContext(code_content=code, filename="collections.py")
        findings = agent.analyze(context)

        finding = next(f for f in findings if "insert(0)" in f.message or "insert" in f.code_snippet)
        assert finding.severity == Severity.HIGH
        assert finding.issue_type == "performance/inefficient-operation"
        assert finding.rule_id == "PERF002_LIST_INSERT"

    def test_detect_search_in_list_in_loop(self, agent):
        """Test detection of 'in list' search inside a loop."""
        code = """
def filter_items(items, whitelist_list):
    result = []
    for item in items:
        if item in whitelist_list:  # O(n) search inside loop -> O(n^2)
            result.append(item)
    return result
"""
        context = AnalysisContext(code_content=code, filename="search.py")
        findings = agent.analyze(context)

        finding = next(f for f in findings if "Búsqueda lineal" in f.message)
        assert finding.severity == Severity.MEDIUM
        assert finding.rule_id == "PERF002_LINEAR_SEARCH"

    def test_ignore_search_outside_loop(self, agent):
        """Test that searching in list outside loop is ignored."""
        code = """
if x in my_list:
    print("found")
"""
        context = AnalysisContext(code_content=code, filename="fast_search.py")
        findings = agent.analyze(context)

        search_findings = [f for f in findings if "Búsqueda lineal" in f.message]
        assert len(search_findings) == 0


class TestResourceLeaks:
    """Test detection of resource leaks (open without with)."""

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

        finding = next(f for f in findings if f.issue_type == "performance/resource-leak")
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

        finding = next(f for f in findings if f.issue_type == "performance/database")
        assert finding.severity == Severity.CRITICAL
        assert "N+1 Query" in finding.message
        assert finding.rule_id == "PERF004_N_PLUS_ONE"

    def test_detect_memory_intensive_read(self, agent):
        """Test detection of unbounded read()."""
        code = """
def load_file(path):
    with open(path, 'r') as f:
        # Unbounded read
        data = f.read()
        return data
"""
        context = AnalysisContext(code_content=code, filename="memory.py")
        findings = agent.analyze(context)

        finding = next(f for f in findings if f.issue_type == "performance/memory")
        assert finding.severity == Severity.HIGH
        assert "memoria intensiva" in finding.message
        assert finding.rule_id == "PERF005_UNBOUNDED_MEMORY"

    def test_detect_socket_leak(self, agent):
        """Test detection of socket leak."""
        code = """
import socket
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 80))
"""
        context = AnalysisContext(code_content=code, filename="net.py")
        findings = agent.analyze(context)

        finding = next(f for f in findings if f.issue_type == "performance/resource-leak")
        assert "socket" in finding.message
        assert finding.rule_id == "PERF003_RESOURCE_LEAK" 
