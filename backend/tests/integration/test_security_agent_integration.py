"""
Integration tests for SecurityAgent.

Tests SecurityAgent with realistic vulnerable code samples
and verifies end-to-end behavior.
"""

import pytest

from src.agents.security_agent import SecurityAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Severity


class TestSecurityAgentIntegration:
    """Integration tests for SecurityAgent with realistic code."""

    @pytest.fixture
    def agent(self):
        """Create SecurityAgent instance."""
        return SecurityAgent()

    @pytest.fixture
    def vulnerable_web_app_code(self):
        """Realistic vulnerable web application code."""
        return """
import hashlib
import pickle
from flask import Flask, request

app = Flask(__name__)

# Hardcoded credentials
DB_PASSWORD = "MyDatabasePass123"
API_KEY = "sk_live_abc123xyz789"

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    if user:
        # Weak hashing
        session_token = hashlib.md5(username.encode()).hexdigest()
        return {'token': session_token}
    
    return {'error': 'Invalid credentials'}, 401

@app.route('/execute', methods=['POST'])
def execute_code():
    code = request.form['code']
    
    # Dangerous function - arbitrary code execution
    result = eval(code)
    
    return {'result': result}

@app.route('/load_data', methods=['POST'])
def load_data():
    data = request.form['data']
    
    # Unsafe deserialization
    obj = pickle.loads(data.encode())
    
    return {'loaded': str(obj)}
"""

    def test_comprehensive_vulnerability_detection(self, agent, vulnerable_web_app_code):
        """Test detection of all vulnerability types in realistic code."""
        context = AnalysisContext(code_content=vulnerable_web_app_code, filename="app.py")

        findings = agent.analyze(context)

        # Should detect multiple vulnerabilities
        assert len(findings) >= 5

        # Verify each vulnerability type is detected
        issue_types = {f.issue_type for f in findings}
        assert "hardcoded_credentials" in issue_types
        assert "sql_injection" in issue_types
        assert "weak_cryptography" in issue_types
        assert "dangerous_function" in issue_types

        # Verify severity distribution
        critical_count = sum(1 for f in findings if f.is_critical)
        high_count = sum(1 for f in findings if f.is_high_or_critical)

        assert critical_count >= 2  # Password, API key, eval
        assert high_count >= 4  # Including SQL injection

        # Verify findings have suggestions
        for finding in findings:
            assert finding.suggestion is not None
            assert len(finding.suggestion) > 10

        # Verify findings are sorted by severity
        severities = [f.severity.value for f in findings]
        expected_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

        for i in range(len(severities) - 1):
            assert expected_order.index(severities[i]) <= expected_order.index(severities[i + 1])

    def test_secure_code_no_false_positives(self, agent):
        """Test that secure code doesn't generate false positives."""
        secure_code = """
import os
import hashlib
from sqlalchemy import create_engine, text

# Secure credential handling
DB_PASSWORD = os.getenv('DB_PASSWORD')
API_KEY = os.getenv('API_KEY')

def authenticate_user(username: str, password: str) -> bool:
    # Parameterized query - safe from SQL injection
    query = text('SELECT * FROM users WHERE username=:username')
    result = db.execute(query, {'username': username})
    user = result.fetchone()
    
    if user:
        # Strong hashing with salt
        hashed = hashlib.sha256(
            (password + user['salt']).encode()
        ).hexdigest()
        return hashed == user['password_hash']
    
    return False

def process_data(data: dict) -> dict:
    # Safe data processing - no eval or exec
    processed = {
        'id': data.get('id'),
        'name': data.get('name'),
        'value': data.get('value', 0) * 2
    }
    return processed
"""
        context = AnalysisContext(code_content=secure_code, filename="secure_app.py")

        findings = agent.analyze(context)

        # Should have 0 findings for secure code
        assert len(findings) == 0

    def test_partial_vulnerability_file(self, agent):
        """Test file with mix of secure and vulnerable code."""
        mixed_code = """
import hashlib

# Secure part
def hash_file(filepath: str) -> str:
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

# Vulnerable part
def legacy_hash(data: str) -> str:
    # Old code - needs refactoring
    return hashlib.md5(data.encode()).hexdigest()

# Secure part
class Config:
    DATABASE_URL = os.getenv('DATABASE_URL')
    SECRET_KEY = os.getenv('SECRET_KEY')
"""
        context = AnalysisContext(code_content=mixed_code, filename="utils.py")

        findings = agent.analyze(context)

        # Should only detect MD5 usage
        assert len(findings) == 1
        assert findings[0].issue_type == "weak_cryptography"
        assert "md5" in findings[0].message.lower()
        assert findings[0].severity == Severity.MEDIUM

    def test_analysis_context_metadata_preserved(self, agent):
        """Test that analysis context metadata is preserved in findings."""
        code = "result = eval(user_input)"
        context = AnalysisContext(code_content=code, filename="vulnerable_script.py")
        context.add_metadata("user_id", "test_user_123")
        context.add_metadata("project", "SecurityTest")

        findings = agent.analyze(context)

        assert len(findings) >= 1
        # Verify agent name is set correctly
        for finding in findings:
            assert finding.agent_name == "SecurityAgent"
            assert finding.detected_at is not None

    def test_large_file_performance(self, agent):
        """Test SecurityAgent performance with larger file."""
        # Generate code with 100 functions
        large_code = """
import hashlib

"""
        for i in range(100):
            large_code += f"""
def function_{i}(data):
    # Safe function
    return hashlib.sha256(data.encode()).hexdigest()

"""

        # Add one vulnerability at the end
        large_code += """
# Single vulnerability
password = "HardcodedPassword123"
"""

        context = AnalysisContext(code_content=large_code, filename="large_module.py")

        findings = agent.analyze(context)

        # Should detect the single vulnerability
        assert len(findings) == 1
        assert findings[0].issue_type == "hardcoded_credentials"

        # Verify finding points to correct line
        assert "password" in findings[0].message.lower()
