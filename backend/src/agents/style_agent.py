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
import os
import re
import subprocess
import sys
import tempfile
from typing import Dict, List, Set

from src.agents.base_agent import BaseAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding, Severity


class StyleAgent(BaseAgent):
    """
    Agente especializado en detectar violaciones de estilo en codigo Python.

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
        """
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

        # Eliminar duplicados y ordenar hallazgos por severidad
        findings = self._remove_duplicates(findings)
        findings.sort(
            key=lambda f: (["critical", "high", "medium", "low", "info"].index(f.severity.value))
        )

        for finding in findings:
            self.log_info(
                f"[{finding.agent_name}] {finding.severity.value.upper()} "
                f"line {finding.line_number} rule={finding.rule_id} "
                f"issue_type={finding.issue_type} msg={finding.message}"
            )

        self.log_info(f"Analisis de estilo completado: {len(findings)} hallazgos")

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
                        issue_type="line_too_long",
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
                        issue_type="trailing_whitespace",
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
                        issue_type="tab_indentation",
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
                        issue_type="multiple_blank_lines",
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
                            issue_type="missing_docstring",
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
                            issue_type="unused_import",
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
                            issue_type="duplicate_import",
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
                            issue_type="naming_convention",
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
                            issue_type="naming_convention",
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
                                    issue_type="naming_convention",
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
                                    issue_type="naming_convention",
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
    # Modulo 5: integracion interna con Pylint
    # ---------------------------------------------------------------------
    def _run_pylint(self, context: AnalysisContext) -> List[Finding]:
        """
        Ejecuta pylint sobre el codigo usando un archivo temporal.

        Si pylint no esta disponible en el entorno, devuelve una lista vacia.
        """
        findings: List[Finding] = []

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".py",
                delete=False,
                mode="w",
                encoding="utf-8",
            ) as tmp:
                tmp.write(context.code_content)
                tmp_path = tmp.name

            cmd = [
                sys.executable,
                "-m",
                "pylint",
                tmp_path,
                "--output-format=text",
                "--score=no",
                "--msg-template={line}:{column}:{msg_id}:{msg}",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            for line in result.stdout.splitlines():
                parts = line.split(":", 3)
                if len(parts) < 4:
                    continue

                line_str, _col_str, msg_id, msg = parts
                try:
                    line_number = int(line_str)
                except ValueError:
                    continue

                severity = self._map_pylint_severity(msg_id)
                findings.append(
                    Finding(
                        severity=severity,
                        issue_type="pylint_style",
                        message=msg.strip(),
                        line_number=line_number,
                        code_snippet=self._get_code_snippet(context, line_number),
                        suggestion=None,
                        agent_name=self.name,
                        rule_id=f"PYLINT_{msg_id}",
                    )
                )

        except FileNotFoundError:
            # pylint no esta instalado en este entorno
            self.log_info("pylint no disponible; se omiten hallazgos externos de pylint")
        except Exception as exc:
            self.log_error(f"Error ejecutando pylint: {exc}")
        finally:
            try:
                if "tmp_path" in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

        return findings

    def _map_pylint_severity(self, msg_id: str) -> Severity:
        """
        Mapea el prefijo del mensaje de pylint a un nivel de severidad interno.
        """
        # pylint usa prefijos como:
        # C = convention, R = refactor, W = warning, E = error, F = fatal
        if not msg_id:
            return Severity.LOW

        prefix = msg_id[0].upper()
        if prefix in ("E", "F"):
            return Severity.HIGH
        if prefix == "W":
            return Severity.MEDIUM
        if prefix in ("C", "R"):
            return Severity.LOW
        return Severity.LOW

    # ---------------------------------------------------------------------
    # Modulo 6: integracion interna con Flake8
    # ---------------------------------------------------------------------
    def _run_flake8(self, context: AnalysisContext) -> List[Finding]:
        """
        Ejecuta flake8 sobre el codigo usando un archivo temporal.

        Si flake8 no esta disponible en el entorno, devuelve una lista vacia.
        """
        findings: List[Finding] = []

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".py", delete=False, mode="w", encoding="utf-8"
            ) as tmp:
                tmp.write(context.code_content)
                tmp_path = tmp.name

            # Formato por defecto de flake8:
            # path:line:col: code message
            cmd = ["flake8", tmp_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            for line in result.stdout.splitlines():
                # path:line:col: code message...
                parts = line.split(":", 3)
                if len(parts) < 4:
                    continue

                _, line_str, col_str, rest = parts
                rest = rest.strip()
                if not rest:
                    continue

                # rest = "CODE message..."
                code_and_msg = rest.split(" ", 1)
                if len(code_and_msg) == 1:
                    code = code_and_msg[0]
                    msg_text = ""
                else:
                    code, msg_text = code_and_msg

                try:
                    line_number = int(line_str)
                except ValueError:
                    continue

                findings.append(
                    Finding(
                        severity=Severity.LOW,
                        issue_type="flake8_style",
                        message=msg_text.strip(),
                        line_number=line_number,
                        code_snippet=self._get_code_snippet(context, line_number),
                        suggestion=None,
                        agent_name=self.name,
                        rule_id=f"FLAKE8_{code}",
                    )
                )

        except FileNotFoundError:
            # flake8 no esta instalado o no esta en PATH
            self.log_debug("flake8 no disponible; se omiten hallazgos externos de flake8")
        except Exception as exc:
            self.log_error(f"Error ejecutando flake8: {exc}")
        finally:
            try:
                if "tmp_path" in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

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
