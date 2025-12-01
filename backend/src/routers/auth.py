"""
Router de autenticación.

Expone endpoint POST /api/v1/auth/login para sincronizar
usuarios de Clerk con la base de datos (AC Escenario 1).
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.external.clerk_client import (
    ClerkClient,
    ClerkTokenExpiredError,
    ClerkTokenInvalidError,
)
from src.repositories.user_repo import UserRepository
from src.schemas.user import User
from src.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

http_bearer = HTTPBearer()


@router.post("/login", response_model=User)
async def login(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Sincroniza usuario de Clerk con la base de datos.

    Este endpoint cumple con AC Escenario 1 de JIRA:
    - Valida el token JWT de Clerk
    - Crea el usuario en la BD si no existe
    - Actualiza los datos del usuario si ya existe
    - Retorna el User schema con los datos sincronizados

    Args:
        credentials: Token JWT en header Authorization: Bearer <token>
        db: Sesión de base de datos.

    Returns:
        User: Usuario sincronizado.

    Raises:
        HTTPException 401: Si el token es inválido o expirado.
    """
    token = credentials.credentials

    # Inyectar dependencias
    clerk_client = ClerkClient()
    user_repository = UserRepository(db)
    auth_service = AuthService(clerk_client, user_repository)

    try:
        user = auth_service.login_user(token)
        return user

    except ClerkTokenExpiredError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ClerkTokenInvalidError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=User)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> User:
    """
    Obtiene información del usuario actual sin sincronizar con BD.

    Útil para verificar el estado de autenticación desde el frontend.

    Args:
        credentials: Token JWT en header Authorization: Bearer <token>

    Returns:
        User: Datos del usuario extraídos del token.

    Raises:
        HTTPException 401: Si el token es inválido o expirado.
    """
    token = credentials.credentials
    clerk_client = ClerkClient()

    try:
        payload = clerk_client.verify_token(token)

        return User(
            id=payload["user_id"],
            email=payload.get("email", ""),
            name=payload.get("name"),
        )

    except ClerkTokenExpiredError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ClerkTokenInvalidError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
