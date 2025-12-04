"""
StyleAgent - Agente especializado en deteccion de violaciones de estilo PEP 8.

Este agente analiza codigo Python en busca de problemas de estilo incluyendo:
- Violaciones de PEP 8 (longitud de linea, espacios, etc.)
- Docstrings faltantes en funciones y clases publicas
- Organizacion y uso de imports
- Convenciones de nombres
(PEP 8: snake_case para funciones/variables, PascalCase para clases)
- Hallazgos externos de Pylint y Flake8
"""

import ast
import re
from typing import Dict, List, Set

from src.agents.analyzers import flake8_analyzer, pylint_analyzer
from src.agents.base_agent import BaseAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding, Severity


class StyleAgent(BaseAgent):
    """Agente especializado en detectar violaciones de estilo en codigo Python.

    Analiza el codigo usando multiples estrategias:
    1. Analisis de lineas (longitud, espacios)
    2. Analisis AST para docstrings en funciones y clases publicas
    3. Analisis AST para organizacion de imports
    4. Analisis AST para convenciones de nombres PEP 8
    5. Integracion interna con Pylint y Flake8
    """

    # Limite por defecto de longitud de linea
    LINE_LENGTH_LIMIT: int = 88

    # Patrones de nombres PEP 8
    FUNCTION_NAME_PATTERN: str = r"^[a-z_][a-z0-9_]*$"
    CLASS_NAME_PATTERN: str = r"^[A-Z][a-zA-Z0-9]*$"
    CONSTANT_NAME_PATTERN: str = r"^[A-Z_][A-Z0-9_]*$"
    VARIABLE_NAME_PATTERN: str = r"^[a-z_][a-z0-9_]*$"

    def __init__(self) -> None:
        """
        Inicializa StyleAgent con configuracion por defecto.
        """
        super().__init__(name="StyleAgent", version="1.0.0", category="style", enabled=True)
        # Usa el limite de clase por defecto
        self.line_length_limit = self.LINE_LENGTH_LIMIT
        # Analizadores externos
        self.pylint_analyzer = pylint_analyzer.PylintAnalyzer()
        self.flake8_analyzer = flake8_analyzer.Flake8Analyzer()
        self.logger.info("StyleAgent inicializado con 6 modulos de analisis de estilo.")

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        """
        Analiza codigo Python en busca de violaciones de estilo.

        Ejecuta varios chequeos de estilo:
        1. Longitud de linea y espacios basicos
        2. Docstrings faltantes
        3. Problemas en imports
        4. Convenciones de nombres
        5. Pylint (si esta disponibles en el entorno)
        6. Flake8 (si esta disponibles en el entorno)

        Args:
            context: Contexto de analisis con el codigo a revisar.

        Returns:
            Lista de Finding ordenada por numero de linea.
        """
        # Emitir evento de inicio
        self._emit_agent_started(context)

        self.log_info(f"Iniciando analisis de estilo para {context.filename}")
        findings: List[Finding] = []

        try:
            # Modulo 1: estilo de lineas
            line_findings = self._check_line_style(context)
            findings.extend(line_findings)
            self.log_debug(f"Estilo de lineas: {len(line_findings)} hallazgos")

            # Modulo 2: docstrings
            docstring_findings = self._check_docstrings(context)
            findings.extend(docstring_findings)
            self.log_debug(f"Docstrings: {len(docstring_findings)} hallazgos")

            # Modulo 3: imports
            import_findings = self._check_imports(context)
            findings.extend(import_findings)
            self.log_debug(f"Imports: {len(import_findings)} hallazgos")

            # Modulo 4: convenciones de nombres
            naming_findings = self._check_naming_conventions(context)
            findings.extend(naming_findings)
            self.log_debug(f"Convenciones de nombres: {len(naming_findings)} hallazgos")

            # Modulo 5: Pylint interno (si disponible)
            pylint_findings = self._run_pylint(context)
            self.log_info(f"pylint produjo {len(pylint_findings)} hallazgos")
            findings.extend(pylint_findings)
            self.log_debug(f"Pylint: {len(pylint_findings)} hallazgos")

            # Modulo 6: Flake8 interno (si disponible)
            flake8_findings = self._run_flake8(context)
            findings.extend(flake8_findings)
            self.log_debug(f"Flake8: {len(flake8_findings)} hallazgos")

        except SyntaxError as e:
            self.log_error(
                f"Error de sintaxis en {context.filename}: {e}. "
                "Algunos modulos de analisis pueden tener resultados incompletos."
            )
            # Emitir evento de fallo pero continuar con findings parciales
            self._emit_agent_failed(context, e)

        except Exception as e:
            self.log_error(f"Error inesperado en analisis de estilo: {e}")
            self._emit_agent_failed(context, e)
            raise

        # Eliminar duplicados y ordenar hallazgos por numero de linea
        findings = self._remove_duplicates(findings)
        findings.sort(key=lambda f: f.line_number)

        self.log_info(f"Analisis de estilo completado: {len(findings)} hallazgos")

        # Emitir evento de completado
        self._emit_agent_completed(context, findings)

        return findings

    # ---------------------------------------------------------------------
    # Modulo 1: estilo de lineas
    # ---------------------------------------------------------------------
    def _check_line_style(self, context: AnalysisContext) -> List[Finding]:
        """
        Detecta problemas basicos de estilo a nivel de linea.

        Verifica:
        - Lineas que exceden line_length_limit
        - Espacios en blanco al final de la linea
        - Caracteres de tabulacion en la indentacion
        - Mas de dos lineas en blanco consecutivas
        """
        findings: List[Finding] = []
        lines = context.code_content.splitlines()
        blank_run = 0

        for line_num, line in enumerate(lines, start=1):
            stripped = line.rstrip("\n")

            # Contar lineas en blanco consecutivas
            if stripped.strip() == "":
                blank_run += 1
            else:
                blank_run = 0

            # Linea demasiado larga
            if len(stripped) > self.line_length_limit:
                findings.append(
                    Finding(
                        severity=Severity.LOW,
                        issue_type="style/pep8",
                        message=(
                            f"La linea excede la longitud maxima de "
                            f"{self.line_length_limit} caracteres"
                        ),
                        line_number=line_num,
                        code_snippet=self._get_code_snippet(context, line_num),
                        suggestion=(
                            "Divide la expresion en varias lineas o usa parentesis "
                            "para agrupar expresiones largas"
                        ),
                        agent_name=self.name,
                        rule_id="STYLE001_LINE_LENGTH",
                    )
                )

            # Espacios en blanco al final de la linea
            if stripped.rstrip(" \t") != stripped:
                findings.append(
                    Finding(
                        severity=Severity.LOW,
                        issue_type="style/pep8",
                        message="La linea tiene espacios en blanco al final",
                        line_number=line_num,
                        code_snippet=self._get_code_snippet(context, line_num),
                        suggestion="Elimina espacios o tabs al final de la linea",
                        agent_name=self.name,
                        rule_id="STYLE002_TRAILING_WS",
                    )
                )

            # Tabs en la indentacion
            if re.match(r"^\t+", line) or re.match(r"^ +\t+", line):
                findings.append(
                    Finding(
                        severity=Severity.MEDIUM,
                        issue_type="style/pep8",
                        message="Se usan caracteres de tabulacion en la indentacion",
                        line_number=line_num,
                        code_snippet=self._get_code_snippet(context, line_num),
                        suggestion="Usa 4 espacios por nivel de indentacion en lugar de tabs",
                        agent_name=self.name,
                        rule_id="STYLE003_TABS",
                    )
                )

            # Mas de dos lineas en blanco consecutivas
            if blank_run > 2:
                findings.append(
                    Finding(
                        severity=Severity.LOW,
                        issue_type="style/pep8",
                        message="Hay mas de dos lineas en blanco consecutivas",
                        line_number=line_num,
                        code_snippet=self._get_code_snippet(context, line_num),
                        suggestion="Reduce las lineas en blanco consecutivas a maximo dos",
                        agent_name=self.name,
                        rule_id="STYLE004_BLANK_LINES",
                    )
                )

        return findings

    # ---------------------------------------------------------------------
    # Modulo 2: docstrings
    # ---------------------------------------------------------------------
    def _check_docstrings(self, context: AnalysisContext) -> List[Finding]:
        """
        Detecta docstrings faltantes en funciones y clases publicas.
        """
        findings: List[Finding] = []

        try:
            tree = ast.parse(context.code_content)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
                if not self._is_public_member(name):
                    continue

                doc = ast.get_docstring(node)
                if not doc:
                    if isinstance(node, ast.AsyncFunctionDef):
                        node_type = "funcion asincrona"
                    elif isinstance(node, ast.ClassDef):
                        node_type = "clase"
                    else:
                        node_type = "funcion"

                    findings.append(
                        Finding(
                            severity=Severity.LOW,
                            issue_type="style/documentation",
                            message=f"La {node_type} publica '{name}' no tiene docstring",
                            line_number=node.lineno,
                            code_snippet=self._get_code_snippet(context, node.lineno),
                            suggestion=(
                                "Agrega un docstring descriptivo que explique el "
                                "comportamiento, parametros y valor de retorno"
                            ),
                            agent_name=self.name,
                            rule_id="STYLE010_MISSING_DOCSTRING",
                        )
                    )

        return findings

    # ---------------------------------------------------------------------
    # Modulo 3: imports
    # ---------------------------------------------------------------------
    def _check_imports(self, context: AnalysisContext) -> List[Finding]:  # noqa: C901
        """
        Detecta problemas basicos en imports:
        - Imports no usados
        - Imports duplicados
        """
        findings: List[Finding] = []

        try:
            tree = ast.parse(context.code_content)
        except SyntaxError:
            return findings

        imported: Dict[str, List[int]] = {}
        used_names: Set[str] = set()

        # Recolectar imports y usos de nombres
        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    alias_name = alias.asname or alias.name
                    imported.setdefault(alias_name, []).append(node.lineno)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    alias_name = alias.asname or alias.name
                    imported.setdefault(alias_name, []).append(node.lineno)

            # Uso de nombres
            if isinstance(node, ast.Name):
                used_names.add(node.id)

        # Detectar imports no usados
        for name, lines in imported.items():
            if name not in used_names:
                for line in lines:
                    findings.append(
                        Finding(
                            severity=Severity.LOW,
                            issue_type="style/imports",
                            message=f"El nombre importado '{name}' no se usa en el archivo",
                            line_number=line,
                            code_snippet=self._get_code_snippet(context, line),
                            suggestion="Elimina imports no usados para mantener el codigo limpio",
                            agent_name=self.name,
                            rule_id="STYLE020_UNUSED_IMPORT",
                        )
                    )

        # Detectar imports duplicados
        for name, lines in imported.items():
            if len(lines) > 1:
                for line in lines[1:]:
                    findings.append(
                        Finding(
                            severity=Severity.LOW,
                            issue_type="style/imports",
                            message=f"El nombre '{name}' se importa multiples veces",
                            line_number=line,
                            code_snippet=self._get_code_snippet(context, line),
                            suggestion="Conserva una sola instruccion de import por nombre",
                            agent_name=self.name,
                            rule_id="STYLE021_DUP_IMPORT",
                        )
                    )

        return findings

    # ---------------------------------------------------------------------
    # Modulo 4: convenciones de nombres
    # ---------------------------------------------------------------------
    def _check_naming_conventions(self, context: AnalysisContext) -> List[Finding]:  # noqa: C901
        """
        Detecta violaciones de convenciones de nombres para funciones, clases y variables.
        """
        findings: List[Finding] = []

        try:
            tree = ast.parse(context.code_content)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            # Funciones
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if self._is_public_member(name) and not self._matches_pattern(
                    name, self.FUNCTION_NAME_PATTERN
                ):
                    findings.append(
                        Finding(
                            severity=Severity.LOW,
                            issue_type="style/naming",
                            message=f"El nombre de funcion '{name}' debe usar snake_case",
                            line_number=node.lineno,
                            code_snippet=self._get_code_snippet(context, node.lineno),
                            suggestion=(
                                "Renombra la funcion para seguir snake_case "
                                "(por ejemplo: mi_funcion_principal)"
                            ),
                            agent_name=self.name,
                            rule_id="STYLE030_FUNC_NAMING",
                        )
                    )

            # Clases
            if isinstance(node, ast.ClassDef):
                name = node.name
                if self._is_public_member(name) and not self._matches_pattern(
                    name, self.CLASS_NAME_PATTERN
                ):
                    findings.append(
                        Finding(
                            severity=Severity.LOW,
                            issue_type="style/naming",
                            message=f"El nombre de clase '{name}' debe usar PascalCase",
                            line_number=node.lineno,
                            code_snippet=self._get_code_snippet(context, node.lineno),
                            suggestion=(
                                "Renombra la clase para seguir PascalCase "
                                "(por ejemplo: MiClasePrincipal)"
                            ),
                            agent_name=self.name,
                            rule_id="STYLE031_CLASS_NAMING",
                        )
                    )

            # Asignaciones simples para variables y constantes
            if isinstance(node, ast.Assign):
                if not node.targets:
                    continue
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    name = target.id
                    # Posible constante: todo en mayusculas
                    if name.isupper():
                        if not self._matches_pattern(name, self.CONSTANT_NAME_PATTERN):
                            findings.append(
                                Finding(
                                    severity=Severity.LOW,
                                    issue_type="style/naming",
                                    message=(
                                        f"El nombre de constante '{name}' debe usar "
                                        "UPPER_SNAKE_CASE"
                                    ),
                                    line_number=node.lineno,
                                    code_snippet=self._get_code_snippet(context, node.lineno),
                                    suggestion=(
                                        "Renombra la constante para usar UPPER_SNAKE_CASE "
                                        "(por ejemplo: MI_CONSTANTE)"
                                    ),
                                    agent_name=self.name,
                                    rule_id="STYLE032_CONST_NAMING",
                                )
                            )
                    else:
                        # Variable regular
                        if not self._matches_pattern(name, self.VARIABLE_NAME_PATTERN):
                            findings.append(
                                Finding(
                                    severity=Severity.LOW,
                                    issue_type="style/naming",
                                    message=(
                                        f"El nombre de variable '{name}' debe usar snake_case"
                                    ),
                                    line_number=node.lineno,
                                    code_snippet=self._get_code_snippet(context, node.lineno),
                                    suggestion=(
                                        "Renombra la variable para usar snake_case "
                                        "(por ejemplo: mi_variable)"
                                    ),
                                    agent_name=self.name,
                                    rule_id="STYLE033_VAR_NAMING",
                                )
                            )

        return findings

    # ---------------------------------------------------------------------
    # Modulo 5: Pylint con analizador
    # ---------------------------------------------------------------------
    def _run_pylint(self, context: AnalysisContext) -> List[Finding]:
        """
        Ejecuta pylint usando PylintAnalyzer.

        Si pylint no esta disponible en el entorno, devuelve una lista vacia.
        """
        findings: List[Finding] = []

        try:
            findings = self.pylint_analyzer.analyze(
                code_content=context.code_content,
                agent_name=self.name,
            )
            self.log_debug(f"PylintAnalyzer retorno {len(findings)} hallazgos")
        except FileNotFoundError:
            # pylint no esta instalado en este entorno
            self.log_info("pylint no disponible; se omiten hallazgos externos de pylint")
        except Exception as exc:
            # No romper todo el analisis si pylint falla
            self.log_error(f"Error ejecutando PylintAnalyzer: {exc}")

        return findings

    # ---------------------------------------------------------------------
    # Modulo 6: Flake8 con analizador
    # ---------------------------------------------------------------------
    def _run_flake8(self, context: AnalysisContext) -> List[Finding]:
        """
        Ejecuta flake8 usando Flake8Analyzer.

        Si flake8 no esta disponible en el entorno, devuelve una lista vacia.
        """
        findings: List[Finding] = []

        try:
            findings = self.flake8_analyzer.analyze(
                code_content=context.code_content,
                agent_name=self.name,
            )
            self.log_debug(f"Flake8Analyzer retorno {len(findings)} hallazgos")
        except FileNotFoundError:
            # flake8 no esta instalado o no esta en PATH
            self.log_debug("flake8 no disponible; se omiten hallazgos externos de flake8")
        except Exception as exc:
            # No romper todo el analisis si flake8 falla
            self.log_error(f"Error ejecutando Flake8Analyzer: {exc}")

        return findings

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _remove_duplicates(self, findings: List[Finding]) -> List[Finding]:
        """
        Elimina hallazgos duplicados manteniendo el primero.
        """
        seen: Set[tuple] = set()
        unique_findings: List[Finding] = []

        for finding in findings:
            key = (
                finding.line_number,
                finding.issue_type,
                finding.rule_id,
                finding.agent_name,
            )
            if key not in seen:
                seen.add(key)
                unique_findings.append(finding)

        return unique_findings

    def _get_code_snippet(
        self,
        context: AnalysisContext,
        line_number: int,
        context_lines: int = 0,
    ) -> str:
        """
        Extrae un fragmento de codigo alrededor de una linea dada.
        """
        lines = context.code_content.splitlines()

        if 1 <= line_number <= len(lines):
            start = max(0, line_number - 1 - context_lines)
            end = min(len(lines), line_number + context_lines)
            snippet_lines = lines[start:end]
            return "\n".join(snippet_lines)

        return ""

    def _is_public_member(self, name: str) -> bool:
        """
        Determina si un miembro (funcion, clase o variable) es publico.

        Un miembro publico no empieza con guion bajo.
        """
        return not name.startswith("_")

    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """
        Verifica si un nombre cumple con el patron regex dado.
        """
        return bool(re.match(pattern, name))
