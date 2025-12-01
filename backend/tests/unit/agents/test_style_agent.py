"""Tests unitarios para StyleAgent."""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.agents.style_agent import StyleAgent
from src.core.events.event_bus import EventBus
from src.core.events.observers import EventObserver
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Severity


class MockEventObserver(EventObserver):
    """Observer de prueba para capturar eventos."""

    def __init__(self):
        self.events_received = []

    def on_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Captura eventos recibidos."""
        self.events_received.append((event_type, data))


class TestStyleAgentInitialization:
    """Tests de inicialización del StyleAgent."""

    def test_agent_initialization(self):
        """StyleAgent se inicializa con configuración correcta."""
        agent = StyleAgent()

        assert agent.name == "StyleAgent"
        assert agent.version == "1.0.0"
        assert agent.category == "style"
        assert agent.enabled is True

    def test_line_length_limit_default(self):
        """El límite de longitud de línea es 88 por defecto."""
        agent = StyleAgent()

        assert agent.line_length_limit == 88


class TestLineLengthDetection:
    """Tests para detección de líneas largas."""

    def test_detect_line_too_long(self):
        """Detecta líneas que exceden 88 caracteres."""
        # Línea de 100+ caracteres
        code = "x = '" + "a" * 100 + "'"
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        line_findings = [f for f in findings if "longitud" in f.message.lower()]
        assert len(line_findings) >= 1
        assert line_findings[0].issue_type == "style/pep8"

    def test_no_finding_for_short_lines(self):
        """No detecta líneas cortas como problema de longitud."""
        code = "x = 1\ny = 2\n"
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        line_length_findings = [f for f in findings if "longitud" in f.message.lower()]
        assert len(line_length_findings) == 0

    def test_detect_trailing_whitespace(self):
        """Detecta espacios en blanco al final de línea."""
        code = "x = 1   \n"  # Espacios al final
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        trailing_findings = [f for f in findings if "blanco al final" in f.message.lower()]
        assert len(trailing_findings) >= 1


class TestDocstringDetection:
    """Tests para detección de docstrings faltantes."""

    def test_detect_missing_function_docstring(self):
        """Detecta función pública sin docstring."""
        code = """
def my_public_function():
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        docstring_findings = [f for f in findings if "docstring" in f.message.lower()]
        assert len(docstring_findings) >= 1
        assert any(f.issue_type == "style/documentation" for f in docstring_findings)

    def test_detect_missing_class_docstring(self):
        """Detecta clase sin docstring."""
        code = """
class MyClass:
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        docstring_findings = [f for f in findings if "docstring" in f.message.lower()]
        assert len(docstring_findings) >= 1

    def test_no_finding_for_private_function(self):
        """No detecta funciones privadas sin docstring."""
        code = """
def _private_function():
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Funciones privadas no requieren docstring en nuestros checks
        private_docstring_findings = [
            f for f in findings if "docstring" in f.message.lower() and "_private" in f.message
        ]
        assert len(private_docstring_findings) == 0

    def test_no_finding_for_function_with_docstring(self):
        """No detecta función con docstring."""
        code = '''
def my_function():
    """Esta es la documentación."""
    pass
'''
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # No debería haber findings de docstring para my_function
        my_func_docstring = [
            f for f in findings if "docstring" in f.message.lower() and "my_function" in f.message
        ]
        assert len(my_func_docstring) == 0


class TestNamingConventions:
    """Tests para convenciones de nombres PEP 8."""

    def test_detect_camelcase_function(self):
        """Detecta función con nombre en camelCase."""
        code = """
def myBadFunction():
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        naming_findings = [
            f
            for f in findings
            if "snake_case" in f.message.lower() and "funcion" in f.message.lower()
        ]
        assert len(naming_findings) >= 1
        assert any(f.issue_type == "style/naming" for f in naming_findings)

    def test_detect_lowercase_class(self):
        """Detecta clase con nombre en lowercase."""
        code = """
class myclass:
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        naming_findings = [
            f for f in findings if "PascalCase" in f.message and "clase" in f.message.lower()
        ]
        assert len(naming_findings) >= 1

    def test_no_finding_for_correct_function_name(self):
        """No detecta función con nombre correcto."""
        code = """
def my_correct_function():
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        naming_findings = [
            f
            for f in findings
            if "my_correct_function" in f.message and "snake_case" in f.message.lower()
        ]
        assert len(naming_findings) == 0

    def test_no_finding_for_correct_class_name(self):
        """No detecta clase con nombre correcto."""
        code = """
class MyCorrectClass:
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        naming_findings = [
            f for f in findings if "MyCorrectClass" in f.message and "PascalCase" in f.message
        ]
        assert len(naming_findings) == 0


