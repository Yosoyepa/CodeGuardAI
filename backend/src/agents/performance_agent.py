"""
PerformanceAgent - Agente especializado en análisis de rendimiento de código Python.

Este agente analiza el AST (Abstract Syntax Tree) para detectar patrones de código
que pueden causar problemas de rendimiento, complejidad temporal excesiva o fugas de recursos.
"""

import ast
from typing import List, Set

from src.agents.base_agent import BaseAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding, Severity


class PerformanceVisitor(ast.NodeVisitor):
    """
    Visitante del AST para detectar problemas de rendimiento.
    Recorre el árbol sintáctico buscando patrones ineficientes.
    """

    # Métodos sospechosos de ser consultas a BD u operaciones costosas de I/O
    DB_METHODS = {"execute", "query", "select", "commit", "flush", "rollback", "fetch", "get"}

    # Métodos que pueden cargar grandes volúmenes de datos en memoria
    MEMORY_INTENSIVE_METHODS = {"read", "readlines", "fetchall"}

    def __init__(self):
        self.findings_data: List[dict] = []
        self.safe_lines: Set[int] = set()
        self.loop_depth = 0
        self.in_loop = False

    def visit_With(self, node: ast.With):
        self._check_safe_resources(node)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self._check_safe_resources(node)
        self.generic_visit(node)

    def _check_safe_resources(self, node):
        for item in node.items:
            if not isinstance(item.context_expr, ast.Call):
                continue

            func = item.context_expr.func
            if (isinstance(func, ast.Name) and func.id == "open") or (
                isinstance(func, ast.Attribute) and func.attr == "socket"
            ):
                self.safe_lines.add(item.context_expr.lineno)

    def visit_For(self, node: ast.For):
        self._check_nested_loop(node)
        self._visit_loop_body(node)

    def visit_While(self, node: ast.While):
        self._check_nested_loop(node)
        self._visit_loop_body(node)

    def _visit_loop_body(self, node):
        """Maneja la lógica común para cuerpos de bucles."""
        self.loop_depth += 1
        prev_in_loop = self.in_loop
        self.in_loop = True

        # Continuar visitando los hijos
        self.generic_visit(node)

        self.in_loop = prev_in_loop
        self.loop_depth -= 1

    def _check_nested_loop(self, node):
        """Detecta anidamiento excesivo de bucles (O(n^2) o peor)."""
        if self.loop_depth >= 1:
            self.findings_data.append(
                {"type": "complexity", "node": node, "depth": self.loop_depth + 1}
            )

    def visit_Call(self, node: ast.Call):
        """Detecta llamadas a funciones ineficientes o mal gestionadas."""
        # Analizar la función llamada una sola vez para reducir complejidad
        func = node.func

        if isinstance(func, ast.Name):
            # Caso: open()
            if func.id == "open":
                self.findings_data.append(
                    {"type": "resource_leak", "resource": "file", "node": node}
                )

        elif isinstance(func, ast.Attribute):
            method_name = func.attr

            # Caso: socket.socket()
            if method_name == "socket":
                self.findings_data.append(
                    {"type": "resource_leak", "resource": "socket", "node": node}
                )

            # Caso: list.insert(0)
            elif method_name == "insert" and self.in_loop:
                if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                    self.findings_data.append({"type": "inefficient_insert", "node": node})

            # Caso: DB Methods (N+1)
            elif self.in_loop and method_name in self.DB_METHODS:
                self.findings_data.append(
                    {"type": "n_plus_one", "method": method_name, "node": node}
                )

            # Caso: Memory Intensive
            elif method_name in self.MEMORY_INTENSIVE_METHODS:
                if not node.args:
                    self.findings_data.append(
                        {"type": "memory_intensive", "method": method_name, "node": node}
                    )

        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        """Detecta búsquedas lineales ineficientes dentro de bucles."""
        if not self.in_loop:
            self.generic_visit(node)
            return

        # Detectar 'x in list'
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, (ast.In, ast.NotIn)):
                # Heurística simple: Si el nombre de la variable sugiere un mapa/set, ignorar
                if isinstance(comparator, ast.Name):
                    name = comparator.id.lower()
                    if any(s in name for s in ["map", "dict", "set", "hash"]):
                        continue

                self.findings_data.append({"type": "linear_search", "node": node})
        self.generic_visit(node)


