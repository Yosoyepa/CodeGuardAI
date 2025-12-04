"""
MCP Context Enricher Service

Enriquece los hallazgos de seguridad con contexto OWASP Top 10 y CWE
para mejorar las explicaciones generadas por IA.

Este servicio actúa como un "Model Context Protocol" local que proporciona
contexto relevante de seguridad para cada hallazgo antes de enviarlo
al modelo de IA generativa.

Principios de diseño:
- SRP: Solo enriquece contexto, no genera explicaciones
- Acoplamiento débil: Usa MCPClient interface, no implementaciones directas
- Async: Todas las operaciones son asíncronas para consistencia
"""

from dataclasses import dataclass
from typing import Optional

from src.core.config.mcp_config import SecurityContext, format_security_context
from src.external.mcp_client import MCPClient, get_mcp_client
from src.schemas.finding import Finding


@dataclass
class EnrichedContext:
    """
    Contexto enriquecido para un hallazgo.

    Attributes:
        finding: El hallazgo original
        security_context: Contexto de seguridad OWASP (si aplica)
        formatted_prompt_context: Texto formateado para incluir en el prompt
        has_security_context: Indica si se encontró contexto OWASP
    """

    finding: Finding
    security_context: Optional[SecurityContext]
    formatted_prompt_context: str
    has_security_context: bool

    @property
    def is_security_finding(self) -> bool:
        """Indica si es un hallazgo de seguridad con contexto OWASP."""
        return self.has_security_context


class MCPContextEnricher:
    """
    Servicio para enriquecer hallazgos con contexto de seguridad.

    Este servicio usa MCPClient para buscar información relevante en la
    base de conocimiento OWASP Top 10 y la formatea para prompts de IA.

    Example:
        enricher = MCPContextEnricher()
        context = await enricher.enrich(finding)
        prompt = f"Analiza este hallazgo:\\n{context.formatted_prompt_context}"

    Principios:
        - SRP: Solo enriquece, no genera explicaciones
        - Acoplamiento débil: Depende de MCPClient interface
        - Testeabilidad: MCP client inyectable facilita testing
    """

    def __init__(self, mcp_client: Optional[MCPClient] = None):
        """
        Inicializa el enricher con un cliente MCP.

        Args:
            mcp_client: Cliente MCP a usar (default: LocalMCPClient)
        """
        self._mcp_client = mcp_client or get_mcp_client()

    async def enrich(self, finding: Finding) -> EnrichedContext:
        """
        Enriquece un hallazgo con contexto de seguridad OWASP.

        Args:
            finding: Hallazgo a enriquecer

        Returns:
            EnrichedContext con información de seguridad relevante
        """
        # Buscar contexto de seguridad usando MCP client
        security_context = await self._mcp_client.get_security_context(finding)

        # Formatear el contexto del hallazgo
        formatted_context = self._format_finding_context(finding, security_context)

        return EnrichedContext(
            finding=finding,
            security_context=security_context,
            formatted_prompt_context=formatted_context,
            has_security_context=security_context is not None,
        )

    async def enrich_batch(self, findings: list[Finding]) -> list[EnrichedContext]:
        """
        Enriquece múltiples hallazgos de forma eficiente.

        Args:
            findings: Lista de hallazgos a enriquecer

        Returns:
            Lista de EnrichedContext
        """
        return [await self.enrich(finding) for finding in findings]

    def _format_finding_context(
        self, finding: Finding, security_context: Optional[SecurityContext]
    ) -> str:
        """
        Formatea el contexto completo del hallazgo para el prompt de IA.

        Incluye información del hallazgo original más contexto OWASP si existe.

        Args:
            finding: Hallazgo original
            security_context: Contexto de seguridad (opcional)

        Returns:
            Texto formateado para incluir en el prompt
        """
        sections = []

        # Sección: Información del hallazgo
        sections.append(self._format_finding_info(finding))

        # Sección: Contexto de seguridad OWASP (si existe)
        if security_context:
            owasp_context = format_security_context(security_context)
            sections.append(owasp_context)

        # Sección: Código problemático (si existe)
        if finding.code_snippet:
            sections.append(self._format_code_section(finding))

        return "\n\n".join(sections)

    def _format_finding_info(self, finding: Finding) -> str:
        """
        Formatea la información básica del hallazgo.

        Args:
            finding: Hallazgo a formatear

        Returns:
            Texto formateado con información del hallazgo
        """
        lines = [
            "## Hallazgo Detectado",
            f"- **Tipo**: {finding.issue_type}",
            f"- **Severidad**: {finding.severity.value.upper()}",
            f"- **Mensaje**: {finding.message}",
            f"- **Línea**: {finding.line_number}",
            f"- **Agente**: {finding.agent_name}",
        ]

        if finding.rule_id:
            lines.append(f"- **Regla**: {finding.rule_id}")

        if finding.suggestion:
            lines.append(f"- **Sugerencia inicial**: {finding.suggestion}")

        return "\n".join(lines)

    def _format_code_section(self, finding: Finding) -> str:
        """
        Formatea la sección de código problemático.

        Args:
            finding: Hallazgo con código

        Returns:
            Texto formateado con el código
        """
        return (
            "## Código Problemático\n"
            "```python\n"
            f"# Línea {finding.line_number}\n"
            f"{finding.code_snippet}\n"
            "```"
        )


# Factory function para facilitar inyección de dependencias
def get_mcp_context_enricher(mcp_client: Optional[MCPClient] = None) -> MCPContextEnricher:
    """
    Factory function para crear instancias del enricher.

    Args:
        mcp_client: Cliente MCP opcional para inyección

    Returns:
        Nueva instancia de MCPContextEnricher
    """
    return MCPContextEnricher(mcp_client=mcp_client)
