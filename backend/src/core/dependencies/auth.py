"""
Dependencia de autenticación.
"""

from fastapi import Header, HTTPException

from src.schemas.user import User


async def get_current_user(authorization: str = Header(None)) -> User:
    """
    Simula la validación de un token JWT (Clerk) y retorna el usuario.

    Nota: Para el Sprint 1, esto puede ser un stub que valida la presencia del header.
    En producción, esto decodifica el JWT real.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Simulación de usuario autenticado
    return User(id="user_123", email="dev@codeguard.ai", name="Developer", role="developer")