class TestImportAnalysis:
    """Tests para análisis de imports."""

    def test_detect_unused_import(self):
        """Detecta import no utilizado."""
        code = """
import os
import sys

print("hello")
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        import_findings = [
            f for f in findings if f.issue_type == "style/imports" or "import" in f.message.lower()
        ]
        # os y sys no se usan, deberían detectarse
        assert len(import_findings) >= 1

    def test_detect_duplicate_import(self):
        """Detecta import duplicado."""
        code = """
import os
import sys
import os
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # El mensaje usa "múltiples veces" no "duplicado"
        duplicate_findings = [
            f
            for f in findings
            if "multiples" in f.message.lower() or "reimport" in f.message.lower()
        ]
        assert len(duplicate_findings) >= 1


class TestFindingsOrdering:
    """Tests para ordenamiento de findings."""

    def test_findings_ordered_by_line_number(self):
        """Los findings se ordenan por número de línea ascendente."""
        code = """
def badFunc():
    pass

class badclass:
    pass

def anotherBadFunc():
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        if len(findings) > 1:
            line_numbers = [f.line_number for f in findings]
            assert line_numbers == sorted(line_numbers), "Findings deben estar ordenados por línea"


class TestEventEmission:
    """Tests para emisión de eventos."""

    def test_emits_agent_started_event(self):
        """El agente emite evento AGENT_STARTED al iniciar."""
        event_bus = EventBus()
        event_bus.clear()  # Limpiar observers previos
        observer = MockEventObserver()
        event_bus.subscribe(observer)

        agent = StyleAgent()
        agent.event_bus = event_bus

        code = "x = 1"
        context = AnalysisContext(code_content=code, filename="test.py")
        agent.analyze(context)

        # Verificar que hubo eventos AGENT_STARTED
        started_events = [
            e
            for e in observer.events_received
            if e[0] == "AGENT_STARTED" or e[1].get("type") == "AGENT_STARTED"
        ]
        assert len(started_events) >= 1

    def test_emits_agent_completed_event(self):
        """El agente emite evento AGENT_COMPLETED al finalizar."""
        event_bus = EventBus()
        event_bus.clear()  # Limpiar observers previos
        observer = MockEventObserver()
        event_bus.subscribe(observer)

        agent = StyleAgent()
        agent.event_bus = event_bus

        code = "x = 1"
        context = AnalysisContext(code_content=code, filename="test.py")
        agent.analyze(context)

        # Verificar que hubo eventos AGENT_COMPLETED
        completed_events = [
            e
            for e in observer.events_received
            if e[0] == "AGENT_COMPLETED" or e[1].get("type") == "AGENT_COMPLETED"
        ]
        assert len(completed_events) >= 1


class TestErrorHandling:
    """Tests para manejo de errores."""

    def test_syntax_error_does_not_crash(self):
        """Error de sintaxis no crashea el agente."""
        code = "def broken("  # Sintaxis inválida
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        # No debe lanzar excepción
        findings = agent.analyze(context)

        # Puede retornar lista vacía o parcial
        assert isinstance(findings, list)

    def test_empty_code_returns_empty_or_minimal_findings(self):
        """Código mínimo retorna lista con findings mínimos."""
        code = "# Empty file"  # Código mínimo válido
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Lista vacía o con findings mínimos (como missing module docstring)
        assert isinstance(findings, list)
        # Puede tener algunos findings menores
        assert len(findings) <= 5


class TestIssueTypeCategories:
    """Tests para verificar categorías correctas de issue_type."""

    def test_line_style_uses_pep8_category(self):
        """Problemas de línea usan categoría style/pep8."""
        code = "x = '" + "a" * 100 + "'"
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        line_findings = [f for f in findings if "longitud" in f.message.lower()]
        for f in line_findings:
            assert f.issue_type == "style/pep8"

    def test_docstring_uses_documentation_category(self):
        """Problemas de docstring usan categoría style/documentation."""
        code = """
def my_function():
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Buscar findings con "docstring" en el mensaje que usen nuestras reglas internas
        doc_findings = [
            f
            for f in findings
            if "docstring" in f.message.lower() and f.rule_id.startswith("STYLE")
        ]
        for f in doc_findings:
            assert f.issue_type == "style/documentation"

    def test_naming_uses_naming_category(self):
        """Problemas de nombres usan categoría style/naming."""
        code = """
def badFunction():
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Buscar findings con snake_case que sean de nuestras reglas internas
        naming_findings = [
            f
            for f in findings
            if "snake_case" in f.message.lower() and f.rule_id.startswith("STYLE")
        ]
        for f in naming_findings:
            assert f.issue_type == "style/naming"

    def test_imports_uses_imports_category(self):
        """Problemas de imports usan categoría style/imports."""
        code = """
import os
import os
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Buscar findings de import que sean de nuestras reglas internas
        import_findings = [f for f in findings if f.rule_id.startswith("STYLE02")]
        for f in import_findings:
            assert f.issue_type == "style/imports"
