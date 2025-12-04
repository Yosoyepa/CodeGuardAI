"""
Dependencia de autenticación.

Valida tokens JWT de Clerk (RS256) y protege rutas.
Extrae información del usuario desde el payload completo del token.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.external.clerk_client import (
    ClerkClient,
    ClerkTokenExpiredError,
    ClerkTokenInvalidError,
)
from src.schemas.user import Role, User

# HTTPBearer para extraer token del header Authorization
http_bearer = HTTPBearer(auto_error=False)


def _map_role_from_payload(payload: dict) -> Role:
    """
    Mapea el rol del payload JWT al enum Role.

    Clerk permite definir roles en public_metadata o como claim directo.
    Orden de prioridad:
    1. public_metadata.role (recomendado)
    2. unsafe_metadata.role
    3. role claim directo
    4. Default: DEVELOPER
    """
    # Prioridad 1: public_metadata.role
    public_metadata = payload.get("public_metadata", {})
    if isinstance(public_metadata, dict):
        role = public_metadata.get("role", "").lower()
        if role == "admin":
            return Role.ADMIN
        if role == "developer":
            return Role.DEVELOPER

    # Prioridad 2: unsafe_metadata.role
    unsafe_metadata = payload.get("unsafe_metadata", {})
    if isinstance(unsafe_metadata, dict):
        role = unsafe_metadata.get("role", "").lower()
        if role == "admin":
            return Role.ADMIN
        if role == "developer":
            return Role.DEVELOPER

    # Prioridad 3: claim directo 'role'
    role_claim = payload.get("role", "").lower()
    if role_claim == "admin":
        return Role.ADMIN
    if role_claim == "developer":
        return Role.DEVELOPER

    return Role.DEVELOPER


def _extract_email_from_payload(payload: dict) -> str:
    """Extrae el email del payload de Clerk."""
    email = payload.get("email", "")
    if email:
        return email

    public_metadata = payload.get("public_metadata", {})
    if isinstance(public_metadata, dict):
        email = public_metadata.get("email", "")
        if email:
            return email

    email_addresses = payload.get("email_addresses", [])
    if isinstance(email_addresses, list) and len(email_addresses) > 0:
        first_email = email_addresses[0]
        if isinstance(first_email, dict):
            return first_email.get("email_address", "")

    return ""


def _extract_name_from_payload(payload: dict) -> str | None:
    """Extrae el nombre completo del usuario desde el payload."""
    name = payload.get("name")
    if name and isinstance(name, str):
        return name.strip() or None

    first_name = payload.get("first_name", "")
    last_name = payload.get("last_name", "")

    if first_name or last_name:
        full_name = f"{first_name} {last_name}".strip()
        return full_name or None

    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> User:
    """Obtiene el usuario actual validando el token JWT de Clerk (RS256)."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    clerk_client = ClerkClient()

    try:
        payload = clerk_client.verify_token(token)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: falta claim 'sub'",
                headers={"WWW-Authenticate": "Bearer"},
            )

        email = _extract_email_from_payload(payload)
        name = _extract_name_from_payload(payload)
        role = _map_role_from_payload(payload)

        return User(
            id=user_id,
            email=email,
            name=name,
            role=role,
        )

    except ClerkTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Por favor, inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except ClerkTokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> User | None:
    """Obtiene el usuario si hay token válido, None si no hay token."""
    if not credentials:
        return None
    return await get_current_user(credentials)


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Requiere que el usuario sea ADMIN."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para esta acción",
        )
    return current_user


async def require_developer(
    current_user: User = Depends(get_current_user),
) -> User:
    """Requiere que el usuario sea DEVELOPER o ADMIN."""
    if current_user.role not in [Role.DEVELOPER, Role.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de developer o superiores",
        )
    return current_user
