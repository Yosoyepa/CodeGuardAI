"""
Definición de eventos del dominio de análisis.
Ubicación: Core/Events (Shared Kernel).
"""

from enum import Enum


class AnalysisEventType(str, Enum):
    """
    Enumeración de tipos de eventos para el ciclo de vida del análisis.
    """

    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"

    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_TIMEOUT = "agent_timeout"
