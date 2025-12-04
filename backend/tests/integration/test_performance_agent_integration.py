"""
Integration tests for PerformanceAgent.

Tests PerformanceAgent with realistic inefficient code samples
and verifies end-to-end behavior.
"""

import pytest
import time

from src.agents.performance_agent import PerformanceAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Severity


class TestPerformanceAgentIntegration:
    """Integration tests for PerformanceAgent with realistic code."""

    @pytest.fixture
    def agent(self):
        """Create PerformanceAgent instance."""
        return PerformanceAgent()

    @pytest.fixture
    def inefficient_data_processing_code(self):
        """Realistic inefficient data processing code."""
        return """
import socket
import time

def process_large_dataset(users, transactions):
    results = []
    
    # 1. Nested loops (O(n^2)) - Critical
    # Comparing every user with every transaction
    for user in users:
        for tx in transactions:
            if user['id'] == tx['user_id']:
                results.append({'user': user, 'tx': tx})
                
    return results

def filter_allowed_items(items, allowed_list):
    filtered = []
    # 2. Linear search in loop - Medium
    for item in items:
        if item in allowed_list:  # O(n) inside loop -> O(n^2)
            filtered.append(item)
    return filtered

def export_logs(logs):
    # 3. Resource leak (File) - High
    f = open('export.log', 'w')
    for log in logs:
        f.write(str(log) + '\\n')
    # Missing close()
    
def check_server_status(host, port):
    # 4. Resource leak (Socket) - High
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(b'PING')
    response = s.recv(1024)
    return response

def update_user_stats(user_ids):
    # 5. N+1 Query - Critical
    for uid in user_ids:
        db.execute("SELECT * FROM stats WHERE user_id = ?", uid)

def terrible_complexity(data):
    # 6. Triple nested loop (O(n^3)) - Critical
    for i in data:
        for j in data:
            for k in data:
                print(i, j, k)
"""

    def test_comprehensive_performance_detection(self, agent, inefficient_data_processing_code):
        """Test detection of all performance issues in realistic code."""
        context = AnalysisContext(code_content=inefficient_data_processing_code, filename="data_processor.py")

        findings = agent.analyze(context)

        # Should detect multiple issues
        assert len(findings) >= 6

        # Verify each issue type is detected
        issue_types = {f.issue_type for f in findings}
        assert "performance/complexity" in issue_types  # Nested loops
        assert "performance/inefficient-operation" in issue_types  # Linear search
        assert "performance/resource-leak" in issue_types  # File and Socket
        assert "performance/database" in issue_types  # N+1

        # Verify severity distribution
        critical_count = sum(1 for f in findings if f.is_critical)
        high_count = sum(1 for f in findings if f.is_high_or_critical)

        assert critical_count >= 2  # Triple nested loops, N+1
        assert high_count >= 5  # + Double nested loops, File leak, Socket leak

        # Verify findings have suggestions
        for finding in findings:
            assert finding.suggestion is not None
            assert len(finding.suggestion) > 10

        # Verify findings are sorted by severity
        severities = [f.severity.value for f in findings]
        expected_order = ["critical", "high", "medium", "low", "info"]
        
        # Check if sorted correctly (indices in expected_order should be non-decreasing)
        indices = [expected_order.index(s) for s in severities]
        assert indices == sorted(indices)

    def test_optimized_code_no_false_positives(self, agent):
        """Test that optimized code doesn't generate false positives."""
        optimized_code = """
def process_efficiently(users, transactions):
    # Optimized: Use dictionary for O(1) lookup
    user_map = {u['id']: u for u in users}
    results = []
    
    for tx in transactions:
        if tx['user_id'] in user_map:
            results.append({'user': user_map[tx['user_id']], 'tx': tx})
            
    return results

def save_safely(data):
    # Safe resource usage
    with open('data.txt', 'w') as f:
        f.write(data)

def get_stats_batch(user_ids):
    # Optimized: Batch query
    placeholders = ','.join(['?'] * len(user_ids))
    query = f"SELECT * FROM stats WHERE user_id IN ({placeholders})"
    db.execute(query, user_ids)
"""
        context = AnalysisContext(code_content=optimized_code, filename="optimized.py")

        findings = agent.analyze(context)

        # Should have 0 findings for optimized code
        assert len(findings) == 0

    def test_mixed_performance_file(self, agent):
        """Test file with mix of efficient and inefficient code."""
        mixed_code = """
def good_function():
    with open('test.txt', 'r') as f:
        return f.read(1024)  # Safe read with limit

def bad_function(items):
    # Inefficient insert
    result = []
    for item in items:
        result.insert(0, item)  # O(n) inside loop
    return result
"""
        context = AnalysisContext(code_content=mixed_code, filename="mixed.py")

        findings = agent.analyze(context)

        # Should only detect the inefficient insert
        assert len(findings) == 1
        assert findings[0].rule_id == "PERF002_LIST_INSERT"
        assert findings[0].severity == Severity.HIGH

    def test_analysis_context_metadata_preserved(self, agent):
        """Test that analysis context metadata is preserved in findings."""
        code = """
def leak():
    f = open('leak.txt')
"""
        context = AnalysisContext(code_content=code, filename="leak.py")
        context.add_metadata("module", "legacy_io")

        findings = agent.analyze(context)

        assert len(findings) >= 1
        for finding in findings:
            assert finding.agent_name == "PerformanceAgent"
            assert finding.detected_at is not None

    def test_large_file_performance(self, agent):
        """Test PerformanceAgent performance with larger file."""
        # Generate code with 500 simple functions
        lines = ["def safe_function():"]
        for i in range(500):
            lines.append(f"    x_{i} = {i} * 2")
        lines.append("    return x_499")
        
        code_content = "\n".join(lines)
        
        context = AnalysisContext(code_content=code_content, filename="large_clean.py")
        
        start_time = time.time()
        findings = agent.analyze(context)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should be fast
        assert execution_time < 1.0
        assert len(findings) == 0
