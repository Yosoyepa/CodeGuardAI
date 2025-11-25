"""
Esquemas de análisis usando Pydantic v2
"""

import ast as python_ast
from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator

from src.models.enums.review_status import ReviewStatus


class AnalysisContext(BaseModel):
    """
    Contexto de análisis que encapsula toda la información de un análisis.

    Se pasa entre agentes para que cada uno realice su análisis específico.

    Attributes:
        code_content: Código Python a analizar
        filename: Nombre del archivo (debe terminar en .py)
        language: Lenguaje de programación (default: python)
        analysis_id: UUID único del análisis
        metadata: Información adicional (usuario, timestamp, etc.)
        created_at: Timestamp UTC de creación

    Example:
        context = AnalysisContext(
            code_content="def hello():\n    print('Hello')",
            filename="app.py",
            metadata={"user_id": "123"}
        )
    """

    code_content: str = Field(..., min_length=1, description="Código Python a analizar")
    filename: str = Field(
        ..., min_length=3, description="Nombre del archivo (debe terminar en .py)"
    )
    language: str = Field(default="python", description="Lenguaje de programación")
    analysis_id: UUID = Field(default_factory=uuid4, description="ID único del análisis")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Información adicional")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp UTC de creación"
    )

    # Se Usa PrivateAttr en Pydantic v2 por sugerencia
    _ast_cache: Optional[python_ast.Module] = PrivateAttr(default=None)
    _lines_cache: Optional[List[str]] = PrivateAttr(default=None)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "code_content": "def hello():\n    print('Hello World')",
                "filename": "example.py",
                "language": "python",
                "metadata": {"user_id": "123", "project": "CodeGuard"},
            }
        },
    )

    @field_validator("code_content")
    @classmethod
    def validate_code_content(cls, v: str) -> str:
        """Valida que el código no esté vacío."""
        if not v or not v.strip():
            raise ValueError("code_content cannot be empty or whitespace only")
        return v

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Valida que sea archivo Python."""
        if not v.endswith(".py"):
            raise ValueError("Only Python files (.py) are supported")
        if not v or len(v) < 3:
            raise ValueError("filename must be at least 3 characters")
        return v

    @model_validator(mode="after")
    def _normalize_code_content(self) -> "AnalysisContext":
        """
        Normaliza el código eliminando la indentación común para evitar
        SyntaxError cuando se parsean fixtures con sangría artificial.
        """
        self.code_content = dedent(self.code_content)
        return self

    @property
    def line_count(self) -> int:
        """Retorna el número de líneas del código."""
        return len(self.code_content.splitlines())  # pylint: disable=no-member

    @property
    def char_count(self) -> int:
        """Retorna el número de caracteres del código."""
        return len(self.code_content)

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Agrega una entrada a la metadata del contexto.

        Args:
            key: Clave de la metadata
            value: Valor de la metadata
        """
        self.metadata[key] = value

    def get_ast(self) -> python_ast.Module:
        """
        Retorna el AST parseado del código (lazy loading).

        Returns:
            AST Module del código Python

        Raises:
            SyntaxError: Si el código no es Python válido
        """
        if self._ast_cache is None:
            try:
                self._ast_cache = python_ast.parse(self.code_content, filename=self.filename)
            except SyntaxError as e:
                raise SyntaxError(f"Invalid Python syntax in {self.filename}: {e}") from e
        return self._ast_cache

    def get_lines(self) -> List[str]:
        """
        Retorna el código como lista de líneas (lazy loading).

        Returns:
            Lista de strings, una por línea
        """
        if self._lines_cache is None:
            self._lines_cache = self.code_content.splitlines()  # pylint: disable=no-member
        return self._lines_cache

    def get_line(self, line_number: int) -> Optional[str]:
        """
        Retorna una línea específica del código (1-based indexing).

        Args:
            line_number: Número de línea (1-based)

        Returns:
            String con la línea o None si no existe
        """
        lines = self.get_lines()
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return None

    def get_code_snippet(self, start_line: int, end_line: int) -> str:
        """
        Retorna un fragmento de código entre líneas.

        Args:
            start_line: Línea inicial (1-based, inclusiva)
            end_line: Línea final (1-based, inclusiva)

        Returns:
            String con el fragmento de código
        """
        lines = self.get_lines()
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        return "\n".join(lines[start_idx:end_idx])


class AnalysisRequest(BaseModel):
    """
    Request para iniciar un análisis de código.

    Attributes:
        filename: Nombre del archivo
        code_content: Código a analizar
        agents_config: Configuración de qué agentes ejecutar
    """

    filename: str = Field(..., min_length=3, description="Nombre del archivo")
    code_content: str = Field(..., min_length=1, description="Código a analizar")
    agents_config: Optional[Dict[str, bool]] = Field(
        default=None, description="Qué agentes ejecutar"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "app.py",
                "code_content": "import os\n\ndef main():\n    pass",
                "agents_config": {
                    "security": True,
                    "quality": True,
                    "performance": False,
                    "style": True,
                },
            }
        }
    )


class AnalysisResponse(BaseModel):
    """
    Response cuando se inicia un análisis.

    Attributes:
        analysis_id: UUID del análisis
        filename: Nombre del archivo
        status: Estado actual (pending, processing, completed, failed)
        created_at: Timestamp de creación
    """

    analysis_id: UUID = Field(..., description="ID único del análisis")
    filename: str = Field(..., description="Nombre del archivo")
    status: str = Field(..., description="Estado del análisis")
    quality_score: int = Field(..., ge=0, le=100, description="Puntaje de calidad")
    total_findings: int = Field(..., ge=0, description="Total de hallazgos")
    created_at: datetime = Field(..., description="Timestamp de creación")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "app.py",
                "status": "pending",
                "created_at": "2025-11-06T21:00:00Z",
            }
        }
    )


class CodeReview(BaseModel):
    """
    Modelo de dominio para una revisión de código completa.

    Este modelo representa la información que fluye entre la capa de persistencia
    y la capa de servicio. Contiene el código desencriptado listo para ser usado.

    Attributes:
        id: Identificador único de la revisión.
        user_id: ID del usuario propietario.
        filename: Nombre del archivo analizado.
        code_content: Contenido del código fuente (texto plano).
        quality_score: Puntaje de calidad calculado (0-100).
        status: Estado actual del análisis.
        total_findings: Cantidad total de hallazgos detectados.
        created_at: Fecha de creación.
        completed_at: Fecha de finalización (opcional).
    """

    id: UUID = Field(..., description="ID único de la revisión")
    user_id: str = Field(..., description="ID del usuario propietario (Clerk ID)")
    filename: str = Field(..., description="Nombre del archivo analizado")
    code_content: str = Field(..., description="Contenido del código fuente desencriptado")
    quality_score: int = Field(..., ge=0, le=100, description="Puntaje de calidad (0-100)")
    status: ReviewStatus = Field(..., description="Estado actual del análisis")
    total_findings: int = Field(default=0, ge=0, description="Total de hallazgos encontrados")
    created_at: datetime = Field(..., description="Fecha de creación del análisis")
    completed_at: Optional[datetime] = Field(default=None, description="Fecha de finalización")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user_2819",
                "filename": "main.py",
                "code_content": "print('Hello World')",
                "quality_score": 85,
                "status": "completed",
                "total_findings": 3,
                "created_at": "2025-11-22T10:00:00Z",
            }
        },
    )
