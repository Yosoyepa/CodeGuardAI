"""
Flake8Analyzer - Analizador especializado para ejecutar Flake8.

Responsabilidad única: Ejecutar flake8 sobre código Python y
parsear su salida en objetos Finding.
"""

import os
import subprocess
import sys
import tempfile
from typing import List, Optional

from src.schemas.finding import Finding, Severity


class Flake8Analyzer:
    """
    Analizador que ejecuta Flake8 sobre código Python.

    Encapsula la lógica de ejecución de flake8 como subproceso
    y el parseo de su salida a objetos Finding.

    Attributes:
        _cmd_template: Lista base de comandos para ejecutar flake8.
    """

    def __init__(self) -> None:
        """Inicializa el analizador Flake8 con la plantilla de comandos."""
        self._cmd_template: List[str] = [
            sys.executable,
            "-m",
            "flake8",
            "--format=%(row)d:%(col)d:%(code)s:%(text)s",
        ]

    def analyze(
        self,
        code_content: str,
        agent_name: str = "StyleAgent",
    ) -> List[Finding]:
        """
        Ejecuta flake8 sobre el código y retorna los hallazgos.

        Args:
            code_content: Código Python a analizar.
            agent_name: Nombre del agente que solicita el análisis.

        Returns:
            Lista de Finding encontrados por Flake8.
            Lista vacía si flake8 no está disponible.
        """
        findings: List[Finding] = []
        tmp_path: Optional[str] = None

        try:
            # Crear archivo temporal con el código
            with tempfile.NamedTemporaryFile(
                suffix=".py",
                delete=False,
                mode="w",
                encoding="utf-8",
            ) as tmp:
                tmp.write(code_content)
                tmp_path = tmp.name

            # Ejecutar flake8
            cmd = self._cmd_template + [tmp_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            # Parsear salida
            findings = self._parse_output(result.stdout, code_content, agent_name)

        except FileNotFoundError:
            # flake8 no está instalado
            pass
        except Exception:
            # Otros errores - silenciar para no romper el análisis
            pass
        finally:
            # Limpiar archivo temporal
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        return findings

    def _parse_output(
        self,
        output: str,
        code_content: str,
        agent_name: str,
    ) -> List[Finding]:
        """
        Parsea la salida de flake8 y genera objetos Finding.

        Args:
            output: Salida estándar de flake8.
            code_content: Código original para extraer snippets.
            agent_name: Nombre del agente para los findings.

        Returns:
            Lista de Finding parseados.
        """
        findings: List[Finding] = []
        lines = code_content.splitlines()

        for line in output.splitlines():
            parts = line.split(":", 3)
            if len(parts) < 4:
                continue

            line_str, _col_str, code, msg = parts
            try:
                line_number = int(line_str)
            except ValueError:
                continue

            severity = self._map_severity(code)
            code_snippet = ""
            if 1 <= line_number <= len(lines):
                code_snippet = lines[line_number - 1]

            findings.append(
                Finding(
                    severity=severity,
                    issue_type="style/pep8",
                    message=msg.strip(),
                    line_number=line_number,
                    code_snippet=code_snippet,
                    suggestion=None,
                    agent_name=agent_name,
                    rule_id=f"FLAKE8_{code}",
                )
            )

        return findings

    @staticmethod
    def _map_severity(code: str) -> Severity:
        """
        Mapea el código de flake8 a severidad.

        Flake8 usa prefijos:
        - E = error (estilo) -> MEDIUM
        - W = warning -> LOW
        - F = pyflakes (errores lógicos) -> HIGH
        - C = complejidad -> MEDIUM
        - N = naming -> LOW

        Args:
            code: Código del error de flake8 (ej: E501, F401).

        Returns:
            Nivel de severidad correspondiente.
        """
        if not code:
            return Severity.LOW

        prefix = code[0].upper()
        if prefix == "F":
            return Severity.HIGH
        if prefix in ("E", "C"):
            return Severity.MEDIUM
        return Severity.LOW
