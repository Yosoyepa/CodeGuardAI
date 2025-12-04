"""
Orquestador de agentes de analisis.

Coordina la ejecucion paralela de los agentes registrados
y agrega sus hallazgos en una lista unica.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.agents.agent_factory import AgentFactory
from src.agents.base_agent import BaseAgent
from src.core.events.event_bus import EventBus
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Finding, Severity

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Orquesta la ejecucion de multiples agentes de analisis en paralelo.

    Responsabilidades:
    - Obtener los agentes registrados y habilitados desde AgentFactory.
    - Ejecutar cada agente en paralelo usando ThreadPoolExecutor.
    - Manejar fallos individuales de agentes sin detener todo el proceso.
    - Agregar y normalizar los hallazgos en una lista unica.
    - Calcular una puntuacion de calidad basada en los hallazgos.
    """

    def __init__(
        self,
        agent_factory: Optional[AgentFactory] = None,
        event_bus: Optional[EventBus] = None,
        ai_explainer: Optional[Any] = None,
        max_workers: int = 4,
        timeout_seconds: int = 30,
    ) -> None:
        """
        Inicializa el orquestador.

        Args:
            agent_factory: Fabrica de agentes a utilizar. Si es None,
                se usa la instancia Singleton de AgentFactory.
            event_bus: EventBus compartido para agentes y orquestador.
            ai_explainer: Servicio opcional para generar explicaciones de IA.
            max_workers: Numero maximo de hilos para la ejecucion paralela.
            timeout_seconds: Tiempo maximo de espera por cada agente.
        """
        self.agent_factory: AgentFactory = agent_factory or AgentFactory.get_instance()
        self.event_bus: EventBus = event_bus or EventBus()
        self.ai_explainer: Optional[Any] = ai_explainer

        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=max_workers)
        self.registered_agents: List[str] = self.agent_factory.get_registered_agents()
        self.timeout_seconds: int = timeout_seconds

    # ------------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------------
    def orchestrate_analysis(self, context: AnalysisContext) -> List[Finding]:
        """
        Orquesta el analisis completo y devuelve la lista de hallazgos.

        Flujo:
        1. Ejecutar agentes en paralelo y recolectar hallazgos por agente.
        2. Agregar todos los hallazgos en una sola lista.
        3. Calcular la puntuacion de calidad (solo para log).

        Returns:
            Lista de hallazgos agregados y ordenados.
        """
        logger.info(
            "Iniciando orquestacion de analisis %s para archivo %s",
            context.analysis_id,
            context.filename,
        )

        # Paso 1: ejecucion paralela de los agentes
        results_by_agent = self.execute_agents_parallel(context)

        # Paso 2: agregacion de hallazgos
        findings = self._aggregate_findings(results_by_agent)

        # Paso 3: calculo de puntuacion de calidad (solo log)
        quality_score = self.calculate_quality_score(findings)

        logger.info(
            "Orquestacion completada para analisis %s. Hallazgos: %d, score: %d",
            context.analysis_id,
            len(findings),
            quality_score,
        )

        return findings

    def execute_agents_parallel(
        self,
        context: AnalysisContext,
    ) -> Dict[str, List[Finding]]:
        """
        Ejecuta todos los agentes registrados y habilitados en paralelo.

        Args:
            context: Contexto de analisis que se pasa a cada agente.

        Returns:
            Diccionario con la forma:
                nombre_agente -> lista de Finding
        """
        # Obtener agentes habilitados e inyectar event_bus
        agents: List[BaseAgent] = self.agent_factory.get_all_agents(
            event_bus=self.event_bus,
            only_enabled=True,
        )

        results: Dict[str, List[Finding]] = {}

        if not agents:
            logger.warning("No hay agentes habilitados para ejecutar.")
            return results

        logger.debug(
            "Ejecutando agentes en paralelo: %s",
            ", ".join(a.name for a in agents),
        )

        future_to_agent = {
            self.executor.submit(self._run_single_agent, agent, context): agent for agent in agents
        }

        for future in as_completed(future_to_agent):
            agent = future_to_agent[future]
            agent_name = agent.name

            try:
                findings = future.result(timeout=self.timeout_seconds)
                results[agent_name] = findings
                logger.info(
                    "Agente %s finalizo con %d hallazgos",
                    agent_name,
                    len(findings),
                )
            except TimeoutError as exc:
                self.handle_agent_failure(agent_name, exc, context)
            except Exception as exc:  # pylint: disable=broad-except
                self.handle_agent_failure(agent_name, exc, context)

        return results

    def calculate_quality_score(self, findings: List[Finding]) -> int:
        """
        Calcula una puntuacion de calidad global (0-100) a partir de los hallazgos.

        Estrategia:
        - Partir de 100 puntos.
        - Restar un castigo por cada hallazgo segun su severidad.
        - Hacer clamp del resultado al rango [0, 100].
        """
        if not findings:
            return 100

        score = 100

        for finding in findings:
            # Si Finding implementa get_severity_penalty() se prioriza ese metodo
            try:
                penalty = finding.get_severity_penalty()
            except AttributeError:
                # Fallback: usar un mapa simple basado en Severity
                if finding.severity == Severity.CRITICAL:
                    penalty = 10
                elif finding.severity == Severity.HIGH:
                    penalty = 5
                elif finding.severity == Severity.MEDIUM:
                    penalty = 2
                elif finding.severity == Severity.LOW:
                    penalty = 1
                else:
                    penalty = 0
            score -= penalty

        # Asegurar que este en el rango 0-100
        return max(0, min(100, score))

    def handle_agent_failure(
        self,
        agent_name: str,
        error: Exception,
        context: Optional[AnalysisContext] = None,
    ) -> None:
        """
        Maneja el fallo de un agente individual.

        No detiene el analisis completo, solo registra el error
        y publica un evento para que los observadores puedan reaccionar.
        """
        logger.error("El agente %s fallo: %s", agent_name, error)

        # Publicar evento de fallo si el EventBus soporta esta interfaz
        try:
            self.event_bus.publish(
                "AGENT_FAILED",
                {
                    "agent_name": agent_name,
                    "analysis_id": str(context.analysis_id) if context else None,
                    "error": str(error),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception:  # pylint: disable=broad-except
            # No queremos que un fallo en el EventBus rompa el orquestador
            logger.exception("Error publicando evento AGENT_FAILED para %s", agent_name)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _run_single_agent(
        self,
        agent: BaseAgent,
        context: AnalysisContext,
    ) -> List[Finding]:
        """
        Ejecuta un agente individual contra el contexto dado.

        Se asume que el propio agente se encarga de emitir sus eventos
        de inicio, exito o fallo usando el event_bus que se le inyecto.
        """
        logger.debug(
            "Ejecutando agente %s sobre analisis %s",
            agent.name,
            context.analysis_id,
        )
        findings = agent.analyze(context)
        return findings

    def _aggregate_findings(
        self,
        results: Dict[str, List[Finding]],
    ) -> List[Finding]:
        """
        Convierte el dict {agente -> hallazgos} en una lista plana.

        Ademas, puede completar metadata del hallazgo con el tipo
        de agente si el modelo Finding lo permite.
        """
        aggregated: List[Finding] = []

        for agent_name, findings in results.items():
            for f in findings:
                # Si Finding tiene un campo agent_type intentar rellenarlo
                if hasattr(f, "agent_type") and not getattr(f, "agent_type", None):
                    setattr(f, "agent_type", agent_name)
                aggregated.append(f)

        return aggregated
