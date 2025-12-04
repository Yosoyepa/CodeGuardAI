from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.core.dependencies.auth import get_current_user
from src.core.dependencies.get_db import get_db
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
