"""
Unit tests for SecurityAgent.

Tests cover all 4 detection modules:
1. Dangerous functions detection
2. SQL injection detection
3. Hardcoded credentials detection
4. Weak cryptography detection
"""

import pytest

from src.agents.security_agent import SecurityAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Severity


class TestSecurityAgentInitialization:
    """Test SecurityAgent initialization."""

    def test_agent_initialization(self):
        """Test SecurityAgent is created with correct attributes."""
        agent = SecurityAgent()

        assert agent.name == "SecurityAgent"
        assert agent.version == "1.0.0"
        assert agent.category == "security"
        assert agent.is_enabled() is True

    def test_agent_info(self):
        """Test get_info returns correct metadata."""
        agent = SecurityAgent()
        info = agent.get_info()

        assert info["name"] == "SecurityAgent"
        assert info["category"] == "security"


class TestDangerousFunctionsDetection:
    """Test detection of dangerous functions."""

    @pytest.fixture
    def agent(self):
        """Create SecurityAgent instance."""
        return SecurityAgent()

    def test_detect_eval_function(self, agent):
        """Test detection of eval() function."""
        code = """
result = eval(user_input)
print(result)
"""
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        eval_finding = next(f for f in findings if "eval" in f.message.lower())
        assert eval_finding.severity == Severity.CRITICAL
        assert eval_finding.issue_type == "dangerous_function"
        assert eval_finding.line_number == 2
        assert "ast.literal_eval" in eval_finding.suggestion
        assert eval_finding.rule_id == "SEC001_EVAL"

    def test_detect_exec_function(self, agent):
        """Test detection of exec() function."""
        code = "exec(malicious_code)"
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        exec_finding = next(f for f in findings if "exec" in f.message.lower())
        assert exec_finding.severity == Severity.CRITICAL
        assert exec_finding.issue_type == "dangerous_function"
        assert "validate input" in exec_finding.suggestion.lower()

    def test_detect_compile_function(self, agent):
        """Test detection of compile() function."""
        code = "compiled = compile(source, 'file', 'exec')"
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        compile_finding = next(f for f in findings if "compile" in f.message.lower())
        assert compile_finding.severity == Severity.CRITICAL

    def test_detect_pickle_loads(self, agent):
        """Test detection of pickle.loads()."""
        code = """
import pickle
data = pickle.loads(untrusted_data)
"""
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        pickle_finding = next(
            f
            for f in findings
            if "pickle" in f.message.lower() or "deserialization" in f.issue_type
        )
        assert pickle_finding.severity == Severity.HIGH
        assert "json.loads" in pickle_finding.suggestion

    def test_no_false_positives_for_safe_functions(self, agent):
        """Test that safe functions don't trigger findings."""
        code = """
def evaluate_math(a, b):
    return a + b

result = evaluate_math(5, 3)
"""
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        # Should have 0 findings for this safe code
        assert len(findings) == 0


class TestSQLInjectionDetection:
    """Test detection of SQL injection vulnerabilities."""

    @pytest.fixture
    def agent(self):
        """Create SecurityAgent instance."""
        return SecurityAgent()

    def test_detect_string_concatenation_sql(self, agent):
        """Test detection of SQL injection via string concatenation."""
        code = 'cursor.execute("SELECT * FROM users WHERE id=" + user_id)'
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        sql_finding = next(f for f in findings if f.issue_type == "sql_injection")
        assert sql_finding.severity == Severity.HIGH
        assert "parameterized" in sql_finding.suggestion.lower()
        assert sql_finding.rule_id == "SEC002_SQL_INJECTION"

    def test_detect_fstring_sql_injection(self, agent):
        """Test detection of SQL injection via f-strings."""
        code = "query = f\"DELETE FROM logs WHERE date < '{cutoff}'\"\ncursor.execute(query)"
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        sql_finding = next(f for f in findings if f.issue_type == "sql_injection")
        assert sql_finding.severity == Severity.HIGH

    def test_detect_percent_formatting_sql(self, agent):
        """Test detection of SQL injection via %s formatting."""
        code = "cursor.execute('SELECT * FROM users WHERE name=%s' % username)"
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        sql_finding = next(f for f in findings if f.issue_type == "sql_injection")
        assert sql_finding.severity == Severity.HIGH

    def test_no_false_positives_for_safe_queries(self, agent):
        """Test that parameterized queries don't trigger findings."""
        code = """
cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
cursor.execute('INSERT INTO logs VALUES (?, ?)', (timestamp, message))
"""
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        # Should have 0 SQL injection findings
        sql_findings = [f for f in findings if f.issue_type == "sql_injection"]
        assert len(sql_findings) == 0


