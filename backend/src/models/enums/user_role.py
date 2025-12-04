"""
Enum para roles de usuario.
Alineado con PostgreSQL ENUM 'user_role'.
"""

from enum import Enum


class UserRole(str, Enum):
    """
    Roles de usuario en el sistema.

    DEVELOPER: Acceso básico, límite de 10 análisis/día
    ADMIN: Acceso completo, sin límites, puede configurar agentes
    """

    DEVELOPER = "DEVELOPER"
    ADMIN = "ADMIN"
