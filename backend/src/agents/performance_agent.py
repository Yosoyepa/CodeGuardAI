"""
PerformanceAgent - Agente especializado en análisis de rendimiento de código Python.

Este agente analiza el AST (Abstract Syntax Tree) para detectar patrones de código
que pueden causar problemas de rendimiento, complejidad temporal excesiva o fugas de recursos.
"""

import ast
from typing import List, Set, Tuple

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
        self.loop_depth = 0
        self.in_loop = False

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
            self.findings_data.append({
                "type": "complexity",
                "node": node,
                "depth": self.loop_depth + 1
            })

    def visit_Call(self, node: ast.Call):
        """Detecta llamadas a funciones ineficientes o mal gestionadas."""
        self._check_resource_leak(node)
        self._check_inefficient_collection_ops(node)
        self._check_n_plus_one_query(node)
        self._check_memory_intensive(node)
        self.generic_visit(node)

    def _check_resource_leak(self, node: ast.Call):
        """Detecta uso de open() o socket() fuera de un contexto 'with'."""
        # Detectar open()
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            self.findings_data.append({
                "type": "resource_leak",
                "resource": "file",
                "node": node
            })
        # Detectar socket.socket()
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "socket":
            # Asumimos que viene de módulo socket, aunque es heurístico
            self.findings_data.append({
                "type": "resource_leak",
                "resource": "socket",
                "node": node
            })

    def _check_inefficient_collection_ops(self, node: ast.Call):
        """Detecta operaciones O(n) dentro de bucles."""
        if not self.in_loop:
            return

        # Detectar list.insert(0, ...)
        if isinstance(node.func, ast.Attribute) and node.func.attr == "insert":
            if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                self.findings_data.append({
                    "type": "inefficient_insert",
                    "node": node
                })

    def _check_n_plus_one_query(self, node: ast.Call):
        """Detecta el problema N+1: Consultas a BD dentro de bucles."""
        if not self.in_loop:
            return

        method_name = ""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
        
        if method_name in self.DB_METHODS:
            self.findings_data.append({
                "type": "n_plus_one",
                "method": method_name,
                "node": node
            })

    def _check_memory_intensive(self, node: ast.Call):
        """Detecta operaciones que cargan datos sin límites en memoria."""
        method_name = ""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
        
        if method_name in self.MEMORY_INTENSIVE_METHODS:
            # Si se llama sin argumentos (ej: f.read()), lee todo el archivo
            if not node.args:
                self.findings_data.append({
                    "type": "memory_intensive",
                    "method": method_name,
                    "node": node
                })

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
                
                self.findings_data.append({
                    "type": "linear_search",
                    "node": node
                })
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
            name="PerformanceAgent",
            version="1.1.0",
            category="performance",
            enabled=True
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
            
            # 1. Validar uso de 'with' para recursos
            safe_resource_lines = self._find_safe_resource_calls(tree)

            # 2. Ejecutar el visitante principal
            visitor = PerformanceVisitor()
            visitor.visit(tree)

            for item in visitor.findings_data:
                finding = self._create_finding(item, context, safe_resource_lines)
                if finding:
                    findings.append(finding)

            # Ordenar hallazgos por severidad (CRITICAL primero)
            findings.sort(
                key=lambda f: (["critical", "high", "medium", "low", "info"].index(f.severity.value))
            )

            self._emit_agent_completed(context, findings)

        except SyntaxError as e:
            self.log_error(f"Error de sintaxis al analizar rendimiento: {e}")
        except Exception as e:
            self._emit_agent_failed(context, e)
            self.log_error(f"Error inesperado en PerformanceAgent: {e}")

        return findings

    def _find_safe_resource_calls(self, tree: ast.AST) -> Set[int]:
        """Identifica las líneas donde recursos se usan correctamente dentro de un 'with'."""
        safe_lines = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        func = item.context_expr.func
                        # Detectar open()
                        if isinstance(func, ast.Name) and func.id == "open":
                            safe_lines.add(item.context_expr.lineno)
                        # Detectar socket.socket()
                        elif isinstance(func, ast.Attribute) and func.attr == "socket":
                            safe_lines.add(item.context_expr.lineno)
        return safe_lines

    def _create_finding(self, item: dict, context: AnalysisContext, safe_lines: Set[int]) -> Finding | None:
        """Convierte los datos crudos del visitante en objetos Finding."""
        node = item["node"]
        issue_type = item["type"]
        
        if issue_type == "complexity":
            depth = item['depth']
            severity = Severity.CRITICAL if depth >= 3 else Severity.HIGH
            
            return Finding(
                severity=severity,
                issue_type="performance/complexity",
                message=f"Posible complejidad O(n^{depth}) detectada por bucles anidados.",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion="Intenta aplanar los bucles o mover el bucle interno a una función separada optimizada.",
                agent_name=self.name,
                rule_id="PERF001_NESTED_LOOPS"
            )
        
        elif issue_type == "n_plus_one":
            return Finding(
                severity=Severity.CRITICAL,
                issue_type="performance/database",
                message=f"Posible problema N+1 Query: Llamada a '{item['method']}' dentro de un bucle.",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion="Usa 'eager loading' (JOINs) o procesa los datos en lote fuera del bucle.",
                agent_name=self.name,
                rule_id="PERF004_N_PLUS_ONE"
            )

        elif issue_type == "memory_intensive":
            return Finding(
                severity=Severity.HIGH,
                issue_type="performance/memory",
                message=f"Operación de memoria intensiva '{item['method']}' sin límites detectada.",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion=f"Usa argumentos de tamaño (ej: {item['method']}(1024)) o procesa el archivo línea por línea.",
                agent_name=self.name,
                rule_id="PERF005_UNBOUNDED_MEMORY"
            )
        
        elif issue_type == "inefficient_insert":
            return Finding(
                severity=Severity.HIGH,
                issue_type="performance/inefficient-operation",
                message="Uso ineficiente de list.insert(0) dentro de un bucle (O(n)).",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion="Usa collections.deque.appendleft() o construye la lista y usa reverse().",
                agent_name=self.name,
                rule_id="PERF002_LIST_INSERT"
            )

        elif issue_type == "linear_search":
            return Finding(
                severity=Severity.MEDIUM,
                issue_type="performance/inefficient-operation",
                message="Búsqueda lineal ('in') detectada dentro de un bucle.",
                line_number=node.lineno,
                code_snippet=self._get_snippet(context, node.lineno),
                suggestion="Si la colección es grande, considera convertirla a un 'set' o 'dict' para búsquedas O(1).",
                agent_name=self.name,
                rule_id="PERF002_LINEAR_SEARCH"
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
                suggestion="Usa 'with' statement para asegurar que el recurso se libere correctamente.",
                agent_name=self.name,
                rule_id="PERF003_RESOURCE_LEAK"
            )
            
        return None

    def _get_snippet(self, context: AnalysisContext, line_no: int) -> str:
        """Extrae la línea de código correspondiente."""
        lines = context.code_content.splitlines()
        if 0 <= line_no - 1 < len(lines):
            return lines[line_no - 1].strip()
        return ""