class TestHardcodedCredentialsDetection:
    """Test detection of hardcoded credentials."""

    @pytest.fixture
    def agent(self):
        """Create SecurityAgent instance."""
        return SecurityAgent()

    def test_detect_hardcoded_password(self, agent):
        """Test detection of hardcoded password."""
        code = 'password = "MySecretPass123"'
        context = AnalysisContext(code_content=code, filename="config.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        pwd_finding = next(
            f
            for f in findings
            if f.issue_type == "hardcoded_credentials" and "password" in f.message.lower()
        )
        assert pwd_finding.severity == Severity.CRITICAL
        assert "environment variable" in pwd_finding.suggestion.lower()
        assert "SEC003_PASSWORD" in pwd_finding.rule_id

    def test_detect_hardcoded_api_key(self, agent):
        """Test detection of hardcoded API key."""
        code = 'api_key = "sk_live_abc123xyz789"'
        context = AnalysisContext(code_content=code, filename="config.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        api_finding = next(
            f
            for f in findings
            if f.issue_type == "hardcoded_credentials" and "api" in f.message.lower()
        )
        assert api_finding.severity == Severity.CRITICAL

    def test_detect_hardcoded_token(self, agent):
        """Test detection of hardcoded token."""
        code = 'auth_token = "ghp_abc123xyz789012345"'
        context = AnalysisContext(code_content=code, filename="auth.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        token_finding = next(
            f
            for f in findings
            if f.issue_type == "hardcoded_credentials" and "token" in f.message.lower()
        )
        assert token_finding.severity == Severity.HIGH

    def test_ignore_placeholders(self, agent):
        """Test that placeholders are not flagged as credentials."""
        code = """
password = "YOUR_PASSWORD_HERE"
api_key = "REPLACE_WITH_YOUR_API_KEY"
token = "TODO: Add token"
secret = "example_secret"
"""
        context = AnalysisContext(code_content=code, filename="config.py")
        findings = agent.analyze(context)

        # Should have 0 findings for placeholders
        cred_findings = [f for f in findings if f.issue_type == "hardcoded_credentials"]
        assert len(cred_findings) == 0

    def test_ignore_short_values(self, agent):
        """Test that very short values are not flagged."""
        code = 'password = "abc"'
        context = AnalysisContext(code_content=code, filename="test.py")
        findings = agent.analyze(context)

        # Should not flag very short passwords
        cred_findings = [f for f in findings if f.issue_type == "hardcoded_credentials"]
        assert len(cred_findings) == 0


