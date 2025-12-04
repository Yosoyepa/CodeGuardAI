"""
Cliente MCP (Model Context Protocol) para enriquecer prompts con contexto de seguridad.

Proporciona acceso a la base de conocimiento OWASP Top 10 y mapeos CWE
para enriquecer las explicaciones generadas por IA.

Principios de diseño:
- SRP: Solo busca y formatea contexto de seguridad
- Acoplamiento débil: Interfaz abstracta permite múltiples implementaciones
- Async: Todas las operaciones son asíncronas para consistencia
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.config.mcp_config import (
    OWASP_TOP_10,
    SecurityContext,
    format_security_context,
    get_security_context,
)
from src.schemas.finding import Finding

logger = logging.getLogger("agents.MCP")


class MCPClient(ABC):
    """
    Interfaz abstracta para clientes MCP (Model Context Protocol).

    Define el contrato para obtener contexto de seguridad que será
    usado para enriquecer prompts de IA generativa.
    """

    @abstractmethod
    async def get_context(self, finding: Finding) -> Optional[str]:
        """
        Obtiene contexto de seguridad formateado para un hallazgo.

        Args:
            finding: Hallazgo de seguridad a enriquecer

        Returns:
            Contexto formateado como texto o None si no se encuentra
        """
        pass

    @abstractmethod
    async def get_security_context(self, finding: Finding) -> Optional[SecurityContext]:
        """
        Obtiene el objeto SecurityContext para un hallazgo.

        Args:
            finding: Hallazgo de seguridad

        Returns:
            SecurityContext o None si no se encuentra
        """
        pass

    @abstractmethod
    def get_available_categories(self) -> List[str]:
        """
        Lista las categorías OWASP disponibles.

        Returns:
            Lista de nombres de categorías
        """
        pass


class LocalMCPClient(MCPClient):
    """
    Cliente MCP local usando el diccionario OWASP Top 10 embebido.

    Busca contexto de seguridad relevante basado en rule_id o issue_type
    del hallazgo y lo formatea para enriquecer prompts de IA.

    Esta implementación usa datos locales. Puede ser extendida o reemplazada
    por una que consulte servidores MCP externos.

    Example:
        client = LocalMCPClient()
        context = await client.get_context(finding)
        if context:
            prompt = f"Contexto OWASP:\\n{context}"
    """

    async def get_context(self, finding: Finding) -> Optional[str]:
        """
        Obtiene contexto de seguridad OWASP formateado para un hallazgo.

        Busca primero por rule_id (más específico) y luego por issue_type.

        Args:
            finding: Hallazgo de seguridad

        Returns:
            Contexto formateado o None si no se encuentra
        """
        context = await self.get_security_context(finding)

        if context:
            formatted = format_security_context(context)
            logger.debug(
                f"[MCP] Contexto encontrado para {finding.rule_id or finding.issue_type}: "
                f"{context.category}"
            )
            return formatted

        logger.debug(f"[MCP] Sin contexto OWASP para {finding.rule_id or finding.issue_type}")
        return None

    async def get_security_context(self, finding: Finding) -> Optional[SecurityContext]:
        """
        Obtiene el objeto SecurityContext para un hallazgo.

        Prioriza rule_id sobre issue_type para mayor precisión.

        Args:
            finding: Hallazgo de seguridad

        Returns:
            SecurityContext o None si no se encuentra
        """
        # Buscar por rule_id primero (más específico)
        if finding.rule_id:
            context = get_security_context(rule_id=finding.rule_id)
            if context:
                return context

        # Fallback a issue_type
        if finding.issue_type:
            context = get_security_context(issue_type=finding.issue_type)
            if context:
                return context

        return None

    def get_available_categories(self) -> List[str]:
        """
        Lista todas las categorías OWASP disponibles.

        Returns:
            Lista de claves del diccionario OWASP_TOP_10
        """
        return list(OWASP_TOP_10.keys())

    async def get_context_by_category(self, category_key: str) -> Optional[str]:
        """
        Obtiene contexto por clave de categoría directamente.

        Args:
            category_key: Clave del diccionario OWASP (ej: "injection", "broken_access_control")

        Returns:
            Contexto formateado o None
        """
        context = OWASP_TOP_10.get(category_key)
        if context:
            return format_security_context(context)
        return None


# Singleton del cliente MCP
_mcp_client_instance: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """
    Factory function para obtener el cliente MCP.

    Usa patrón singleton para reutilizar la misma instancia.

    Returns:
        Instancia de MCPClient (LocalMCPClient por defecto)
    """
    global _mcp_client_instance
    if _mcp_client_instance is None:
        _mcp_client_instance = LocalMCPClient()
    return _mcp_client_instance


def reset_mcp_client() -> None:
    """
    Resetea el singleton del cliente MCP (útil para testing).
    """
    global _mcp_client_instance
    _mcp_client_instance = None
