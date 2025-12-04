"""
Tests for AIExplainerService and related components.

Tests Sprint 3 functionality including:
- Rate limiting
- MCP Context Enricher
- AI explanation generation
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.config.mcp_config import (
    OWASP_TOP_10,
    SecurityContext,
    format_security_context,
    get_security_context,
)
from src.external.interfaces.ai_client import AIResponse
from src.schemas.ai_explanation import AIExplanation, RateLimitInfo
from src.schemas.finding import Finding, Severity
from src.services.ai_service import (
    AIExplainerService,
    AIExplanationError,
    InMemoryRateLimiter,
    RateLimitExceeded,
)
from src.services.mcp_context_enricher import (
    EnrichedContext,
    MCPContextEnricher,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_security_finding() -> Finding:
    """Create a sample security finding for testing."""
    return Finding(
        severity=Severity.CRITICAL,
        issue_type="dangerous_function",
        message="Use of eval() detected - allows arbitrary code execution",
        line_number=42,
        agent_name="SecurityAgent",
        code_snippet="result = eval(user_input)",
        suggestion="Use ast.literal_eval() for safe literal evaluation",
        rule_id="SEC001_EVAL",
    )


@pytest.fixture
def sample_style_finding() -> Finding:
    """Create a sample style finding (non-security)."""
    return Finding(
        severity=Severity.LOW,
        issue_type="line_too_long",
        message="Line exceeds 88 characters",
        line_number=100,
        agent_name="StyleAgent",
        code_snippet="x = 'a very long string' * 10  # this line is too long",
        suggestion="Break the line into multiple lines",
        rule_id="STYLE001_LINE_LENGTH",
    )


@pytest.fixture
def mock_ai_client():
    """Create a mock AI client."""
    client = AsyncMock()
    client.generate_explanation = AsyncMock(
        return_value=AIResponse(
            content='{"explanation": "Test explanation", "suggested_fix": "# fixed code", "attack_example": "evil code", "references": ["CWE-94"]}',
            model_name="gemini-1.5-flash-001",
            tokens_used=150,
            finish_reason="STOP",
        )
    )
    client.is_configured = True
    client.model_name = "gemini-1.5-flash-001"
    return client


@pytest.fixture
def rate_limiter():
    """Create a rate limiter with low limit for testing."""
    return InMemoryRateLimiter(limit_per_hour=3)


# ============================================================
# Tests for MCP Config (OWASP Top 10)
# ============================================================


class TestMCPConfig:
    """Tests for MCP configuration and OWASP lookups."""

    def test_owasp_top_10_has_all_categories(self):
        """OWASP dictionary should have all 10 categories."""
        assert len(OWASP_TOP_10) == 10

        # Las claves son descriptivas, las categorías OWASP están en los valores
        expected_categories = [
            "A01:2021",
            "A02:2021",
            "A03:2021",
            "A04:2021",
            "A05:2021",
            "A06:2021",
            "A07:2021",
            "A08:2021",
            "A09:2021",
            "A10:2021",
        ]
        # Extraer las categorías de los valores del diccionario
        actual_categories = [ctx.category for ctx in OWASP_TOP_10.values()]
        for cat in expected_categories:
            found = any(cat in actual_cat for actual_cat in actual_categories)
            assert found, f"Missing OWASP category: {cat}"

    def test_get_security_context_by_rule_id(self):
        """Should find security context by rule_id."""
        context = get_security_context(rule_id="SEC001_EVAL")

        assert context is not None
        assert "Injection" in context.category or "Inyección" in context.category

    def test_get_security_context_by_issue_type(self):
        """Should find security context by issue_type."""
        context = get_security_context(issue_type="sql_injection")

        assert context is not None
        assert context.cwe_ids is not None

    def test_get_security_context_unknown(self):
        """Should return None for unknown rule_id."""
        context = get_security_context(rule_id="UNKNOWN_RULE")
        assert context is None

    def test_format_security_context(self):
        """Should format security context as text."""
        context = SecurityContext(
            category="A03:2021 - Injection",
            description="Test description",
            impact="Test impact",
            mitigation="Test mitigation",
            references=["https://owasp.org"],
            cwe_ids=["CWE-94"],
        )

        formatted = format_security_context(context)

        assert "A03:2021" in formatted
        assert "Test description" in formatted
        assert "CWE-94" in formatted


# ============================================================
# Tests for MCP Context Enricher
# ============================================================


class TestMCPContextEnricher:
    """Tests for the MCP Context Enricher service."""

    @pytest.mark.asyncio
    async def test_enrich_security_finding(self, sample_security_finding):
        """Should enrich security findings with OWASP context."""
        enricher = MCPContextEnricher()

        result = await enricher.enrich(sample_security_finding)

        assert isinstance(result, EnrichedContext)
        assert result.finding == sample_security_finding
        assert result.has_security_context
        assert result.security_context is not None
        assert result.is_security_finding

    @pytest.mark.asyncio
    async def test_enrich_non_security_finding(self, sample_style_finding):
        """Should handle non-security findings gracefully."""
        enricher = MCPContextEnricher()

        result = await enricher.enrich(sample_style_finding)

        assert isinstance(result, EnrichedContext)
        assert result.finding == sample_style_finding
        # Style findings don't have OWASP context
        assert not result.is_security_finding

    @pytest.mark.asyncio
    async def test_enrich_batch(self, sample_security_finding, sample_style_finding):
        """Should enrich multiple findings."""
        enricher = MCPContextEnricher()
        findings = [sample_security_finding, sample_style_finding]

        results = await enricher.enrich_batch(findings)

        assert len(results) == 2
        assert all(isinstance(r, EnrichedContext) for r in results)

    @pytest.mark.asyncio
    async def test_formatted_context_includes_finding_info(self, sample_security_finding):
        """Formatted context should include finding details."""
        enricher = MCPContextEnricher()

        result = await enricher.enrich(sample_security_finding)

        assert (
            "eval()" in result.formatted_prompt_context
            or "dangerous_function" in result.formatted_prompt_context
        )
        assert str(sample_security_finding.line_number) in result.formatted_prompt_context


# ============================================================
# Tests for In-Memory Rate Limiter
# ============================================================


class TestInMemoryRateLimiter:
    """Tests for the in-memory rate limiter."""

    def test_check_and_consume_allows_within_limit(self, rate_limiter):
        """Should allow requests within limit."""
        user_id = "user-123"

        # First 3 requests should succeed (limit is 3)
        for i in range(3):
            info = rate_limiter.check_and_consume(user_id)
            assert info.requests_remaining == 2 - i

    def test_check_and_consume_blocks_over_limit(self, rate_limiter):
        """Should block requests over limit."""
        user_id = "user-456"

        # Consume all 3 requests
        for _ in range(3):
            rate_limiter.check_and_consume(user_id)

        # 4th request should raise
        with pytest.raises(RateLimitExceeded) as exc_info:
            rate_limiter.check_and_consume(user_id)

        assert exc_info.value.rate_limit_info.requests_remaining == 0

    def test_rate_limit_per_user(self, rate_limiter):
        """Each user should have independent limits."""
        user1 = "user-1"
        user2 = "user-2"

        # Exhaust user1's limit
        for _ in range(3):
            rate_limiter.check_and_consume(user1)

        # user2 should still be able to make requests
        info = rate_limiter.check_and_consume(user2)
        assert info.requests_remaining == 2

    def test_get_remaining_without_consuming(self, rate_limiter):
        """get_remaining should not consume a request."""
        user_id = "user-789"

        info1 = rate_limiter.get_remaining(user_id)
        info2 = rate_limiter.get_remaining(user_id)

        assert info1.requests_remaining == info2.requests_remaining == 3


# ============================================================
# Tests for AI Explainer Service
# ============================================================


class TestAIExplainerService:
    """Tests for the AI Explainer Service."""

    @pytest.mark.asyncio
    async def test_explain_finding_success(self, sample_security_finding, mock_ai_client):
        """Should successfully generate explanation."""
        service = AIExplainerService(
            ai_client=mock_ai_client,
            rate_limiter=InMemoryRateLimiter(limit_per_hour=10),
        )

        explanation, rate_info = await service.explain_finding(
            finding=sample_security_finding,
            user_id="test-user",
        )

        assert isinstance(explanation, AIExplanation)
        assert explanation.explanation == "Test explanation"
        assert explanation.model_used == "gemini-1.5-flash-001"
        assert rate_info.requests_remaining == 9

    @pytest.mark.asyncio
    async def test_explain_finding_rate_limited(self, sample_security_finding, mock_ai_client):
        """Should raise when rate limit exceeded."""
        service = AIExplainerService(
            ai_client=mock_ai_client,
            rate_limiter=InMemoryRateLimiter(limit_per_hour=1),
        )

        # First request succeeds
        await service.explain_finding(
            finding=sample_security_finding,
            user_id="limited-user",
        )

        # Second request should fail
        with pytest.raises(RateLimitExceeded):
            await service.explain_finding(
                finding=sample_security_finding,
                user_id="limited-user",
            )

    @pytest.mark.asyncio
    async def test_explain_finding_parses_json_response(
        self, sample_security_finding, mock_ai_client
    ):
        """Should parse JSON response from AI."""
        # Set up mock to return JSON
        mock_ai_client.generate_explanation.return_value = AIResponse(
            content='{"explanation": "Detailed explanation", "suggested_fix": "fixed_code()", "attack_example": "exploit", "references": ["CWE-94", "OWASP A03"]}',
            model_name="gemini-1.5-pro-001",
            tokens_used=200,
            finish_reason="STOP",
        )

        service = AIExplainerService(
            ai_client=mock_ai_client,
            rate_limiter=InMemoryRateLimiter(limit_per_hour=10),
        )

        explanation, _ = await service.explain_finding(
            finding=sample_security_finding,
            user_id="test-user",
        )

        assert explanation.explanation == "Detailed explanation"
        assert explanation.suggested_fix == "fixed_code()"
        assert explanation.attack_example == "exploit"
        assert "CWE-94" in explanation.references

    @pytest.mark.asyncio
    async def test_explain_finding_handles_non_json_response(
        self, sample_security_finding, mock_ai_client
    ):
        """Should handle non-JSON response gracefully."""
        mock_ai_client.generate_explanation.return_value = AIResponse(
            content="This is a plain text response without JSON formatting.",
            model_name="gemini-1.5-flash-001",
            tokens_used=50,
            finish_reason="STOP",
        )

        service = AIExplainerService(
            ai_client=mock_ai_client,
            rate_limiter=InMemoryRateLimiter(limit_per_hour=10),
        )

        explanation, _ = await service.explain_finding(
            finding=sample_security_finding,
            user_id="test-user",
        )

        # Should use raw content as explanation
        assert "plain text response" in explanation.explanation

    def test_is_configured_delegates_to_client(self, mock_ai_client):
        """is_configured should delegate to AI client."""
        service = AIExplainerService(ai_client=mock_ai_client)

        assert service.is_configured == mock_ai_client.is_configured


# ============================================================
# Tests for AIExplanation Schema
# ============================================================


class TestAIExplanationSchema:
    """Tests for AIExplanation Pydantic schema."""

    def test_to_dict_serialization(self):
        """Should serialize to dict for JSONB storage."""
        explanation = AIExplanation(
            explanation="Test explanation",
            suggested_fix="# fixed",
            attack_example="exploit code",
            references=["CWE-94"],
            model_used="gemini-1.5-flash",
            tokens_used=100,
        )

        data = explanation.to_dict()

        assert data["explanation"] == "Test explanation"
        assert data["tokens_used"] == 100
        assert "generated_at" in data

    def test_from_dict_deserialization(self):
        """Should deserialize from JSONB dict."""
        data = {
            "explanation": "Test explanation with sufficient length for validation",
            "suggested_fix": "# fix",
            "attack_example": None,
            "references": ["CWE-1"],
            "model_used": "test-model",
            "tokens_used": 50,
            "generated_at": "2024-01-15T10:30:00+00:00",
        }

        explanation = AIExplanation.from_dict(data)

        assert explanation.explanation == "Test explanation with sufficient length for validation"
        assert explanation.model_used == "test-model"
        assert explanation.generated_at.year == 2024
