"""
Servicio de autenticación.

Orquesta la validación de tokens JWT de Clerk y la sincronización
de usuarios en la base de datos.
"""

from src.external.clerk_client import ClerkClient, ClerkTokenInvalidError
from src.models.user import UserEntity
from src.repositories.user_repo import UserRepository
from src.schemas.user import Role, User


class AuthService:
    """
    Servicio para gestionar la autenticación de usuarios.

    Responsabilidad: lógica de negocio para validación de tokens
    y sincronización de usuarios con Clerk.
    """

    def __init__(self, clerk_client: ClerkClient, user_repository: UserRepository):
        """
        Inicializa el servicio con sus dependencias.

        Args:
            clerk_client: Cliente para validar tokens de Clerk.
            user_repository: Repositorio para operaciones de usuarios.
        """
        self._clerk_client = clerk_client
        self._user_repository = user_repository

    def login_user(self, token: str) -> User:
        """
        Procesa el login de un usuario con token de Clerk.

        Flujo:
        1. Valida el token JWT con Clerk
        2. Busca el usuario en la BD
        3. Si no existe, lo crea; si existe, actualiza sus datos
        4. Retorna el User schema

        Args:
            token: Token JWT de Clerk.

        Returns:
            User schema con los datos del usuario.

        Raises:
            ClerkTokenError: Si el token es inválido o expirado.
        """
        # 1. Validar token con Clerk
        clerk_data = self._clerk_client.verify_token(token)

        # Clerk usa 'sub' para user_id en el payload JWT
        user_id = clerk_data.get("sub")
        if not user_id:
            raise ClerkTokenInvalidError("Token no contiene 'sub' claim")

        email = clerk_data.get("email")
        name = clerk_data.get("name")

        # 2. Buscar usuario en BD
        user_entity = self._user_repository.get_by_id(user_id)

        # 3. Crear o actualizar usuario
        if not user_entity:
            user_entity = self._user_repository.create(
                user_id=user_id,
                email=email,
                name=name,
            )
        else:
            user_entity = self._user_repository.update(
                user=user_entity,
                email=email,
                name=name,
            )

        # 4. Convertir a schema
        return self._entity_to_schema(user_entity)

    def get_user_from_token(self, token: str) -> User:
        """
        Obtiene un User schema a partir de un token válido.

        No sincroniza con la BD, solo valida el token.
        Útil para el middleware de protección de rutas.

        Args:
            token: Token JWT de Clerk.

        Returns:
            User schema con datos del token.

        Raises:
            ClerkTokenError: Si el token es inválido o expirado.
        """
        clerk_data = self._clerk_client.verify_token(token)

        user_id = clerk_data.get("sub")
        if not user_id:
            raise ClerkTokenInvalidError("Token no contiene 'sub' claim")

        return User(
            id=user_id,
            email=clerk_data.get("email", ""),
            name=clerk_data.get("name"),
            role=Role.DEVELOPER,
        )

    def _entity_to_schema(self, entity: UserEntity) -> User:
        """
        Convierte UserEntity a User schema.

        Args:
            entity: Entidad de usuario.

        Returns:
            User schema.
        """
        return User(
            id=entity.id,
            email=entity.email,
            name=entity.name,
            role=Role(entity.role.value.lower()),
        )
