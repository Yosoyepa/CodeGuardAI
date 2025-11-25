"""
Dependencia de autenticación.

Provee OAuth2PasswordBearer para Swagger UI y autenticación opcional en desarrollo.
"""

import os

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from src.schemas.user import Role, User

# OAuth2 scheme para Swagger UI - muestra botón "Authorize"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Obtiene el usuario actual basado en el token.

    En desarrollo: retorna usuario mock.
    En producción: valida token JWT (a implementar en Sprint 2).

    Args:
        token: Token JWT del header Authorization.

    Returns:
        User: Usuario autenticado.

    Raises:
        HTTPException: 401 si el token es inválido en producción.
    """
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        # En producción, validar token real
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Token de autenticación requerido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # TODO: Implementar validación real con Clerk en Sprint 2
        raise HTTPException(
            status_code=401,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # En desarrollo, retornar usuario mock
    return User(
        id="user_123",
        email="dev@codeguard.ai",
        name="Developer User",
        role=Role.DEVELOPER,
    )
