"""
Definición de interfaces para el patrón Observer.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class EventObserver(ABC):
    """
    Interfaz base para cualquier observador que desee suscribirse al EventBus.
    """

    @abstractmethod
    async def on_event(self, event: Dict[str, Any]) -> None:
        """
        Método invocado cuando ocurre un evento.

        Args:
            event: Diccionario con los datos del evento (tipo, timestamp, payload).
        """
        pass
