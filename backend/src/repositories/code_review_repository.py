from typing import Optional
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models.code_review import CodeReviewEntity
from src.models.enums.severity_enum import SeverityEnum
from src.models.finding import AgentFindingEntity
from src.schemas.analysis import CodeReview
from src.utils.encryption.aes_encryptor import decrypt_aes256, encrypt_aes256
from src.utils.logger import logger


class CodeReviewRepository:
    """
    Repositorio para manejar la persistencia de las revisiones de código.

    Implementa el patrón Repository para desacoplar la lógica de negocio (Domain)
    de la implementación de base de datos (SQLAlchemy). Maneja automáticamente
    la encriptación/desencriptación del código fuente.
    """

    def __init__(self, session: Session):
        """
        Inicializa el repositorio con una sesión de base de datos.

        Args:
            session: Sesión activa de SQLAlchemy.
        """
        self.session = session

    def create(self, review: CodeReview) -> CodeReview:
        """
        Persiste una nueva entidad CodeReview en la base de datos.

        Aplica encriptación AES-256 al contenido del código antes de guardar,
        cumpliendo con la Regla de Negocio RN16.

        Args:
            review: Objeto de dominio CodeReview con los datos a guardar.

        Returns:
            CodeReview: El objeto de dominio confirmado y persistido.

        Raises:
            SQLAlchemyError: Si ocurre un error a nivel de base de datos.
            ValueError: Si el contenido del código es inválido para encriptar.
        """
        try:
            # RN16: Encriptar contenido sensible antes de tocar la BD
            encrypted_content = encrypt_aes256(review.code_content)

            entity = CodeReviewEntity(
                id=review.id,
                user_id=review.user_id,
                filename=review.filename,
                code_content=encrypted_content,
                quality_score=review.quality_score,
                status=review.status,
                total_findings=review.total_findings,
                created_at=review.created_at,
                completed_at=review.completed_at,
            )

            self.session.add(entity)

            # Persistir hallazgos (findings)
            for finding in review.findings:
                # Mapear severidad de Schema (lowercase) a Entity (uppercase)
                if finding.severity.name not in SeverityEnum.__members__:
                    logger.warning(
                        f"Finding with unsupported severity '{finding.severity.name}' "
                        f"skipped for review {review.id}."
                    )
                    continue
                severity_enum = SeverityEnum[finding.severity.name]

                finding_entity = AgentFindingEntity(
                    review_id=review.id,
                    agent_type=finding.agent_name,
                    severity=severity_enum,
                    issue_type=finding.issue_type,
                    line_number=finding.line_number,
                    code_snippet=finding.code_snippet,
                    message=finding.message,
                    suggestion=finding.suggestion,
                    created_at=finding.detected_at,
                )
                self.session.add(finding_entity)

            self.session.commit()

            logger.info(f"CodeReview persistido exitosamente: {review.id}")
            return review

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al crear CodeReview {review.id}: {str(e)}")
            raise e
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado en CodeReviewRepository.create: {str(e)}")
            raise e

    def find_by_id(self, review_id: UUID) -> Optional[CodeReview]:
        """
        Busca una revisión por su ID y desencripta el contenido automáticamente.

        Args:
            review_id: Identificador único (UUID) de la revisión.

        Returns:
            Optional[CodeReview]: Objeto de dominio reconstruido o None si no existe.

        Raises:
            Exception: Si falla la desencriptación o la lectura de BD.
        """
        try:
            entity = self.session.get(CodeReviewEntity, review_id)

            if not entity:
                return None

            decrypted_content = decrypt_aes256(entity.code_content)

            return CodeReview(
                id=entity.id,
                user_id=entity.user_id,
                filename=entity.filename,
                code_content=decrypted_content,
                quality_score=entity.quality_score,
                status=entity.status,
                total_findings=entity.total_findings,
                created_at=entity.created_at,
                completed_at=entity.completed_at,
            )
        except Exception as e:
            logger.error(f"Error recuperando CodeReview {review_id}: {str(e)}")
            raise e
