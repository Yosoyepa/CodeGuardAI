"""
Unit tests for BaseAgent abstract class
Tests para la clase base BaseAgent
"""

from typing import List
from unittest.mock import Mock

import pytest

from src.agents.base_agent import BaseAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding, Severity


class DummyAgent(BaseAgent):
    """
    Agente dummy para testing.

    Implementación concreta de BaseAgent para fines de testing.
    """

    def __init__(self):
        super().__init__(name="DummyAgent", version="1.0.0", category="test")

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        """Implementación dummy que retorna un finding de prueba."""
        return [
            Finding(
                severity=Severity.INFO,
                issue_type="test",
                message="Test finding",
                line_number=1,
                agent_name=self.name,
            )
        ]


class TestBaseAgentInitialization:
    """Tests para inicialización del agente."""

    def test_create_agent_with_defaults(self):
        """Test crear agente con valores por defecto."""
        agent = DummyAgent()

        assert agent.name == "DummyAgent"
        assert agent.version == "1.0.0"
        assert agent.category == "test"
        assert agent.enabled is True

    def test_agent_name_required(self):
        """Test que el nombre es requerido."""
        with pytest.raises(ValueError, match="name cannot be empty"):

            class BadAgent(BaseAgent):
                def __init__(self):
                    super().__init__(name="")

                def analyze(self, context):
                    pass

            BadAgent()

    def test_agent_info_dict(self):
        """Test que get_info retorna diccionario correcto."""
        agent = DummyAgent()
        info = agent.get_info()

        assert isinstance(info, dict)
        assert info["name"] == "DummyAgent"
        assert info["version"] == "1.0.0"
        assert info["category"] == "test"
        assert info["enabled"] is True


class TestBaseAgentMethods:
    """Tests para métodos del agente."""

    def test_is_enabled_when_enabled(self):
        """Test is_enabled cuando está habilitado."""
        agent = DummyAgent()
        assert agent.is_enabled() is True

    def test_is_enabled_when_disabled(self):
        """Test is_enabled cuando está deshabilitado."""
        agent = DummyAgent()
        agent.disable()
        assert agent.is_enabled() is False

    def test_enable_agent(self):
        """Test habilitar un agente."""
        agent = DummyAgent()
        agent.disable()
        assert agent.enabled is False

        agent.enable()
        assert agent.enabled is True

    def test_disable_agent(self):
        """Test deshabilitar un agente."""
        agent = DummyAgent()
        assert agent.enabled is True

        agent.disable()
        assert agent.enabled is False


class TestBaseAgentAnalyze:
    """Tests para el método analyze."""

    def test_analyze_returns_findings(self):
        """Test que analyze retorna lista de findings."""
        agent = DummyAgent()
        context = AnalysisContext(code_content="print('hello')", filename="test.py")

        findings = agent.analyze(context)

        assert isinstance(findings, list)
        assert len(findings) >= 1
        assert findings[0].agent_name == "DummyAgent"
        assert findings[0].severity == Severity.INFO

    def test_abstract_method_not_callable(self):
        """Test que no se puede instanciar BaseAgent directamente."""
        with pytest.raises(TypeError):
            BaseAgent(name="TestAgent")


class TestBaseAgentRepr:
    """Tests para representación string."""

    def test_repr_contains_name_and_version(self):
        """Test que __repr__ contiene nombre y versión."""
        agent = DummyAgent()
        repr_str = repr(agent)

        assert "DummyAgent" in repr_str
        assert "1.0.0" in repr_str
        assert "test" in repr_str

    def test_str_representation(self):
        """Test que __str__ es legible."""
        agent = DummyAgent()
        str_repr = str(agent)

        assert "DummyAgent" in str_repr
        assert "1.0.0" in str_repr
        assert "test" in str_repr
        assert "enabled" in str_repr.lower()


class TestBaseAgentEvents:
    """Tests para emisión de eventos."""

    def test_emit_agent_started(self):
        """Test que _emit_agent_started publica evento."""
        event_bus_mock = Mock()
        agent = DummyAgent()
        agent.event_bus = event_bus_mock

        context = AnalysisContext(code_content="code", filename="test.py")

        agent._emit_agent_started(context)

        event_bus_mock.publish.assert_called_once()
        # publish recibe (event_type, data)
        event_type = event_bus_mock.publish.call_args[0][0]
        data = event_bus_mock.publish.call_args[0][1]
        assert event_type == "AGENT_STARTED"
        assert data["agent_name"] == "DummyAgent"

    def test_emit_agent_completed(self):
        """Test que _emit_agent_completed publica evento."""
        event_bus_mock = Mock()
        agent = DummyAgent()
        agent.event_bus = event_bus_mock

        context = AnalysisContext(code_content="code", filename="test.py")
        findings = [
            Finding(
                severity=Severity.INFO,
                issue_type="test",
                message="Test finding message",
                line_number=1,
                agent_name="DummyAgent",
            )
        ]

        agent._emit_agent_completed(context, findings)

        event_bus_mock.publish.assert_called_once()
        # publish recibe (event_type, data)
        event_type = event_bus_mock.publish.call_args[0][0]
        data = event_bus_mock.publish.call_args[0][1]
        assert event_type == "AGENT_COMPLETED"
        assert data["findings_count"] == 1

    def test_emit_agent_failed(self):
        """Test que _emit_agent_failed publica evento."""
        event_bus_mock = Mock()
        agent = DummyAgent()
        agent.event_bus = event_bus_mock
        context = AnalysisContext(code_content="code", filename="test.py")

        error = RuntimeError("boom")
        agent._emit_agent_failed(context, error)

        event_bus_mock.publish.assert_called_once()
        # publish recibe (event_type, data)
        event_type = event_bus_mock.publish.call_args[0][0]
        data = event_bus_mock.publish.call_args[0][1]
        assert event_type == "AGENT_FAILED"
        assert "boom" in data["error"]

    def test_no_events_when_event_bus_none(self):
        """Test que no falla si event_bus es None."""
        agent = DummyAgent()
        agent.event_bus = None

        context = AnalysisContext(code_content="code", filename="test.py")

        # No debe lanzar excepción
        agent._emit_agent_started(context)
        agent._emit_agent_completed(context, [])


class TestBaseAgentLogging:
    """Tests para el logging del agente."""

    def test_log_helpers_delegate_to_logger(self):
        """Test que los helpers de log delegan en el logger."""
        agent = DummyAgent()
        agent.logger = Mock()

        agent.log_info("info")
        agent.log_warning("warn")
        agent.log_error("err")
        agent.log_debug("dbg")

        agent.logger.info.assert_called_once_with("[%s] %s", "DummyAgent", "info")
        agent.logger.warning.assert_called_once_with("[%s] %s", "DummyAgent", "warn")
        agent.logger.error.assert_called_once_with("[%s] %s", "DummyAgent", "err")
        agent.logger.debug.assert_called_once_with("[%s] %s", "DummyAgent", "dbg")