class TestWeakCryptographyDetection:
    """Test detection of weak cryptographic algorithms."""

    @pytest.fixture
    def agent(self):
        """Create SecurityAgent instance."""
        return SecurityAgent()

    def test_detect_md5_usage(self, agent):
        """Test detection of MD5 hash algorithm."""
        code = """
import hashlib
hash_value = hashlib.md5(data).hexdigest()
"""
        context = AnalysisContext(code_content=code, filename="crypto.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        md5_finding = next(
            f
            for f in findings
            if f.issue_type == "weak_cryptography" and "md5" in f.message.lower()
        )
        assert md5_finding.severity == Severity.MEDIUM
        assert "SHA-256" in md5_finding.suggestion
        assert md5_finding.rule_id == "SEC004_MD5"

    def test_detect_sha1_usage(self, agent):
        """Test detection of SHA1 hash algorithm."""
        code = """
                import hashlib
                digest = hashlib.sha1(message.encode()).digest()
               """
        context = AnalysisContext(code_content=code, filename="hasher.py")
        findings = agent.analyze(context)

        assert len(findings) >= 1
        sha1_finding = next(
            f
            for f in findings
            if f.issue_type == "weak_cryptography" and "sha1" in f.message.lower()
        )
        assert sha1_finding.severity == Severity.MEDIUM

    def test_safe_sha256_no_findings(self, agent):
        """Test that SHA-256 doesn't trigger findings."""
        code = """
                import hashlib
                secure_hash = hashlib.sha256(data).hexdigest()
               """
        context = AnalysisContext(code_content=code, filename="secure.py")
        findings = agent.analyze(context)

        # Should have 0 weak crypto findings for SHA-256
        crypto_findings = [f for f in findings if f.issue_type == "weak_cryptography"]
        assert len(crypto_findings) == 0


class TestComplexScenarios:
    """Test complex scenarios with multiple vulnerabilities."""

    @pytest.fixture
    def agent(self):
        """Create SecurityAgent instance."""
        return SecurityAgent()

    def test_multiple_vulnerabilities_in_one_file(self, agent):
        """Test detection of multiple vulnerability types."""
        code = """
                import hashlib
                import pickle

                # Hardcoded credential
                password = "MySecretPassword123"
                api_key = "sk_live_abc123xyz"

                # Dangerous function
                def execute_command(user_input):
                    result = eval(user_input)
                    return result

                # SQL injection
                def query_user(user_id):
                    query = f"SELECT * FROM users WHERE id = {user_id}"
                    cursor.execute(query)
                    return cursor.fetchone()

                # Weak crypto
                def hash_password(pwd):
                    return hashlib.md5(pwd.encode()).hexdigest()

                # Unsafe deserialization
                def load_data(data):
                    return pickle.loads(data)
               """
        context = AnalysisContext(code_content=code, filename="vulnerable.py")
        findings = agent.analyze(context)

        # Should detect at least 6 vulnerabilities
        assert len(findings) >= 6

        # Verify each type is detected
        issue_types = {f.issue_type for f in findings}
        assert "hardcoded_credentials" in issue_types
        assert "dangerous_function" in issue_types
        assert "sql_injection" in issue_types
        assert "weak_cryptography" in issue_types

        # Verify CRITICAL findings are first (sorted by severity)
        critical_findings = [f for f in findings if f.is_critical]
        assert len(critical_findings) >= 2
        # First findings should be CRITICAL
        assert findings[0].severity == Severity.CRITICAL

    def test_syntax_error_handling(self, agent):
        """Test that syntax errors are handled gracefully."""
        code = """
                def incomplete_function(
                    # Missing closing parenthesis and body
               """
        context = AnalysisContext(code_content=code, filename="broken.py")

        # Should not raise exception, but log error
        findings = agent.analyze(context)

        # May have some findings from regex-based modules
        # Should not crash
        assert isinstance(findings, list)

    def test_empty_code(self, agent):
        """Test analysis of minimal valid code."""
        code = "# Just a comment\npass"
        context = AnalysisContext(code_content=code, filename="minimal.py")
        findings = agent.analyze(context)

        assert len(findings) == 0

    def test_findings_sorted_by_severity(self, agent):
        """Test that findings are sorted by severity."""
        code = """
                # MEDIUM severity issue
                import hashlib
                hash1 = hashlib.md5(data).hexdigest()

                # CRITICAL severity issue
                password = "SuperSecret123"

                # HIGH severity issue
                query = f"DELETE FROM users WHERE id={user_id}"
                cursor.execute(query)

                # CRITICAL severity issue
                result = eval(user_input)
                """
        context = AnalysisContext(code_content=code, filename="mixed.py")
        findings = agent.analyze(context)

        assert len(findings) >= 4

        # First findings should be CRITICAL
        for i in range(min(2, len(findings))):
            assert findings[i].severity in [Severity.CRITICAL, Severity.HIGH]
