from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.core.dependencies.auth import get_current_user
from src.core.dependencies.get_db import get_db
from src.models.code_review import CodeReviewEntity
from src.models.finding import AgentFindingEntity
from src.repositories.code_review_repository import CodeReviewRepository
from src.schemas.analysis import AnalysisResponse
from src.schemas.user import User
from src.services.analysis_service import AnalysisService
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analizar código fuente Python",
)
async def analyze_code(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sube un archivo Python para análisis automatizado de seguridad y calidad.

    Reglas de Negocio:
    - **RN1**: Requiere autenticación JWT.
    - **RN3**: Verifica cuota diaria (Developers: 10/día).
    - **RN4**: Valida extensión .py, tamaño <10MB y codificación UTF-8.

    Args:
        file: Archivo .py a analizar.
        current_user: Usuario autenticado (inyectado).
        db: Sesión de base de datos (inyectada).

    Returns:
        AnalysisResponse: Objeto con ID de análisis, estado y resumen.

    Raises:
        HTTPException: 500 si ocurre un error interno.
    """

    repo = CodeReviewRepository(db)
    service = AnalysisService(repo)

    try:
        result = await service.analyze_code(file, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interno en análisis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor"
        ) from e

    return AnalysisResponse(
        analysis_id=result.id,
        filename=result.filename,
        status=result.status,
        quality_score=result.quality_score,
        total_findings=result.total_findings,
        created_at=result.created_at,
    )


@router.get(
    "/analyses/{analysis_id}/findings",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Obtener findings de un análisis",
)
async def get_analysis_findings(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Obtiene todos los findings de un análisis específico.

    Args:
        analysis_id: UUID del análisis
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de findings con sus detalles
    """
    # Verificar que el análisis existe
    analysis = db.query(CodeReviewEntity).filter(CodeReviewEntity.id == analysis_id).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Análisis {analysis_id} no encontrado"
        )

    # Obtener findings del análisis
    findings = (
        db.query(AgentFindingEntity)
        .filter(AgentFindingEntity.review_id == analysis_id)
        .order_by(AgentFindingEntity.line_number)
        .all()
    )

    return [
        {
            "id": str(f.id),
            "agent_type": f.agent_type,
            "severity": f.severity.value,
            "issue_type": f.issue_type,
            "line_number": f.line_number,
            "message": f.message,
            "code_snippet": f.code_snippet,
            "suggestion": f.suggestion,
            "ai_explanation": f.ai_explanation,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in findings
    ]
