"""
Dependencia de autenticación.

Valida tokens JWT de Clerk y protege rutas.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.external.clerk_client import (
    ClerkClient,
    ClerkTokenExpiredError,
    ClerkTokenInvalidError,
)
from src.schemas.user import Role, User

# HTTPBearer para extraer token del header Authorization
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> User:
    """
    Obtiene el usuario actual validando el token JWT de Clerk.

    Flujo:
    1. Extrae token del header Authorization: Bearer <token>
    2. Valida el token con ClerkClient
    3. Retorna User schema con los datos del token

    Args:
        credentials: Credenciales HTTP Bearer.

    Returns:
        User: Usuario autenticado.

    Raises:
        HTTPException 401: Si el token falta, es inválido o expiró.
    """
    # AC Escenario 2: Verificar que el token esté presente
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    clerk_client = ClerkClient()

    try:
        # Validar token con Clerk
        payload = clerk_client.verify_token(token)

        return User(
            id=payload["user_id"],
            email=payload.get("email", ""),
            name=payload.get("name"),
            role=Role.DEVELOPER,
        )

    except ClerkTokenExpiredError:
        # AC Escenario 6: Token expirado
        raise HTTPException(
            status_code=401,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ClerkTokenInvalidError:
        # AC Escenario 5: Token inválido
        raise HTTPException(
            status_code=401,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> User | None:
    """
    Obtiene el usuario actual si hay token, None si no.

    Útil para endpoints que funcionan con o sin autenticación.

    Args:
        credentials: Credenciales HTTP Bearer (opcional).

    Returns:
        User si hay token válido, None si no hay token.

    Raises:
        HTTPException 401: Si hay token pero es inválido o expiró.
    """
    if not credentials:
        return None

    return await get_current_user(credentials)
