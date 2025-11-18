"""
Clase base abstracta para todos los agentes de análisis
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding

if TYPE_CHECKING:
    from src.core.events.event_bus import EventBus


class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes de análisis.

    Todos los agentes especializados deben heredar de esta clase
    e implementar el método analyze().

    Attributes:
        name: Nombre identificador del agente
        version: Versión del agente
        category: Categoría (security, quality, performance, style)
        enabled: Estado de habilitación del agente
        event_bus: Sistema de eventos para comunicación (opcional)

    Example:
        class SecurityAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    name="SecurityAgent",
                    version="1.0.0",
                    category="security"
                )

            def analyze(self, context: AnalysisContext) -> List[Finding]:
                # Implementación específica
                pass
    """

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        category: str = "general",
        enabled: bool = True,
        event_bus: Optional["EventBus"] = None,
    ) -> None:
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Inicializa el agente base.

        Args:
            name: Identificador único del agente
            version: Versión del agente (semver)
            category: Categoría de análisis
            enabled: Si el agente está activo
            event_bus: EventBus para emitir eventos (opcional)

        Raises:
            ValueError: Si name está vacío
        """
        if not name or not name.strip():
            raise ValueError("Agent name cannot be empty")

        self.name = name
        self.version = version
        self.category = category
        self.enabled = enabled
        self.event_bus = event_bus
        self.logger = logging.getLogger(f"agents.{name}")

        self.logger.info("[%s] Agent initialized - version %s", self.name, self.version)

    @abstractmethod
    def analyze(self, context: AnalysisContext) -> List[Finding]:
        """
        Método abstracto que debe ser implementado por todas las clases hijas.

        Analiza el código en el contexto y retorna una lista de hallazgos.

        Args:
            context: Contexto de análisis con código y metadata

        Returns:
            Lista de Finding encontrados durante el análisis

        Raises:
            NotImplementedError: Si no es implementado por la clase hija
        """

    def _emit_agent_started(self, context: AnalysisContext) -> None:
        """Emite evento AGENT_STARTED."""
        if self.event_bus:
            self.event_bus.publish(
                {
                    "type": "AGENT_STARTED",
                    "agent_name": self.name,
                    "analysis_id": str(context.analysis_id),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        self.log_info("Analysis started")

    def _emit_agent_completed(self, context: AnalysisContext, findings: List[Finding]) -> None:
        """Emite evento AGENT_COMPLETED."""
        if self.event_bus:
            self.event_bus.publish(
                {
                    "type": "AGENT_COMPLETED",
                    "agent_name": self.name,
                    "analysis_id": str(context.analysis_id),
                    "findings_count": len(findings),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        self.log_info(f"Analysis completed - {len(findings)} findings")

    def _emit_agent_failed(self, context: AnalysisContext, error: Exception) -> None:
        """Emite evento AGENT_FAILED."""
        if self.event_bus:
            self.event_bus.publish(
                {
                    "type": "AGENT_FAILED",
                    "agent_name": self.name,
                    "analysis_id": str(context.analysis_id),
                    "error": str(error),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        self.log_error(f"Analysis failed: {error}")

    def is_enabled(self) -> bool:
        """
        Verifica si el agente está habilitado.

        Returns:
            True si el agente está habilitado, False en caso contrario
        """
        return self.enabled

    def enable(self) -> None:
        """Habilita el agente."""
        self.enabled = True
        self.logger.info("[%s] Agent enabled", self.name)

    def disable(self) -> None:
        """Deshabilita el agente."""
        self.enabled = False
        self.logger.warning("[%s] Agent disabled", self.name)

    def get_info(self) -> dict:
        """
        Retorna información metadata del agente.

        Returns:
            Diccionario con información del agente
        """
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "enabled": self.enabled,
        }

    def log_info(self, message: str) -> None:
        """Log a message at INFO level."""
        self.logger.info("[%s] %s", self.name, message)

    def log_warning(self, message: str) -> None:
        """Log a nivel WARNING."""
        self.logger.warning("[%s] %s", self.name, message)

    def log_error(self, message: str) -> None:
        """Log a nivel ERROR."""
        self.logger.error("[%s] %s", self.name, message)

    def log_debug(self, message: str) -> None:
        """Log a nivel DEBUG."""
        self.logger.debug("[%s] %s", self.name, message)

    def __repr__(self) -> str:
        """Representación string del agente."""
        return (
            f"<{self.__class__.__name__}("
            f"name={self.name}, "
            f"version={self.version}, "
            f"category={self.category}, "
            f"enabled={self.enabled})>"
        )

    def __str__(self) -> str:
        """String amigable del agente."""
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name} v{self.version} ({self.category}) - {status}"
