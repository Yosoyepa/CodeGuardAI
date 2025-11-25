"""
Event Bus para comunicación desacoplada entre componentes.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from src.core.events.observers import EventObserver

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Tipos de eventos estándar del sistema."""

    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"


class EventBus:
    """
    Bus de eventos centralizado para desacoplar componentes.

    Permite que el AnalysisService notifique progreso sin conocer
    detalles de WebSockets o persistencia.
    """

    _instance: Optional["EventBus"] = None
    _observers: List[EventObserver] = []

    def __new__(cls) -> "EventBus":
        """Implementación del patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._observers = []
        return cls._instance

    def subscribe(self, observer: EventObserver) -> None:
        """
        Registra un observer para recibir eventos.

        Args:
            observer: Observer que implementa EventObserver.
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: EventObserver) -> None:
        """
        Elimina un observer del bus.

        Args:
            observer: Observer a eliminar.
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publica un evento a todos los observers suscritos.

        Args:
            event_type: Tipo de evento (str o EventType).
            data: Datos del evento.
        """
        # Convertir Enum a string si es necesario
        if isinstance(event_type, Enum):
            event_type = event_type.value

        for observer in self._observers:
            try:
                observer.on_event(event_type, data)
            except Exception as e:
                # Log error pero no interrumpir otros observers
                logger.error(f"Error in observer {observer}: {e}")

    def clear(self) -> None:
        """Elimina todos los observers."""
        self._observers.clear()
