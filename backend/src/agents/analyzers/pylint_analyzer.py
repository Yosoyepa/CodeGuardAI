"""
PylintAnalyzer - Analizador especializado para ejecutar Pylint.

Responsabilidad única: Ejecutar pylint sobre código Python y
parsear su salida en objetos Finding.
"""

import os
import subprocess
import sys
import tempfile
from typing import List, Optional

from src.schemas.finding import Finding, Severity


class PylintAnalyzer:
    """
    Analizador que ejecuta Pylint sobre código Python.

    Encapsula la lógica de ejecución de pylint como subproceso
    y el parseo de su salida a objetos Finding.

    Attributes:
        _cmd_template: Lista base de comandos para ejecutar pylint.
    """

    def __init__(self) -> None:
        """Inicializa el analizador Pylint con la plantilla de comandos."""
        self._cmd_template: List[str] = [
            sys.executable,
            "-m",
            "pylint",
            "--output-format=text",
            "--score=no",
            "--msg-template={line}:{column}:{msg_id}:{msg}",
        ]

    def analyze(
        self,
        code_content: str,
        agent_name: str = "StyleAgent",
    ) -> List[Finding]:
        """
        Ejecuta pylint sobre el código y retorna los hallazgos.

        Args:
            code_content: Código Python a analizar.
            agent_name: Nombre del agente que solicita el análisis.

        Returns:
            Lista de Finding encontrados por Pylint.
            Lista vacía si pylint no está disponible.
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

            # Ejecutar pylint
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
            # pylint no está instalado
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
        Parsea la salida de pylint y genera objetos Finding.

        Args:
            output: Salida estándar de pylint.
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

            line_str, _col_str, msg_id, msg = parts
            try:
                line_number = int(line_str)
            except ValueError:
                continue

            severity = self._map_severity(msg_id)
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
                    rule_id=f"PYLINT_{msg_id}",
                )
            )

        return findings

    @staticmethod
    def _map_severity(msg_id: str) -> Severity:
        """
        Mapea el prefijo de mensaje pylint a severidad.

        Pylint usa prefijos:
        - C = convention, R = refactor -> LOW
        - W = warning -> MEDIUM
        - E = error, F = fatal -> HIGH

        Args:
            msg_id: ID del mensaje de pylint (ej: C0114, E0001).

        Returns:
            Nivel de severidad correspondiente.
        """
        if not msg_id:
            return Severity.LOW

        prefix = msg_id[0].upper()
        if prefix in ("E", "F"):
            return Severity.HIGH
        if prefix == "W":
            return Severity.MEDIUM
        return Severity.LOW
