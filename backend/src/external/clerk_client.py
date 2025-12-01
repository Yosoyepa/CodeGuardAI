"""
Cliente externo para validación de tokens JWT de Clerk.

Abstrae la lógica de validación usando python-jose con algoritmo HS256.
"""

from typing import Any, Dict

from jose import ExpiredSignatureError, JWTError, jwt

from src.core.config.settings import settings


class ClerkTokenError(Exception):
    """Error base para problemas con tokens de Clerk."""

    pass


class ClerkTokenExpiredError(ClerkTokenError):
    """Token JWT expirado."""

    pass


class ClerkTokenInvalidError(ClerkTokenError):
    """Token JWT inválido o malformado."""

    pass


class ClerkClient:
    """
    Cliente para validar tokens JWT emitidos por Clerk.

    Utiliza el algoritmo HS256 con la CLERK_SECRET_KEY para
    decodificar y validar tokens.
    """

    def __init__(self):
        """Inicializa el cliente con la configuración de Clerk."""
        self._secret_key = settings.CLERK_SECRET_KEY
        self._algorithms = ["HS256"]

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Valida un token JWT y retorna el payload decodificado.

        Args:
            token: Token JWT a validar.

        Returns:
            Dict con user_id, email, name extraídos del payload.

        Raises:
            ClerkTokenExpiredError: Si el token ha expirado.
            ClerkTokenInvalidError: Si el token es inválido o malformado.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=self._algorithms,
            )

            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
            }

        except ExpiredSignatureError as e:
            raise ClerkTokenExpiredError("El token ha expirado") from e
        except JWTError as e:
            raise ClerkTokenInvalidError("Token inválido o malformado") from e

    def get_user_id_from_token(self, token: str) -> str:
        """
        Extrae solo el user_id del token.

        Args:
            token: Token JWT.

        Returns:
            User ID (sub claim).

        Raises:
            ClerkTokenExpiredError: Si el token ha expirado.
            ClerkTokenInvalidError: Si el token es inválido.
        """
        payload = self.verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise ClerkTokenInvalidError("Token no contiene user_id (sub)")

        return user_id
