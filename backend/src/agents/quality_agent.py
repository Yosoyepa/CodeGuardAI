"""
QualityAgent - Agente especializado en análisis de calidad de código Python.
"""

import ast
import hashlib
from typing import Dict, List

try:
    from radon.complexity import cc_visit_ast as radon_visit
    from radon.metrics import mi_visit
except ImportError:
    radon_visit = None
    mi_visit = None

from src.agents.base_agent import BaseAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding, Severity


class QualityAgent(BaseAgent):
    """
    Agente especializado en analizar la calidad del código Python.
    Implementa métricas de complejidad, duplicación, longitud y mantenibilidad.
    """

    def __init__(self, event_bus=None):
        """
        Inicializa QualityAgent con reglas de calidad.

        Args:
            event_bus: EventBus para emitir eventos (opcional)
        """
        super().__init__(
            name="QualityAgent",
            version="1.0.0",
            category="quality",
            enabled=True,
            event_bus=event_bus,
        )
        # Atributos definidos en el diagrama de dominio
        self.complexity_threshold: int = 10
        self.duplication_threshold: float = 0.20
        self.function_length_threshold: int = 100

        # Atributos adicionales para funcionalidades extra
        self.maintainability_threshold: float = 50.0
        self.duplication_block_size: int = 4

        self.logger.info("QualityAgent inicializado")

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        """
        Analiza código Python en busca de problemas de calidad.

        Args:
            context (AnalysisContext): Contexto del análisis con código y metadatos.

        Returns:
            List[Finding]: Lista de hallazgos ordenados por severidad.
        """
        self._emit_agent_started(context)
        findings: List[Finding] = []

        try:
            # Parsear AST una sola vez
            try:
                ast_tree = ast.parse(context.code_content)
            except SyntaxError as e:
                self.log_error(f"Error de sintaxis al parsear AST: {e}")
                return findings

            # 1. Complejidad Ciclomática
            findings.extend(self.calculate_complexity(ast_tree))

            # 2. Duplicación de Código
            findings.extend(self.detect_code_duplication(context.code_content))

            # 3. Longitud de Funciones
            findings.extend(self.measure_function_length(ast_tree))

            # 4. Índice de Mantenibilidad
            mi_score = self.calculate_maintainability_index(context.code_content)
            if mi_score < self.maintainability_threshold:
                findings.append(self._create_mi_finding(mi_score))

            self._emit_agent_completed(context, findings)

        except Exception as e:
            self._emit_agent_failed(context, e)
            self.log_error(f"Error durante análisis de calidad: {str(e)}")

        # Ordenar hallazgos por severidad
        findings.sort(
            key=lambda f: (["critical", "high", "medium", "low", "info"].index(f.severity.value))
        )

        return findings

    def calculate_complexity(self, ast_tree: ast.AST) -> List[Finding]:
        """
        Calcula la complejidad ciclomática usando Radon sobre el AST.

        Args:
            ast_tree (ast.AST): Árbol de sintaxis abstracta del código.

        Returns:
            List[Finding]: Lista de hallazgos de complejidad que superan el umbral.
        """
        findings: List[Finding] = []
        if not radon_visit:
            return findings

        try:
            # radon.complexity.visit retorna una lista de bloques (Function, Class)
            blocks = radon_visit(ast_tree)
            for block in blocks:
                # Filtramos solo funciones/métodos
                if hasattr(block, "complexity") and block.complexity > self.complexity_threshold:
                    severity = Severity.MEDIUM
                    if block.complexity > 20:
                        severity = Severity.HIGH
                    if block.complexity > 50:
                        severity = Severity.CRITICAL

                    finding = Finding(
                        severity=severity,
                        issue_type="quality/cyclomatic-complexity",
                        message=(
                            f"Alta complejidad ciclomática detectada ({block.complexity}) "
                            f"en '{block.name}'"
                        ),
                        line_number=block.lineno,
                        code_snippet=f"def {block.name}...",
                        suggestion=(
                            f"Refactoriza '{block.name}' para reducir su complejidad "
                            f"(objetivo: < {self.complexity_threshold})."
                        ),
                        agent_name=self.name,
                        rule_id="QUAL001_COMPLEXITY",
                    )
                    findings.append(finding)
        except Exception as e:
            self.log_error(f"Error en cálculo de complejidad: {e}")

        return findings

    def detect_code_duplication(self, code: str) -> List[Finding]:
        """
        Detecta duplicación de código mediante hashing de bloques.

        Args:
            code (str): Código fuente completo a analizar.

        Returns:
            List[Finding]: Lista de hallazgos de bloques de código duplicados.
        """
        findings: List[Finding] = []
        lines = [line.strip() for line in code.splitlines()]
        block_hashes: Dict[str, List[int]] = {}
        block_size = self.duplication_block_size

        if len(lines) < block_size:
            return findings

        for i in range(len(lines) - block_size + 1):
            block_content = "".join(lines[i : i + block_size])
            if not block_content or block_content.startswith("#"):
                continue

            block_hash = hashlib.md5(block_content.encode("utf-8")).hexdigest()

            if block_hash in block_hashes:
                original_line = block_hashes[block_hash][0]
                if i > original_line + block_size:
                    finding = Finding(
                        severity=Severity.MEDIUM,
                        issue_type="quality/duplication",
                        message=(
                            f"Bloque de código duplicado "
                            f"(original en línea {original_line + 1})"
                        ),
                        line_number=i + 1,
                        code_snippet="...",
                        suggestion="Extrae la lógica duplicada a una función reutilizable",
                        agent_name=self.name,
                        rule_id="QUAL002_DUPLICATION",
                    )
                    findings.append(finding)
            else:
                block_hashes[block_hash] = [i]

        return findings

    def measure_function_length(self, ast_tree: ast.AST) -> List[Finding]:
        """
        Mide la longitud de las funciones y detecta las que exceden el umbral.

        Args:
            ast_tree (ast.AST): Árbol de sintaxis abstracta del código.

        Returns:
            List[Finding]: Lista de hallazgos de funciones demasiado largas.
        """
        findings: List[Finding] = []

        for node in ast.walk(ast_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                info = self._visit_function_def(node)
                length = info.get("length", 0)

                if length > self.function_length_threshold:
                    finding = Finding(
                        severity=Severity.MEDIUM,
                        issue_type="quality/function-length",
                        message=f"Función '{node.name}' demasiado larga ({length} líneas)",
                        line_number=node.lineno,
                        code_snippet=f"def {node.name}...",
                        suggestion=(
                            f"""Divide la función en partes más pequeñas """
                            f"""(límite: {self.function_length_threshold})"""
                        ),
                        agent_name=self.name,
                        rule_id="QUAL005_FUNCTION_LENGTH",
                    )
                    findings.append(finding)

        return findings

    def calculate_maintainability_index(self, code: str) -> float:
        """
        Calcula el índice de mantenibilidad (MI) del código.

        Args:
            code (str): Código fuente a analizar.

        Returns:
            float: Puntuación del índice de mantenibilidad (0-100).
        """
        if not mi_visit:
            return 100.0
        try:
            return mi_visit(code, True)
        except Exception:
            return 100.0

    def _visit_function_def(self, node: ast.FunctionDef) -> Dict:
        """
        Helper para extraer información de una definición de función.

        Args:
            node (ast.FunctionDef): Nodo de definición de función del AST.

        Returns:
            Dict: Diccionario con nombre, línea de inicio y longitud de la función.
        """
        length = 0
        if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
            length = node.end_lineno - node.lineno
        return {"name": node.name, "lineno": node.lineno, "length": length}

    def _create_mi_finding(self, score: float) -> Finding:
        """
        Crea un hallazgo para un índice de mantenibilidad bajo.

        Args:
            score (float): Puntuación de mantenibilidad calculada.

        Returns:
            Finding: Objeto Finding con la severidad y detalles correspondientes.
        """
        severity = Severity.MEDIUM
        if score < 20:
            severity = Severity.CRITICAL
        elif score < 40:
            severity = Severity.HIGH

        return Finding(
            severity=severity,
            issue_type="quality/maintainability-index",
            message=f"Índice de mantenibilidad bajo ({score:.2f})",
            line_number=1,
            code_snippet=None,
            suggestion="Mejora la mantenibilidad reduciendo complejidad.",
            agent_name=self.name,
            rule_id="QUAL003_MAINTAINABILITY",
        )
