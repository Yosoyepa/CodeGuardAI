"""
Fabrica de agentes de analisis.

Implementa un patron Singleton que mantiene un registro
de los tipos de agentes disponibles y crea instancias
segun se necesiten.
"""

import logging
import threading
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

from src.agents.base_agent import BaseAgent

if TYPE_CHECKING:
    from src.core.events.event_bus import EventBus
    from src.schemas.agent_config import AgentConfig

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Fabrica Singleton para agentes de analisis.

    Responsabilidades:
    - Mantener un registro de nombre de agente -> clase de agente.
    - Crear instancias de agentes bajo demanda.
    - Reutilizar instancias para cada nombre logico de agente.
    """

    _instance: Optional["AgentFactory"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """
        Constructor privado segun el patron Singleton.

        No debe llamarse directamente; usar get_instance().
        """
        # Estas propiedades se inicializan solo una vez por instancia
        self._registry: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}

        self._register_default_agents()

    # ------------------------------------------------------------------
    # Acceso al Singleton
    # ------------------------------------------------------------------
    @classmethod
    def get_instance(cls) -> "AgentFactory":
        """
        Devuelve la instancia unica de AgentFactory.

        Crea la instancia de forma segura en presencia de hilos.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def _reset_instance(cls) -> None:
        """
        Resetea la instancia unica.

        Metodo pensado para pruebas unitarias, para poder
        recrear el estado de la fabrica desde cero.
        """
        with cls._lock:
            cls._instance = None

    # ------------------------------------------------------------------
    # Registro de tipos de agentes
    # ------------------------------------------------------------------
    def _register_default_agents(self) -> None:
        """
        Registra los agentes base disponibles en el sistema.

        Se hace el import dentro del metodo para evitar
        importaciones circulares al cargar los modulos.
        """
        try:
            from src.agents.quality_agent import QualityAgent
            from src.agents.security_agent import SecurityAgent

            # from src.agents.performance_agent import PerformanceAgent
            from src.agents.style_agent import StyleAgent

            self.register_agent("security", SecurityAgent)
            self.register_agent("quality", QualityAgent)
            # self.register_agent("performance", PerformanceAgent)
            self.register_agent("style", StyleAgent)

            logger.info(
                "Agentes por defecto registrados: %s",
                ", ".join(self.get_registered_agents()),
            )
        except ImportError as exc:
            logger.warning("No fue posible registrar los agentes por defecto: %s", exc)

    def register_agent(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """
        Registra un nuevo tipo de agente en la fabrica.

        Args:
            name: Nombre logico del agente (por ejemplo, 'security').
            agent_class: Clase concreta que implementa BaseAgent.
        """
        self._registry[name] = agent_class
        logger.info("Agente registrado en factory: %s -> %s", name, agent_class.__name__)

    def unregister_agent(self, name: str) -> None:
        """
        Elimina un agente del registro y de las instancias cacheadas.

        Si el nombre no existe, no hace nada.
        """
        if name in self._registry:
            self._registry.pop(name, None)
            self._instances.pop(name, None)
            logger.info("Agente desregistrado de factory: %s", name)

    def get_registered_agents(self) -> List[str]:
        """
        Devuelve la lista de nombres de agentes registrados.
        """
        return list(self._registry.keys())

    # ------------------------------------------------------------------
    # Creacion y obtencion de instancias
    # ------------------------------------------------------------------
    def create_agent(
        self,
        name: str,
        config: Optional["AgentConfig"] = None,
        event_bus: Optional["EventBus"] = None,
    ) -> BaseAgent:
        """
        Crea una nueva instancia de agente para el nombre indicado.

        Intenta pasar config y event_bus al constructor del agente.
        Si la firma del constructor no los acepta, se hace un
        fallback para crear la instancia con los argumentos
        minimos posibles.

        Args:
            name: Nombre logico del agente registrado.
            config: Objeto de configuracion del agente (opcional).
            event_bus: EventBus compartido para que el agente emita eventos.

        Raises:
            ValueError: Si el agente no esta registrado.
        """
        if name not in self._registry:
            raise ValueError(f"El agente '{name}' no esta registrado en AgentFactory")

        agent_cls = self._registry[name]

        # Intentar distintas combinaciones segun el soporte de cada agente
        init_kwargs: Dict[str, Any] = {}
        if config is not None:
            init_kwargs["config"] = config
        if event_bus is not None:
            init_kwargs["event_bus"] = event_bus

        try:
            agent = agent_cls(**init_kwargs)
        except TypeError:
            # Si el agente no soporta alguno de los kwargs, intentar degradar
            try:
                # Intentar solo con event_bus
                if "event_bus" in init_kwargs:
                    agent = agent_cls(event_bus=init_kwargs["event_bus"])
                else:
                    raise TypeError()
            except TypeError:
                # Intentar sin argumentos
                agent = agent_cls()

        self._instances[name] = agent
        logger.debug("Instancia creada para agente '%s': %r", name, agent)
        return agent

    def get_agent(
        self,
        name: str,
        config: Optional["AgentConfig"] = None,
        event_bus: Optional["EventBus"] = None,
    ) -> BaseAgent:
        """
        Devuelve una instancia de agente.

        Si ya existe una instancia cacheada para ese nombre,
        se reutiliza. Si no existe, se crea una nueva.

        Nota: si ya hay una instancia cacheada se devuelve tal cual,
        por lo que config y event_bus solo se aplican en la primera
        creacion de la instancia.
        """
        if name in self._instances:
            return self._instances[name]
        return self.create_agent(name, config=config, event_bus=event_bus)

    def get_all_agents(
        self,
        config: Optional["AgentConfig"] = None,
        event_bus: Optional["EventBus"] = None,
        only_enabled: bool = True,
    ) -> List[BaseAgent]:
        """
        Devuelve las instancias de todos los agentes registrados.

        Por defecto solo devuelve los agentes que estan habilitados
        segun la propiedad enabled de BaseAgent.

        Args:
            config: Configuracion comun que se puede pasar a los agentes
                que se creen por primera vez (opcional).
            event_bus: EventBus a inyectar en los agentes que se creen
                por primera vez.
            only_enabled: Si es True, filtra solo agentes habilitados.

        Returns:
            Lista de instancias de agentes.
        """
        agents: List[BaseAgent] = [
            self.get_agent(name, config=config, event_bus=event_bus)
            for name in self._registry.keys()
        ]

        if not only_enabled:
            return agents

        enabled_agents = [a for a in agents if a.is_enabled()]
        return enabled_agents
