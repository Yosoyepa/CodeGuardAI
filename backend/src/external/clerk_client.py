"""
Cliente externo para validación de tokens JWT de Clerk.

Soporta dos tipos de tokens:
1. Session Tokens (RS256 con JWKS) - Tokens estándar de Clerk
2. Custom JWT Templates (HS256 con secret key) - Para integraciones de terceros

El cliente detecta automáticamente el algoritmo del token y usa la
validación correspondiente.
"""

from typing import Any, Dict, Optional

import httpx
from jose import ExpiredSignatureError, JWTError, jwk, jwt

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

    Detecta automáticamente el tipo de token:
    - RS256: Session tokens estándar (valida con JWKS)
    - HS256: Custom JWT templates (valida con secret key)

    Referencias:
    - Session Tokens: https://clerk.com/docs/guides/sessions/session-tokens
    - JWT Templates: https://clerk.com/docs/guides/sessions/jwt-templates
    """

    # Cache de JWKS para evitar requests en cada validación
    _jwks_cache: Optional[Dict[str, Any]] = None

    def __init__(self):
        """
        Inicializa el cliente con la configuración de Clerk.

        Requiere al menos uno de:
        - CLERK_JWKS_URL: Para validar session tokens (RS256)
        - CLERK_JWT_SIGNING_KEY: Para validar custom JWT templates (HS256)
        """
        self._jwks_url = settings.CLERK_JWKS_URL
        # Para HS256, priorizar JWT_SIGNING_KEY sobre SECRET_KEY
        self._signing_key = settings.CLERK_JWT_SIGNING_KEY or settings.CLERK_SECRET_KEY

        if not self._jwks_url and not self._signing_key:
            raise ValueError(
                "Se requiere CLERK_JWKS_URL o CLERK_JWT_SIGNING_KEY. "
                "Configura al menos una de estas variables de entorno."
            )

    def _get_token_algorithm(self, token: str) -> str:
        """
        Extrae el algoritmo del header del token.

        Args:
            token: Token JWT.

        Returns:
            Algoritmo (ej: "HS256", "RS256").

        Raises:
            ClerkTokenInvalidError: Si no se puede leer el header.
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg")

            if not alg:
                raise ClerkTokenInvalidError("Token no contiene algoritmo en el header")

            return alg

        except JWTError as e:
            raise ClerkTokenInvalidError(f"Error al leer header del token: {e}") from e

    def _fetch_jwks(self) -> Dict[str, Any]:
        """
        Obtiene las claves públicas del endpoint JWKS de Clerk.

        Returns:
            Dict con las claves JWKS en formato JWK.

        Raises:
            ClerkTokenInvalidError: Si no se puede obtener el JWKS.
        """
        if ClerkClient._jwks_cache is not None:
            return ClerkClient._jwks_cache

        if not self._jwks_url:
            raise ClerkTokenInvalidError(
                "CLERK_JWKS_URL no configurado. " "Requerido para validar tokens RS256."
            )

        try:
            response = httpx.get(self._jwks_url, timeout=10.0)
            response.raise_for_status()
            jwks_data = response.json()

            # Validar que tenga la estructura esperada
            if "keys" not in jwks_data or not isinstance(jwks_data["keys"], list):
                raise ClerkTokenInvalidError("Respuesta JWKS inválida: falta campo 'keys'")

            ClerkClient._jwks_cache = jwks_data
            return ClerkClient._jwks_cache

        except httpx.HTTPError as e:
            raise ClerkTokenInvalidError(f"Error al obtener JWKS de {self._jwks_url}: {e}") from e

    def _get_public_key(self, token: str):
        """
        Obtiene la clave pública RSA correcta para verificar el token RS256.

        Args:
            token: Token JWT para extraer el kid del header.

        Returns:
            Clave pública RSA construida desde JWKS.

        Raises:
            ClerkTokenInvalidError: Si no se encuentra la clave o el kid.
        """
        try:
            # Obtener kid del header del token (sin verificar aún)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise ClerkTokenInvalidError("Token RS256 no contiene 'kid' en el header")

            # Buscar la clave en JWKS
            jwks_data = self._fetch_jwks()

            for key_data in jwks_data.get("keys", []):
                if key_data.get("kid") == kid:
                    return jwk.construct(key_data)

            # Si no se encuentra, invalidar cache y reintentar una vez
            ClerkClient._jwks_cache = None
            jwks_data = self._fetch_jwks()

            for key_data in jwks_data.get("keys", []):
                if key_data.get("kid") == kid:
                    return jwk.construct(key_data)

            raise ClerkTokenInvalidError(f"No se encontró clave pública con kid '{kid}' en JWKS")

        except JWTError as e:
            raise ClerkTokenInvalidError(f"Error al extraer header del token: {e}") from e

    def _verify_rs256_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica un token RS256 (Session Token estándar de Clerk).

        Args:
            token: Token JWT con algoritmo RS256.

        Returns:
            Payload decodificado del token.

        Raises:
            ClerkTokenExpiredError: Si el token expiró.
            ClerkTokenInvalidError: Si el token es inválido.
        """
        public_key = self._get_public_key(token)

        return jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": False,  # Clerk no siempre usa aud
                "verify_iss": False,  # ISS varía según instancia
            },
        )

    def _verify_hs256_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica un token HS256 (Custom JWT Template de Clerk).

        Args:
            token: Token JWT con algoritmo HS256.

        Returns:
            Payload decodificado del token.

        Raises:
            ClerkTokenExpiredError: Si el token expiró.
            ClerkTokenInvalidError: Si el token es inválido.
        """
        if not self._signing_key:
            raise ClerkTokenInvalidError(
                "CLERK_JWT_SIGNING_KEY no configurado. "
                "Requerido para validar tokens HS256 (JWT Templates)."
            )

        return jwt.decode(
            token,
            self._signing_key,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": False,
                "verify_iss": False,
            },
        )

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Valida un token JWT de Clerk y retorna el payload completo.

        Detecta automáticamente el algoritmo del token:
        - RS256: Session token estándar (valida con JWKS)
        - HS256: Custom JWT template (valida con secret key)

        Args:
            token: Token JWT a validar.

        Returns:
            Dict con el payload completo del JWT, incluyendo:
            - sub: User ID (subject)
            - email: Email del usuario
            - name: Nombre del usuario
            - role: Rol del usuario (si está configurado)
            - exp, iat, nbf: Timestamps
            - iss, jti: Emisor e identificador
            - public_metadata, user_metadata, app_metadata: Metadatos

        Raises:
            ClerkTokenExpiredError: Si el token ha expirado (exp < now).
            ClerkTokenInvalidError: Si el token es inválido, malformado,
                                   o no se puede validar.
        """
        try:
            # Detectar algoritmo del token
            algorithm = self._get_token_algorithm(token)

            # Validar según el algoritmo
            if algorithm == "RS256":
                payload = self._verify_rs256_token(token)
            elif algorithm == "HS256":
                payload = self._verify_hs256_token(token)
            else:
                raise ClerkTokenInvalidError(
                    f"Algoritmo no soportado: {algorithm}. "
                    "Clerk usa RS256 (session tokens) o HS256 (JWT templates)."
                )

            return payload

        except ExpiredSignatureError as e:
            raise ClerkTokenExpiredError(
                "El token ha expirado. El usuario debe iniciar sesión nuevamente."
            ) from e

        except ClerkTokenExpiredError:
            # Re-raise para mantener el tipo de excepción
            raise

        except ClerkTokenInvalidError:
            # Re-raise para mantener el tipo de excepción
            raise

        except JWTError as e:
            raise ClerkTokenInvalidError(f"Token inválido o malformado: {e}") from e

    def get_user_id_from_token(self, token: str) -> str:
        """
        Extrae solo el user_id del token.

        Args:
            token: Token JWT.

        Returns:
            User ID (claim 'sub').

        Raises:
            ClerkTokenExpiredError: Si el token ha expirado.
            ClerkTokenInvalidError: Si el token es inválido o no tiene 'sub'.
        """
        payload = self.verify_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise ClerkTokenInvalidError("Token no contiene 'sub' claim. Token inválido de Clerk.")

        return user_id

    @classmethod
    def clear_jwks_cache(cls):
        """
        Limpia el cache de JWKS.

        Útil para:
        - Testing
        - Forzar recarga después de rotación de claves
        """
        cls._jwks_cache = None
