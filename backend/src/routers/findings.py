"""
Router para hallazgos (findings) con explicaciones de IA.

Endpoints:
- GET /api/v1/findings/{id} - Obtener un hallazgo
- POST /api/v1/findings/{id}/explain - Generar explicación con IA
- GET /api/v1/findings/{id}/explain/status - Estado del rate limit

Principios de diseño:
- SRP: Solo maneja HTTP, delega lógica a servicios
- Defensibilidad: Validación de entrada y manejo de errores
- Seguridad: Requiere autenticación para todas las operaciones
"""

from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.config.ai_config import get_ai_settings
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.get_db import get_db
from src.models.finding import AgentFindingEntity
from src.schemas.ai_explanation import (
    AIExplanation,
    AIExplanationError,
    AIExplanationRequest,
    AIExplanationResponse,
    RateLimitInfo,
)
from src.schemas.finding import Finding, Severity
from src.schemas.user import User
from src.services.ai_service import (
    AIExplainerService,
)
from src.services.ai_service import AIExplanationError as ServiceAIError
from src.services.ai_service import (
    RateLimitExceeded,
    get_ai_explainer_service,
)
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])


def _entity_to_finding(entity: AgentFindingEntity) -> Finding:
    """
    Convierte una entidad de BD a esquema Finding.

    Args:
        entity: Entidad de base de datos

    Returns:
        Esquema Finding
    """
    return Finding(
        severity=Severity(entity.severity.value),
        issue_type=entity.issue_type,
        message=entity.message,
        line_number=entity.line_number,
        agent_name=entity.agent_type,
        code_snippet=entity.code_snippet,
        suggestion=entity.suggestion,
        rule_id=entity.issue_type,  # Usar issue_type como rule_id si no hay otro
    )


@router.get(
    "/{finding_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Obtener un hallazgo por ID",
)
async def get_finding(
    finding_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Obtiene los detalles de un hallazgo específico.

    Args:
        finding_id: UUID del hallazgo
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Detalles del hallazgo

    Raises:
        HTTPException 404: Si el hallazgo no existe
    """
    finding = db.query(AgentFindingEntity).filter(AgentFindingEntity.id == finding_id).first()

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Hallazgo {finding_id} no encontrado"
        )

    return {
        "id": str(finding.id),
        "agent_type": finding.agent_type,
        "severity": finding.severity.value,
        "issue_type": finding.issue_type,
        "line_number": finding.line_number,
        "message": finding.message,
        "code_snippet": finding.code_snippet,
        "suggestion": finding.suggestion,
        "ai_explanation": finding.ai_explanation,
        "created_at": finding.created_at.isoformat(),
    }


@router.post(
    "/{finding_id}/explain",
    response_model=AIExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar explicación con IA para un hallazgo",
    responses={
        200: {"description": "Explicación generada exitosamente"},
        404: {"description": "Hallazgo no encontrado"},
        429: {"description": "Rate limit excedido"},
        503: {"description": "Servicio de IA no disponible"},
    },
)
async def explain_finding(
    finding_id: UUID,
    request: AIExplanationRequest = AIExplanationRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AIExplainerService = Depends(get_ai_explainer_service),
) -> AIExplanationResponse:
    """
    Genera una explicación detallada de un hallazgo usando IA generativa.

    Este endpoint:
    1. Verifica si ya existe una explicación en cache (JSONB)
    2. Si no, genera una nueva usando Vertex AI (Gemini)
    3. Almacena la explicación en cache para futuras consultas

    Reglas de Negocio:
    - **RN1**: Requiere autenticación JWT
    - **RN**: Rate limit de 10 requests/hora por usuario (configurable)
    - **RN**: La explicación se cachea en BD para evitar regeneración

    Args:
        finding_id: UUID del hallazgo a explicar
        request: Opciones de la explicación
        current_user: Usuario autenticado
        db: Sesión de base de datos
        service: Servicio de explicaciones de IA

    Returns:
        AIExplanationResponse con la explicación generada

    Raises:
        HTTPException 404: Si el hallazgo no existe
        HTTPException 429: Si se excede el rate limit
        HTTPException 503: Si el servicio de IA no está disponible
    """
    # 1. Verificar que el servicio está configurado
    settings = get_ai_settings()
    if not settings.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de IA no está configurado. "
            "Configure GOOGLE_APPLICATION_CREDENTIALS.",
        )

    # 2. Buscar el hallazgo
    finding_entity = (
        db.query(AgentFindingEntity).filter(AgentFindingEntity.id == finding_id).first()
    )

    if not finding_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Hallazgo {finding_id} no encontrado"
        )

    # 3. Verificar cache (ai_explanation JSONB)
    if finding_entity.ai_explanation:
        logger.info(f"Returning cached AI explanation for finding {finding_id}")
        cached_explanation = AIExplanation.from_dict(finding_entity.ai_explanation)
        return AIExplanationResponse(
            finding_id=finding_id.int,
            explanation=cached_explanation,
            cached=True,
        )

    # 4. Generar nueva explicación
    try:
        # Convertir entidad a Finding schema
        finding = _entity_to_finding(finding_entity)

        # Obtener código fuente del code_review si existe
        code_context = None
        if finding_entity.code_review and hasattr(finding_entity.code_review, "source_code"):
            code_context = finding_entity.code_review.source_code

        # Generar explicación
        explanation, rate_limit_info = await service.explain_finding(
            finding=finding,
            code_context=code_context,
            user_id=current_user.id,
        )

        # 5. Guardar en cache (JSONB)
        finding_entity.ai_explanation = explanation.to_dict()
        db.commit()

        logger.info(
            f"AI explanation generated and cached for finding {finding_id}. "
            f"Tokens used: {explanation.tokens_used}"
        )

        return AIExplanationResponse(
            finding_id=finding_id.int,
            explanation=explanation,
            cached=False,
        )

    except RateLimitExceeded as e:
        logger.warning(f"Rate limit exceeded for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=AIExplanationError(
                error_type="rate_limit",
                message="Has excedido el límite de explicaciones por hora. "
                f"Límite: {e.rate_limit_info.requests_limit}/hora.",
                rate_limit_info=e.rate_limit_info,
            ).model_dump(),
        ) from e

    except ServiceAIError as e:
        logger.error(f"AI service error for finding {finding_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=AIExplanationError(
                error_type="ai_error",
                message=str(e),
            ).model_dump(),
        ) from e

    except Exception as e:
        logger.error(f"Unexpected error explaining finding {finding_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno generando explicación",
        ) from e


@router.get(
    "/{finding_id}/explain/status",
    response_model=RateLimitInfo,
    status_code=status.HTTP_200_OK,
    summary="Obtener estado del rate limit para explicaciones",
)
async def get_rate_limit_status(
    finding_id: UUID,  # Solo para consistencia de URL
    current_user: User = Depends(get_current_user),
    service: AIExplainerService = Depends(get_ai_explainer_service),
) -> RateLimitInfo:
    """
    Obtiene el estado actual del rate limit del usuario.

    Útil para mostrar al usuario cuántas explicaciones puede
    solicitar antes de alcanzar el límite.

    Args:
        finding_id: UUID del hallazgo (no usado, solo para URL)
        current_user: Usuario autenticado
        service: Servicio de explicaciones

    Returns:
        RateLimitInfo con requests restantes y tiempo de reset
    """
    return service.get_rate_limit_info(current_user.id)
