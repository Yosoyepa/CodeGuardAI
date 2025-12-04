"""
Orquestador de agentes de análisis.
Coordina la ejecución paralela y la agregación de resultados.
"""

import concurrent.futures
import logging
from typing import Any, Dict, List

from src.agents.agent_factory import AgentFactory
from src.agents.base_agent import BaseAgent
from src.core.events.analysis_events import AnalysisEventType
from src.core.events.event_bus import EventBus
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Coordina la ejecución de múltiples agentes de análisis en paralelo.
    """

    def __init__(self):
        self.agent_factory = AgentFactory()
        self.event_bus = EventBus()
        # Configuración de concurrencia (ajustable según CPU)
        self.max_workers = 4

    def run_analysis(self, context: AnalysisContext) -> List[Finding]:
        """
        Ejecuta todos los agentes registrados contra el contexto proporcionado.

        Flujo:
        1. Obtener agentes habilitados.
        2. Ejecutar en paralelo (ThreadPool).
        3. Recolectar hallazgos.
        4. Manejar errores individuales sin detener el proceso global.

        Args:
            context: Contexto del análisis (código, metadatos).

        Returns:
            Lista consolidada de todos los hallazgos encontrados.
        """
        agents = self.agent_factory.get_all_agents()
        all_findings: List[Finding] = []

        if not agents:
            logger.warning("No hay agentes registrados para ejecutar.")
            return []

        # Ejecución Paralela
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Mapeamos: futuro -> instancia del agente (para saber cuál falló)
            future_to_agent = {
                executor.submit(self._safe_analyze, agent, context): agent for agent in agents
            }

            for future in concurrent.futures.as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    findings = future.result()
                    all_findings.extend(findings)

                    # Notificar éxito del agente
                    self.event_bus.publish(
                        AnalysisEventType.AGENT_COMPLETED,
                        {
                            "analysis_id": str(context.analysis_id),
                            "agent": agent.name,
                            "findings_count": len(findings),
                        },
                    )
                except Exception as e:
                    logger.error(f"El agente {agent.name} falló: {e}")
                    self.event_bus.publish(
                        AnalysisEventType.AGENT_FAILED,
                        {
                            "analysis_id": str(context.analysis_id),
                            "agent": agent.name,
                            "error": str(e),
                        },
                    )

        return all_findings

    def _safe_analyze(self, agent: BaseAgent, context: AnalysisContext) -> List[Finding]:
        """
        Wrapper para ejecutar el análisis de un agente y notificar su inicio.
        """
        self.event_bus.publish(
            AnalysisEventType.AGENT_STARTED,
            {"analysis_id": str(context.analysis_id), "agent": agent.name},
        )
        return agent.analyze(context)
