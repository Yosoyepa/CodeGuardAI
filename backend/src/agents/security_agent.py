"""
SecurityAgent - Agente especializado en detección de vulnerabilidades de seguridad.

Este agente analiza código Python en busca de problemas de seguridad comunes incluyendo:
- Funciones peligrosas (eval, exec, pickle, etc.)
- Vulnerabilidades de inyección SQL
- Credenciales hardcodeadas (contraseñas, API keys, tokens)
- Algoritmos criptográficos débiles (MD5, SHA1, DES)
"""

import ast
import re
from typing import Dict, List, Optional, Set

from src.agents.base_agent import BaseAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding, Severity


class SecurityAgent(BaseAgent):
    """
    Agente especializado en detectar vulnerabilidades de seguridad en código Python.

    Analiza el código usando múltiples estrategias de detección:
    1. Análisis AST (Abstract Syntax Tree) para funciones peligrosas
    2. Coincidencia de patrones regex para inyección SQL
    3. Regex y detección de placeholders para credenciales hardcodeadas
    4. Análisis AST para algoritmos criptográficos débiles

    Atributos:
        DANGEROUS_FUNCTIONS: Conjunto de nombres de funciones consideradas peligrosas
        SQL_INJECTION_PATTERNS: Patrones regex para detección de inyección SQL
        CREDENTIAL_PATTERNS: Patrones regex para detección de credenciales
        WEAK_CRYPTO_ALGORITHMS: Conjunto de nombres de algoritmos criptográficos débiles

    Ejemplo:
        >>> agent = SecurityAgent()
        >>> context = AnalysisContext(
        ...     code_content="result = eval(user_input)",
        ...     filename="vulnerable.py"
        ... )
        >>> findings = agent.analyze(context)
        >>> assert len(findings) >= 1
        >>> assert findings[0].severity == Severity.CRITICAL
    """

    # Funciones peligrosas que permiten ejecución arbitraria de código
    DANGEROUS_FUNCTIONS: Set[str] = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "execfile",  # Python 2
    }

    # Funciones peligrosas de pickle/serialización
    PICKLE_FUNCTIONS: Set[str] = {
        "pickle.loads",
        "pickle.load",
        "cPickle.loads",
        "cPickle.load",
        "yaml.load",  # Sin argumento Loader
        "marshal.loads",
    }

    # Patrones de inyección SQL (regex) - CORREGIDOS
    SQL_INJECTION_PATTERNS: List[str] = [
        r'execute\s*\(\s*["\'].*\+',  # Concatenación con +
        r'execute\s*\(\s*f["\']',  # f-strings en execute directo
        r'execute\s*\(\s*["\'].*%s',  # %s formatting
        r'execute\s*\(\s*["\'].*\.format',  # .format() en execute
        r'\.execute\s*\(\s*["\'].*\+\s*\w',  # execute con concatenación y variable
    ]

    # Patrones de credenciales (regex)
    CREDENTIAL_PATTERNS: List[dict] = [
        {
            "pattern": r'password\s*=\s*["\'][^"\']{8,}["\']',
            "name": "password",
            "severity": Severity.CRITICAL,
        },
        {
            "pattern": r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']',
            "name": "api_key",
            "severity": Severity.CRITICAL,
        },
        {
            "pattern": r'secret[_-]?key\s*=\s*["\'][^"\']{10,}["\']',
            "name": "secret_key",
            "severity": Severity.CRITICAL,
        },
        {
            "pattern": r'token\s*=\s*["\'][^"\']{10,}["\']',
            "name": "token",
            "severity": Severity.HIGH,
        },
        {
            "pattern": r'access[_-]?key\s*=\s*["\'][^"\']{10,}["\']',
            "name": "access_key",
            "severity": Severity.HIGH,
        },
    ]

    # Placeholders a ignorar (no son credenciales reales)
    PLACEHOLDER_PATTERNS: List[str] = [
        r"YOUR_",
        r"REPLACE_",
        r"CHANGE_",
        r"TODO",
        r"FIXME",
        r"example",
        r"test",
        r"dummy",
        r"<.*>",
        r"\*+",
        r"xxx+",
    ]

    # Algoritmos criptográficos débiles
    WEAK_CRYPTO_ALGORITHMS: Set[str] = {
        "md5",
        "sha1",
        "DES",
        "RC4",
        "Blowfish",
    }

    SQL_INJECTION_MESSAGE = (
        "Posible vulnerabilidad de inyección SQL detectada - "
        "entrada de usuario concatenada o formateada en consulta"
    )
    SQL_INJECTION_SUGGESTION = (
        "Use parameterized queries or an ORM: "
        "cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))"
    )

    def __init__(self):
        """Inicializa SecurityAgent con reglas de seguridad predefinidas."""
        super().__init__(name="SecurityAgent", version="1.0.0", category="security", enabled=True)
        self.logger.info("SecurityAgent inicializado con 4 módulos de detección")

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        """
        Analiza código Python en busca de vulnerabilidades de seguridad.

        Ejecuta 4 tipos de análisis de seguridad:
        1. Detección de funciones peligrosas (eval, exec, etc.)
        2. Detección de patrones de inyección SQL
        3. Detección de credenciales hardcodeadas
        4. Detección de criptografía débil

        Args:
            context: Contexto de análisis que contiene el código y metadata

        Returns:
            Lista de hallazgos de seguridad, ordenados por severidad (CRITICAL primero)

        Raises:
            SyntaxError: Si el código tiene sintaxis Python inválida (se registra, no se lanza)

        Ejemplo:
            >>> agent = SecurityAgent()
            >>> context = AnalysisContext(
            ...     code_content="password = 'MySecret123'",
            ...     filename="config.py"
            ... )
            >>> findings = agent.analyze(context)
            >>> assert any(f.issue_type == "hardcoded_credentials" for f in findings)
        """
        self.log_info(f"Iniciando análisis de seguridad para {context.filename}")
        findings: List[Finding] = []

        try:
            # Módulo 1: Detectar funciones peligrosas
            dangerous_findings = self._detect_dangerous_functions(context)
            findings.extend(dangerous_findings)
            self.log_debug(f"Funciones peligrosas: {len(dangerous_findings)} hallazgos")

            # Módulo 2: Detectar patrones de inyección SQL (regex + AST)
            sql_findings = self._detect_sql_injection(context)
            findings.extend(sql_findings)
            self.log_debug(f"Inyección SQL: {len(sql_findings)} hallazgos")

            # Módulo 3: Detectar credenciales hardcodeadas
            credential_findings = self._detect_hardcoded_credentials(context)
            findings.extend(credential_findings)
            self.log_debug(f"Credenciales hardcodeadas: {len(credential_findings)} hallazgos")

            # Módulo 4: Detectar criptografía débil
            crypto_findings = self._detect_weak_crypto(context)
            findings.extend(crypto_findings)
            self.log_debug(f"Criptografía débil: {len(crypto_findings)} hallazgos")

        except SyntaxError as e:
            self.log_error(
                f"Error de sintaxis en {context.filename}: {e}. "
                "Algunos módulos de análisis pueden tener resultados incompletos."
            )
            # Continuar con hallazgos de módulos que no necesitan análisis AST

        # Ordenar hallazgos por severidad (CRITICAL primero)
        findings.sort(
            key=lambda f: (["critical", "high", "medium", "low", "info"].index(f.severity.value))
        )

        self.log_info(
            f"Análisis de seguridad completado: {len(findings)} hallazgos "
            f"({sum(1 for f in findings if f.is_critical)} críticos)"
        )

        return findings

    def _detect_dangerous_functions(self, context: AnalysisContext) -> List[Finding]:
        """
        Detecta funciones peligrosas como eval(), exec() usando análisis AST.

        Args:
            context: Contexto de análisis con el código a analizar

        Returns:
            Lista de hallazgos para uso de funciones peligrosas
        """
        findings: List[Finding] = []

        try:
            tree = ast.parse(context.code_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node)

                    # Verificar funciones peligrosas directas
                    if func_name in self.DANGEROUS_FUNCTIONS:
                        finding = Finding(
                            severity=Severity.CRITICAL,
                            issue_type="dangerous_function",
                            message=(
                                f"Uso de {func_name}() detectado - "
                                "permite ejecución arbitraria de código"
                            ),
                            line_number=node.lineno,
                            code_snippet=self._get_code_snippet(context, node.lineno),
                            suggestion=self._get_dangerous_function_suggestion(func_name),
                            agent_name=self.name,
                            rule_id=f"SEC001_{func_name.upper()}",
                        )
                        findings.append(finding)

                    # Verificar funciones de pickle/serialización
                    elif func_name in self.PICKLE_FUNCTIONS:
                        finding = Finding(
                            severity=Severity.HIGH,
                            issue_type="unsafe_deserialization",
                            message=(
                                f"Uso de {func_name} detectado - "
                                "puede ejecutar código arbitrario durante "
                                "deserialización"
                            ),
                            line_number=node.lineno,
                            code_snippet=self._get_code_snippet(context, node.lineno),
                            suggestion=(
                                "Use json.loads() for data deserialization or "
                                "validate pickle sources"
                            ),
                            agent_name=self.name,
                            rule_id="SEC001_PICKLE",
                        )
                        findings.append(finding)

        except SyntaxError:
            # El código fuente puede estar incompleto o contener errores de sintaxis.
            # Ignoramos el error porque no se puede analizar AST en código inválido.
            pass

        return findings

    def _detect_sql_injection(self, context: AnalysisContext) -> List[Finding]:
        """
        Detecta vulnerabilidades de inyección SQL usando patrones regex mejorados.

        Detecta múltiples patrones comunes de SQL injection:
        - Concatenación de strings con +
        - Formateo con %s
        - F-strings con {}
        - .format() en queries
        - Palabras clave SQL con variables

        Args:
            context: Contexto de análisis con el código a analizar

        Returns:
            Lista de hallazgos para vulnerabilidades de inyección SQL
        """
        findings: List[Finding] = []
        found_sql_lines: Set[int] = set()

        findings.extend(self._detect_sql_injection_patterns(context, found_sql_lines))
        findings.extend(self._detect_sql_injection_ast(context, found_sql_lines))
        return findings

    def _detect_sql_injection_patterns(
        self, context: AnalysisContext, found_sql_lines: Set[int]
    ) -> List[Finding]:
        """Analiza línea por línea usando regex para detectar SQL injection directa."""
        findings: List[Finding] = []
        lines = context.code_content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or line_num in found_sql_lines:
                continue

            for pattern in self.SQL_INJECTION_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE | re.MULTILINE):
                    findings.append(
                        Finding(
                            severity=Severity.HIGH,
                            issue_type="sql_injection",
                            message=self.SQL_INJECTION_MESSAGE,
                            line_number=line_num,
                            code_snippet=stripped,
                            suggestion=self.SQL_INJECTION_SUGGESTION,
                            agent_name=self.name,
                            rule_id="SEC002_SQL_INJECTION",
                        )
                    )
                    found_sql_lines.add(line_num)
                    break

        return findings

    def _detect_sql_injection_ast(
        self, context: AnalysisContext, found_sql_lines: Set[int]
    ) -> List[Finding]:
        """Analiza el AST para detectar queries construidas antes de ejecutar."""
        findings: List[Finding] = []
        suspicious_vars = self._collect_suspicious_query_assignments(context)
        if not suspicious_vars:
            return findings

        execute_calls = self._find_execute_calls(context)
        for line_num, argument in execute_calls:
            if line_num not in found_sql_lines and self._is_suspicious_execute_arg(
                argument, suspicious_vars
            ):
                findings.append(
                    Finding(
                        severity=Severity.HIGH,
                        issue_type="sql_injection",
                        message=self.SQL_INJECTION_MESSAGE,
                        line_number=line_num,
                        code_snippet=self._get_code_snippet(context, line_num),
                        suggestion=self.SQL_INJECTION_SUGGESTION,
                        agent_name=self.name,
                        rule_id="SEC002_SQL_INJECTION",
                    )
                )
                found_sql_lines.add(line_num)

        return findings

    @staticmethod
    def _collect_suspicious_query_assignments(
        context: AnalysisContext,
    ) -> Dict[str, str]:
        """Construye un mapa de variables que contienen posibles queries inseguras."""
        suspicious_vars: Dict[str, str] = {}
        try:
            tree = ast.parse(context.code_content)
        except SyntaxError:
            return suspicious_vars

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and node.targets:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    assignment_type = SecurityAgent._classify_sql_assignment(node.value)
                    if assignment_type:
                        suspicious_vars[target.id] = assignment_type
        return suspicious_vars

    @staticmethod
    def _find_execute_calls(context: AnalysisContext) -> List[tuple[int, ast.AST]]:
        """Obtiene las llamadas a execute() con su línea y primer argumento."""
        execute_calls: List[tuple[int, ast.AST]] = []
        try:
            tree = ast.parse(context.code_content)
        except SyntaxError:
            return execute_calls

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute"
                and node.args
            ):
                line_num = getattr(node, "lineno", 1)
                execute_calls.append((line_num, node.args[0]))
        return execute_calls

    @staticmethod
    def _classify_sql_assignment(value: ast.AST) -> Optional[str]:
        """Clasifica asignaciones sospechosas de queries."""
        if isinstance(value, ast.JoinedStr):
            return "fstring"
        if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
            return "concat"
        if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mod):
            return "mod"
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and value.func.attr == "format"
        ):
            return "format"
        return None

    @staticmethod
    def _is_suspicious_execute_arg(arg: ast.AST, suspicious_vars: Dict[str, str]) -> bool:
        """Determina si el argumento pasado a execute es potencialmente inseguro."""
        if isinstance(arg, ast.JoinedStr):
            return True
        if isinstance(arg, ast.BinOp) and isinstance(arg.op, (ast.Add, ast.Mod)):
            return True
        if (
            isinstance(arg, ast.Call)
            and isinstance(arg.func, ast.Attribute)
            and arg.func.attr == "format"
        ):
            return True
        if isinstance(arg, ast.Name) and arg.id in suspicious_vars:
            return True
        return False

    def _detect_hardcoded_credentials(self, context: AnalysisContext) -> List[Finding]:
        """
        Detecta credenciales hardcodeadas usando patrones regex y detección de placeholders.

        Busca patrones comunes como:
        - password = "valor"
        - api_key = "valor"
        - secret_key = "valor"
        - token = "valor"

        Filtra falsos positivos ignorando placeholders y valores cortos.

        Args:
            context: Contexto de análisis con el código a analizar

        Returns:
            Lista de hallazgos para credenciales hardcodeadas
        """
        findings: List[Finding] = []
        lines = context.code_content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            # Saltar comentarios y líneas vacías
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            for cred_config in self.CREDENTIAL_PATTERNS:
                pattern = cred_config["pattern"]
                cred_name = cred_config["name"]
                severity = cred_config["severity"]

                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value = match.group(0).split("=")[1].strip().strip("\"'")
                    if self._is_placeholder(value) or len(value) < 8:
                        continue

                    env_var = cred_name.upper()
                    finding = Finding(
                        severity=severity,
                        issue_type="hardcoded_credentials",
                        message=(
                            f"Hardcoded {cred_name} detected - secrets "
                            "should not be in source code"
                        ),
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion=(
                            f"Use environment variables: {env_var} = " f"os.getenv('{env_var}')"
                        ),
                        agent_name=self.name,
                        rule_id=f"SEC003_{env_var}",
                    )
                    findings.append(finding)
                    break  # Solo un hallazgo por línea

        return findings

    def _detect_weak_crypto(self, context: AnalysisContext) -> List[Finding]:
        """
        Detecta uso de algoritmos criptográficos débiles.

        Busca uso de:
        - hashlib.md5()
        - hashlib.sha1()
        - Crypto.Cipher.DES
        - RC4
        - Blowfish

        Args:
            context: Contexto de análisis con el código a analizar

        Returns:
            Lista de hallazgos para criptografía débil
        """
        findings: List[Finding] = []

        try:
            tree = ast.parse(context.code_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_function_name(node)
                    if not func_name:
                        continue

                    lower_name = func_name.lower()

                    # Verificar funciones débiles de hash (md5 o sha1 en cualquiera de sus formas)
                    if "md5" in lower_name or "sha1" in lower_name:
                        algo = "MD5" if "md5" in lower_name else "SHA1"
                        finding = Finding(
                            severity=Severity.MEDIUM,
                            issue_type="weak_cryptography",
                            message=f"Uso de algoritmo de hash débil {algo} detectado",
                            line_number=node.lineno,
                            code_snippet=self._get_code_snippet(context, node.lineno),
                            suggestion="Usa SHA-256 o superior: hashlib.sha256()",
                            agent_name=self.name,
                            rule_id=f"SEC004_{algo}",
                        )
                        findings.append(finding)
                        continue

                    # Verificar algoritmos débiles de encriptación en librería Crypto
                    if any(weak in func_name for weak in ["DES", "RC4", "Blowfish"]):
                        finding = Finding(
                            severity=Severity.HIGH,
                            issue_type="weak_cryptography",
                            message=(
                                "Uso de algoritmo de encriptación débil " f"detectado: {func_name}"
                            ),
                            line_number=node.lineno,
                            code_snippet=self._get_code_snippet(context, node.lineno),
                            suggestion="Usa AES-256 con Crypto.Cipher.AES",
                            agent_name=self.name,
                            rule_id="SEC004_WEAK_ENCRYPTION",
                        )
                        findings.append(finding)

        except SyntaxError:
            # El código fuente puede estar incompleto o contener errores de sintaxis.
            # Ignoramos el error porque no se puede analizar criptografía en código inválido.
            pass

        return findings

    def _get_function_name(self, node: ast.Call) -> str:
        """
        Extrae el nombre de la función de un nodo Call del AST.

        Maneja tanto llamadas simples (func()) como llamadas de atributo (module.func()).

        Args:
            node: Nodo Call del AST

        Returns:
            Nombre de la función como string (ej: "eval" o "hashlib.md5")
        """
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            return node.func.attr
        return ""

    def _get_code_snippet(
        self, context: AnalysisContext, line_number: int, context_lines: int = 0
    ) -> str:
        """
        Extrae fragmento de código alrededor de la línea especificada.

        Args:
            context: Contexto de análisis con el código
            line_number: Número de línea (1-based) a extraer
            context_lines: Número de líneas antes/después a incluir

        Returns:
            Fragmento de código como string
        """
        lines = context.code_content.splitlines()

        if 1 <= line_number <= len(lines):
            start = max(0, line_number - 1 - context_lines)
            end = min(len(lines), line_number + context_lines)
            snippet_lines = lines[start:end]
            return "\n".join(snippet_lines)

        return ""

    def _get_dangerous_function_suggestion(self, func_name: str) -> str:
        """
        Obtiene sugerencia específica para el uso de función peligrosa.

        Args:
            func_name: Nombre de la función peligrosa

        Returns:
            String con sugerencia de alternativa segura
        """
        suggestions = {
            "eval": "Use ast.literal_eval() for safe evaluation of literals",
            "exec": "Avoid exec() or validate input strictly with whitelisting",
            "compile": "Avoid compile() or validate source code strictly",
            "__import__": "Use importlib.import_module() with validation",
            "execfile": "Use with open() and exec() with strict validation (Python 2 only)",
        }
        return suggestions.get(func_name, f"Avoid using {func_name}() or validate input strictly")

    def _is_placeholder(self, value: str) -> bool:
        """
        Verifica si un valor de credencial es un placeholder (no un secreto real).

        Ignora valores que contienen patrones comunes de placeholders como:
        - YOUR_, REPLACE_, CHANGE_
        - TODO, FIXME
        - example, test, dummy

        Args:
            value: Valor de credencial a verificar

        Returns:
            True si el valor es un placeholder, False en caso contrario
        """
        value_lower = value.lower()

        for pattern in self.PLACEHOLDER_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True

        return False