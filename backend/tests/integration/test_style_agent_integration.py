"""Tests de integración para StyleAgent.

Estos tests verifican el funcionamiento del StyleAgent con código
realista que contiene múltiples tipos de problemas de estilo.
"""

from typing import Any, Dict

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


class TestStyleAgentComprehensiveAnalysis:
    """Tests de análisis completo con múltiples problemas."""

    def test_comprehensive_style_analysis(self):
        """StyleAgent detecta múltiples tipos de problemas en código realista."""
        code = """
import os
import sys
import os

def badFunction():
    x = "Esta es una linea que tiene mucho codigo y excede el limite de 88 caracteres establecido por PEP 8"   
    return x

class badclass:
    def anotherBadMethod():
        pass

"""
        context = AnalysisContext(code_content=code, filename="test_file.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Debe detectar varios tipos de problemas
        assert len(findings) >= 3, "Debe detectar múltiples problemas"

        # Verificar categorías detectadas
        categories = {f.issue_type for f in findings}

        # Al menos algunas de estas categorías deben estar
        expected_categories = {"style/pep8", "style/naming", "style/documentation", "style/imports"}
        found_expected = categories.intersection(expected_categories)
        assert (
            len(found_expected) >= 2
        ), f"Debe detectar al menos 2 categorías, encontró: {categories}"

    def test_clean_code_minimal_findings(self):
        """Código limpio produce mínimos findings."""
        code = '''"""Módulo de prueba bien documentado."""


def my_function(value: int) -> int:
    """Retorna el valor duplicado.
    
    Args:
        value: Valor a duplicar.
        
    Returns:
        El valor multiplicado por 2.
    """
    return value * 2


class MyClass:
    """Clase de prueba bien documentada."""
    
    def __init__(self):
        """Inicializa la clase."""
        self.value = 0
    
    def get_value(self) -> int:
        """Retorna el valor actual."""
        return self.value
'''
        context = AnalysisContext(code_content=code, filename="clean_code.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Código limpio debería tener pocos o ningún finding
        assert (
            len(findings) <= 3
        ), f"Código limpio no debería tener muchos findings: {len(findings)}"

    def test_findings_contain_required_fields(self):
        """Todos los findings tienen los campos requeridos."""
        code = """
def myBadFunc():
    x = 1
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        for finding in findings:
            # Campos requeridos
            assert finding.message is not None
            assert finding.line_number is not None
            assert finding.issue_type is not None
            assert finding.severity is not None
            assert finding.agent_name is not None

    def test_agent_name_is_set_correctly(self):
        """El nombre del agente está correcto en todos los findings."""
        code = """
def badFunc():
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        for finding in findings:
            assert finding.agent_name == "StyleAgent"


class TestStyleAgentEventLifecycle:
    """Tests del ciclo de vida completo con eventos."""

    def test_full_event_lifecycle(self):
        """Verifica el ciclo completo: STARTED -> (análisis) -> COMPLETED."""
        event_bus = EventBus()
        event_bus.clear()  # Limpiar observers previos
        observer = MockEventObserver()
        event_bus.subscribe(observer)

        agent = StyleAgent()
        agent.event_bus = event_bus

        code = "x = 1"
        context = AnalysisContext(code_content=code, filename="test.py")
        agent.analyze(context)

        # Extraer tipos de eventos
        event_types = [e[0] for e in observer.events_received]

        assert "AGENT_STARTED" in event_types, "Debe emitir AGENT_STARTED"
        assert "AGENT_COMPLETED" in event_types, "Debe emitir AGENT_COMPLETED"
        assert "AGENT_FAILED" not in event_types, "No debe emitir AGENT_FAILED en caso exitoso"


class TestStyleAgentWithRealWorldPatterns:
    """Tests con patrones de código del mundo real."""

    def test_flask_route_pattern(self):
        """Analiza patrón típico de ruta Flask."""
        code = '''
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/api/users")
def get_users():
    """Retorna lista de usuarios."""
    return jsonify({"users": []})
'''
        context = AnalysisContext(code_content=code, filename="routes.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Este código es bastante limpio, pocos findings esperados
        assert isinstance(findings, list)

    def test_dataclass_pattern(self):
        """Analiza patrón de dataclass."""
        code = '''
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Representa un usuario del sistema."""
    
    id: int
    name: str
    email: str
    age: Optional[int] = None
'''
        context = AnalysisContext(code_content=code, filename="models.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Código limpio, mínimos findings
        assert isinstance(findings, list)

    def test_test_file_pattern(self):
        """Analiza patrón típico de archivo de tests."""
        code = '''
import pytest
from mymodule import MyClass


class TestMyClass:
    """Tests para MyClass."""
    
    def test_initialization(self):
        """Verifica inicialización correcta."""
        obj = MyClass()
        assert obj is not None
    
    def test_method_call(self):
        """Verifica llamada a método."""
        obj = MyClass()
        result = obj.do_something()
        assert result == "expected"
'''
        context = AnalysisContext(code_content=code, filename="test_mymodule.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # Tests bien escritos, pocos findings
        assert isinstance(findings, list)


class TestStyleAgentSeverityLevels:
    """Tests para niveles de severidad apropiados."""

    def test_severity_levels_are_valid(self):
        """Todas las severidades son valores válidos del enum."""
        code = """
def badFunc():
    x = "linea muy larga " + "a" * 100
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        valid_severities = {Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL}

        for finding in findings:
            assert finding.severity in valid_severities, f"Severidad inválida: {finding.severity}"

    def test_naming_issues_are_medium_or_lower(self):
        """Problemas de naming son MEDIUM o menor severidad."""
        code = """
def badFunction():
    pass
"""
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        naming_findings = [f for f in findings if f.issue_type == "style/naming"]

        for f in naming_findings:
            assert f.severity in {Severity.LOW, Severity.MEDIUM}


class TestStyleAgentEdgeCases:
    """Tests de casos borde."""

    def test_unicode_content(self):
        """Maneja contenido con caracteres unicode."""
        code = '''
def greet():
    """Saluda en español."""
    return "¡Hola, cómo estás! 你好 🎉"
'''
        context = AnalysisContext(code_content=code, filename="test.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # No debe crashear
        assert isinstance(findings, list)

    def test_very_long_file(self):
        """Maneja archivos largos."""
        # Generar código con 500 funciones
        lines = ["# Generated file\n"]
        for i in range(100):
            lines.append(
                f'''
def function_{i}():
    """Función número {i}."""
    return {i}
'''
            )
        code = "\n".join(lines)

        context = AnalysisContext(code_content=code, filename="large_file.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        # No debe crashear ni tomar demasiado tiempo
        assert isinstance(findings, list)

    def test_only_comments(self):
        """Maneja archivo con solo comentarios."""
        code = """
# Este es un comentario
# Otro comentario
# Más comentarios
"""
        context = AnalysisContext(code_content=code, filename="comments.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        assert isinstance(findings, list)

    def test_only_imports(self):
        """Maneja archivo con solo imports."""
        code = """
import os
import sys
from typing import List, Dict
"""
        context = AnalysisContext(code_content=code, filename="imports.py")

        agent = StyleAgent()
        findings = agent.analyze(context)

        assert isinstance(findings, list)
