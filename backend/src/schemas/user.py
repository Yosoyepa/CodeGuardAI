"""
Esquemas de usuario para CodeGuard AI
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Role(str, Enum):
    """Roles de usuario."""

    DEVELOPER = "developer"
    ADMIN = "admin"


class User(BaseModel):
    """
    Modelo de usuario autenticado.

    Attributes:
        id: Clerk user ID
        email: Email del usuario
        name: Nombre completo
        role: Rol (developer o admin)
    """

    id: str = Field(..., description="Clerk user ID")
    email: EmailStr = Field(..., description="Email del usuario")
    name: Optional[str] = Field(default=None, description="Nombre completo")
    role: Role = Field(default=Role.DEVELOPER, description="Rol del usuario")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "user_123",
                "email": "dev@codeguard.ai",
                "name": "Developer",
                "role": "developer",
            }
        },
    )
