"""
Repositorio para operaciones CRUD de usuarios.

Maneja la persistencia en la tabla 'users' usando UserEntity.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.models.enums.user_role import UserRole
from src.models.user import UserEntity


class UserRepository:
    """
    Repositorio para gestionar usuarios en la base de datos.

    Responsabilidad única: operaciones de persistencia sobre la tabla users.
    """

    def __init__(self, db: Session):
        """
        Inicializa el repositorio con una sesión de base de datos.

        Args:
            db: Sesión de SQLAlchemy.
        """
        self._db = db

    def get_by_id(self, user_id: str) -> Optional[UserEntity]:
        """
        Busca un usuario por su ID (Clerk user_id).

        Args:
            user_id: ID del usuario (Clerk sub).

        Returns:
            UserEntity si existe, None si no.
        """
        return self._db.query(UserEntity).filter(UserEntity.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        """
        Busca un usuario por su email.

        Args:
            email: Email del usuario.

        Returns:
            UserEntity si existe, None si no.
        """
        return self._db.query(UserEntity).filter(UserEntity.email == email).first()

    def create(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        role: UserRole = UserRole.DEVELOPER,
    ) -> UserEntity:
        """
        Crea un nuevo usuario en la base de datos.

        Args:
            user_id: ID del usuario (Clerk sub).
            email: Email del usuario.
            name: Nombre del usuario (opcional).
            avatar_url: URL del avatar (opcional).
            role: Rol del usuario (default: DEVELOPER).

        Returns:
            UserEntity creado.
        """
        now = datetime.utcnow()
        user = UserEntity(
            id=user_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
            role=role,
            daily_analysis_count=0,
            created_at=now,
            updated_at=now,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update(
        self,
        user: UserEntity,
        email: Optional[str] = None,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> UserEntity:
        """
        Actualiza los datos de un usuario existente.

        Args:
            user: Entidad de usuario a actualizar.
            email: Nuevo email (opcional).
            name: Nuevo nombre (opcional).
            avatar_url: Nueva URL de avatar (opcional).

        Returns:
            UserEntity actualizado.
        """
        if email is not None:
            user.email = email
        if name is not None:
            user.name = name
        if avatar_url is not None:
            user.avatar_url = avatar_url

        user.updated_at = datetime.utcnow()
        self._db.commit()
        self._db.refresh(user)
        return user

    def delete(self, user: UserEntity) -> None:
        """
        Elimina un usuario de la base de datos.

        Args:
            user: Entidad de usuario a eliminar.
        """
        self._db.delete(user)
        self._db.commit()

    def increment_analysis_count(self, user: UserEntity) -> UserEntity:
        """
        Incrementa el contador de análisis del usuario.

        Args:
            user: Entidad de usuario.

        Returns:
            UserEntity con contador actualizado.
        """
        user.increment_analysis_count()
        self._db.commit()
        self._db.refresh(user)
        return user
