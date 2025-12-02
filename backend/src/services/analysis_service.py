"""
Servicio de análisis de código para CodeGuard AI.
"""

from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from src.agents.quality_agent import QualityAgent
from src.agents.security_agent import SecurityAgent
from src.core.events.analysis_events import AnalysisEventType
from src.core.events.event_bus import EventBus
from src.models.enums.review_status import ReviewStatus
from src.repositories.code_review_repository import CodeReviewRepository
from src.schemas.analysis import AnalysisContext, CodeReview
from src.schemas.finding import Finding, Severity
from src.utils.logger import logger


class AnalysisService:
    """
    Servicio de aplicación para orquestar el análisis de código.
    Coordina la validación, ejecución de agentes y persistencia.
    """

    def __init__(self, repo: CodeReviewRepository):
        """
        Inicializa el servicio con sus dependencias.

        Args:
            repo: Repositorio para persistencia de revisiones.
        """
        self.repo = repo
        self.event_bus = EventBus()

    async def analyze_code(self, file: UploadFile, user_id: str) -> CodeReview:
        """
        Procesa un archivo subido, ejecuta el análisis y guarda los resultados.

        Flujo (RN4, RN5, RN8):
        1. Validar archivo.
        2. Crear contexto de análisis.
        3. Ejecutar SecurityAgent.
        4. Calcular métricas.
        5. Persistir resultados.

        Args:
            file: Archivo subido por el usuario.
            user_id: ID del usuario autenticado.

        Returns:
            CodeReview: Resultado del análisis persistido.

        Raises:
            HTTPException: Si el archivo no es válido (422) o muy grande (413).
        """
        logger.info(f"Iniciando análisis para usuario {user_id} archivo {file.filename}")

        # 1. Validación de Archivo (RN4)
        content, filename = await self._validate_file(file)

        # 2. Preparar Contexto
        analysis_id = uuid4()
        context = AnalysisContext(
            code_content=content,
            filename=filename,
            analysis_id=analysis_id,
            metadata={"user_id": user_id},
        )

        # Notificar inicio usando el Enum
        self.event_bus.publish(AnalysisEventType.ANALYSIS_STARTED, {"id": str(analysis_id)})

        # 3. Ejecutar Agentes (SecurityAgent y QualityAgent)
        findings: List[Finding] = []

        # Security Agent
        try:
            agent = SecurityAgent()
            findings = agent.analyze(context)
        except Exception as e:
            logger.error(f"Error ejecutando SecurityAgent: {e}")

        # Quality Agent
        try:
            quality_agent = QualityAgent()
            findings.extend(quality_agent.analyze(context))
        except Exception as e:
            logger.error(f"Error ejecutando QualityAgent: {e}")

        # 4. Calcular Quality Score (RN8)
        quality_score = self._calculate_quality_score(findings)

        # 5. Construir Objeto de Dominio para persistencia
        review = CodeReview(
            id=analysis_id,
            user_id=user_id,
            filename=filename,
            code_content=content,
            quality_score=quality_score,
            status=ReviewStatus.COMPLETED,
            total_findings=len(findings),
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        # 6. Persistir (RN14)
        saved_review = self.repo.create(review)

        # Notificar fin usando el Enum
        self.event_bus.publish(
            AnalysisEventType.ANALYSIS_COMPLETED,
            {"id": str(analysis_id), "score": quality_score},
        )

        return saved_review

    async def _validate_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        Valida las restricciones del archivo (RN4).

        Args:
            file: Archivo subido por el usuario.

        Returns:
            Tuple[str, str]: (contenido, nombre_archivo)

        Raises:
            HTTPException: Si el archivo no cumple las validaciones.
        """
        # Validar que filename exista
        if not file.filename:
            raise HTTPException(
                status_code=422,
                detail="El nombre del archivo es requerido",
            )

        filename = file.filename

        if not filename.endswith(".py"):
            raise HTTPException(status_code=422, detail="Solo se aceptan archivos .py")

        # Leer contenido
        content_bytes = await file.read()

        # Validar tamaño (10MB = 10 * 1024 * 1024 bytes)
        if len(content_bytes) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="El tamaño del archivo excede el límite de 10 MB",
            )

        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail="El archivo debe tener codificación UTF-8 válida",
            ) from exc

        # Validar contenido vacío
        lines = [line for line in content.splitlines() if line.strip()]
        if len(lines) < 5:
            raise HTTPException(
                status_code=422,
                detail="El archivo debe tener al menos 5 líneas de código",
            )

        # Resetear puntero del archivo
        await file.seek(0)

        return content, filename

    def _calculate_quality_score(self, findings: List[Finding]) -> int:
        """
        Calcula el puntaje de calidad basado en penalizaciones (RN8).

        Fórmula: score = max(0, 100 - penalizaciones)

        Args:
            findings: Lista de hallazgos detectados.

        Returns:
            int: Puntaje de calidad (0-100).
        """
        penalty = 0
        for finding in findings:
            if finding.severity == Severity.CRITICAL:
                penalty += 10
            elif finding.severity == Severity.HIGH:
                penalty += 5
            elif finding.severity == Severity.MEDIUM:
                penalty += 2
            elif finding.severity == Severity.LOW:
                penalty += 1

        return max(0, 100 - penalty)