class PerformanceAgent(BaseAgent):
    """
    Agente especializado en detectar ineficiencias de rendimiento.

    Analiza:
    1. Complejidad Algorítmica: Bucles anidados.
    2. Database: Problema N+1 queries.
    3. Memoria: Operaciones intensivas sin límites.
    4. Colecciones: Inserciones costosas, búsquedas lineales.
    5. Recursos: Fugas en archivos y sockets.
    """

    def __init__(self):
        super().__init__(
            name="PerformanceAgent", version="1.1.0", category="performance", enabled=True
        )

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        """
        Analiza el código en busca de problemas de rendimiento.

        Args:
            context: Contexto del análisis con el código fuente.

        Returns:
            Lista de hallazgos de rendimiento.
        """
        self._emit_agent_started(context)
        findings: List[Finding] = []

        try:
            tree = ast.parse(context.code_content)

            # 1. Ejecutar el visitante principal (detecta problemas y recursos seguros)
            visitor = PerformanceVisitor()
            visitor.visit(tree)

            for item in visitor.findings_data:
                finding = self._create_finding(item, context, visitor.safe_lines)
                if finding:
                    findings.append(finding)

            # Ordenar hallazgos por severidad (CRITICAL primero)
            findings.sort(
                key=lambda f: (
                    ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"].index(f.severity.value)
                )
            )

            self._emit_agent_completed(context, findings)

        except SyntaxError as e:
            self.log_error(f"Error de sintaxis al analizar rendimiento: {e}")
        except Exception as e:
            self._emit_agent_failed(context, e)
            self.log_error(f"Error inesperado en PerformanceAgent: {e}")

        return findings

    def _create_finding(
        self, item: dict, context: AnalysisContext, safe_lines: Set[int]
    ) -> Finding | None:
        """Convierte los datos crudos del visitante en objetos Finding."""
        node = item["node"]
        issue_type = item["type"]

        if issue_type == "complexity":
            depth = item["depth"]
            severity = Severity.CRITICAL if depth >= 3 else Severity.HIGH

            return Finding(
                severity=severity,
                issue_type="performance/complexity",
                message=f"Posible complejidad O(n^{depth}) detectada por bucles anidados.",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion=(
                    "Intenta aplanar los bucles o mover el bucle interno a una función "
                    "separada optimizada."
                ),
                agent_name=self.name,
                rule_id="PERF001_NESTED_LOOPS",
            )

        elif issue_type == "n_plus_one":
            return Finding(
                severity=Severity.CRITICAL,
                issue_type="performance/database",
                message=(
                    f"Posible problema N+1 Query: Llamada a '{item['method']}' dentro de un bucle."
                ),
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion=(
                    "Usa 'eager loading' (JOINs) o procesa los datos en lote fuera del bucle."
                ),
                agent_name=self.name,
                rule_id="PERF004_N_PLUS_ONE",
            )

        elif issue_type == "memory_intensive":
            return Finding(
                severity=Severity.HIGH,
                issue_type="performance/memory",
                message=f"Operación de memoria intensiva '{item['method']}' sin límites detectada.",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion=(
                    f"Usa argumentos de tamaño (ej: {item['method']}(1024)) o procesa el "
                    "archivo línea por línea."
                ),
                agent_name=self.name,
                rule_id="PERF005_UNBOUNDED_MEMORY",
            )

        elif issue_type == "inefficient_insert":
            return Finding(
                severity=Severity.HIGH,
                issue_type="performance/inefficient-operation",
                message="Uso ineficiente de list.insert(0) dentro de un bucle (O(n)).",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion=(
                    "Usa collections.deque.appendleft() o construye la lista y usa reverse()."
                ),
                agent_name=self.name,
                rule_id="PERF002_LIST_INSERT",
            )

        elif issue_type == "linear_search":
            return Finding(
                severity=Severity.MEDIUM,
                issue_type="performance/inefficient-operation",
                message="Búsqueda lineal ('in') detectada dentro de un bucle.",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion=(
                    "Si la colección es grande, considera convertirla a un 'set' o 'dict' "
                    "para búsquedas O(1)."
                ),
                agent_name=self.name,
                rule_id="PERF002_LINEAR_SEARCH",
            )

        elif issue_type == "resource_leak":
            if node.lineno in safe_lines:
                return None

            resource = item.get("resource", "resource")
            return Finding(
                severity=Severity.HIGH,
                issue_type="performance/resource-leak",
                message=f"Llamada a {resource} sin usar un context manager ('with').",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion=(
                    "Usa 'with' statement para asegurar que el recurso se libere correctamente."
                ),
                agent_name=self.name,
                rule_id="PERF003_RESOURCE_LEAK",
            )

        return None

    def _get_snippet(self, context: AnalysisContext, line_no: int) -> str:
        """Extrae la línea de código correspondiente."""
        lines = context.code_content.splitlines()
        if 0 <= line_no - 1 < len(lines):
            return lines[line_no - 1].strip()
        return ""
