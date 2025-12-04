"""
Integration tests for QualityAgent.

Tests QualityAgent with realistic code samples
and verifies end-to-end behavior for code quality metrics.
"""

import pytest

from src.agents.quality_agent import QualityAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Severity


class TestQualityAgentIntegration:
    """Integration tests for QualityAgent with realistic code."""

    @pytest.fixture
    def agent(self):
        """Create QualityAgent instance."""
        return QualityAgent()

    @pytest.fixture
    def poor_quality_code(self):
        """Realistic poor quality code with multiple issues."""
        return """
def complex_and_long_function(data):
    # High Cyclomatic Complexity
    result = []
    if data:
        for item in data:
            if item.get('active'):
                if item.get('type') == 'A':
                    if item.get('value') > 10:
                        result.append(item)
                    else:
                        print("Value too low")
                elif item.get('type') == 'B':
                    if item.get('value') > 20:
                        result.append(item)
                else:
                    if item.get('force'):
                        result.append(item)
            else:
                if item.get('retry'):
                    process_retry(item)
                elif item.get('fail'):
                    log_failure(item)
                elif item.get('warn'):
                    log_warning(item)
    
    # Code Duplication Block 1
    x = 0
    y = 0
    z = 0
    for i in range(10):
        x += i
        y += i * 2
        z += i * 3
    print(f"Result: {x}, {y}, {z}")

    # Code Duplication Block 2 (Identical to Block 1)
    x = 0
    y = 0
    z = 0
    for i in range(10):
        x += i
        y += i * 2
        z += i * 3
    print(f"Result: {x}, {y}, {z}")

    return result

def another_complex_function(x, y):
    # Another complex function to ensure multiple findings
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    else:
        if y > 0:
            return y - x
        else:
            return -x - y
"""

    def test_comprehensive_quality_detection(self, agent, poor_quality_code):
        """Test detection of all quality issues in realistic code."""
        context = AnalysisContext(code_content=poor_quality_code, filename="legacy_module.py")

        findings = agent.analyze(context)

        # Should detect multiple quality issues
        # 1. Complexity (complex_and_long_function)
        # 2. Duplication
        # 3. Maintainability (likely low due to complexity)
        assert len(findings) >= 3

        # Verify each issue type is detected
        issue_types = {f.issue_type for f in findings}

        # Note: Depending on the exact complexity score, it might be medium or high
        assert "quality/cyclomatic-complexity" in issue_types
        assert "quality/duplication" in issue_types

        # Verify severity distribution
        # Complexity > 10 is Medium, > 20 is High. The sample code is moderately complex.
        # Duplication is Medium.

        # Verify findings have suggestions
        for finding in findings:
            assert finding.suggestion is not None
            assert len(finding.suggestion) > 5

        # Verify findings are sorted by severity
        severities = [f.severity.value for f in findings]
        expected_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

        for i in range(len(severities) - 1):
            assert expected_order.index(severities[i]) <= expected_order.index(severities[i + 1])

    def test_clean_code_no_false_positives(self, agent):
        """Test that clean code doesn't generate false positives."""
        clean_code = '''
def calculate_total(items: list) -> float:
    """Calculate total price of items."""
    return sum(item.price for item in items)

def filter_active_items(items: list) -> list:
    """Return only active items."""
    return [item for item in items if item.is_active]

class UserProcessor:
    def __init__(self, user_service):
        self.user_service = user_service

    def process(self, user_id: int):
        user = self.user_service.get_user(user_id)
        if user and user.is_active:
            return self._handle_active_user(user)
        return None

    def _handle_active_user(self, user):
        return {"status": "processed", "id": user.id}
'''
        context = AnalysisContext(code_content=clean_code, filename="clean_module.py")

        findings = agent.analyze(context)

        # Should have 0 findings for clean code
        # Complexity is low, functions are short, no duplication
        assert len(findings) == 0

    def test_long_function_detection(self, agent):
        """Test specifically for function length."""
        # Generate a function with > 100 lines
        long_code = "def very_long_function():\n"
        for i in range(105):
            long_code += f"    var_{i} = {i}\n"
        long_code += "    return var_100\n"

        context = AnalysisContext(code_content=long_code, filename="long_func.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        assert findings[0].issue_type == "quality/function-length"
        assert "demasiado larga" in findings[0].message.lower()

    def test_analysis_context_metadata_preserved(self, agent):
        """Test that analysis context metadata is preserved in findings."""
        # Generate code with high complexity to trigger a finding
        bad_code = "def complex_func(x):\n"
        for i in range(20):
            bad_code += f"    if x == {i}: return {i}\n"

        context = AnalysisContext(code_content=bad_code, filename="complex.py")
        context.add_metadata("user_id", "dev_user")

        findings = agent.analyze(context)
        assert len(findings) > 0
        for finding in findings:
            assert finding.agent_name == "QualityAgent"

    def test_large_file_performance(self, agent):
        """Test QualityAgent performance with larger file."""
        # Generate code with 50 simple functions
        large_code = ""
        for i in range(50):
            large_code += f"""
def function_{i}(data):
    return data * {i}
"""
        # Add a duplicated block at the end
        dupe_block = """
def duplicated_logic():
    x = 1
    y = 2
    z = 3
    return x + y + z
"""
        large_code += dupe_block
        large_code += dupe_block  # Duplication

        context = AnalysisContext(code_content=large_code, filename="large_module.py")

        findings = agent.analyze(context)

        # Should detect the duplication
        dupe_findings = [f for f in findings if f.issue_type == "quality/duplication"]
        assert len(dupe_findings) >= 1
