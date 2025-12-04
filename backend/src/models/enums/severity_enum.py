"""
Enum para niveles de severidad de hallazgos.
Alineado con PostgreSQL ENUM 'finding_severity'.
"""

from enum import Enum


class SeverityEnum(str, Enum):
    """
    Niveles de severidad de un hallazgo en la base de datos.

    CRITICAL: OWASP Top 10, explotable inmediatamente
    HIGH: Vulnerabilidades comunes que requieren condiciones específicas
    MEDIUM: Code smells de seguridad/rendimiento
    LOW: Violaciones de estilo menores
    """

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
