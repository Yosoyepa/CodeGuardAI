"""Schemas for code analysis operations"""

from pydantic import BaseModel, Field
from typing import List, Optional


class AnalysisContext(BaseModel):
    """Context for code analysis"""

    filename: str
    code_content: str


class FindingOut(BaseModel):
    """Output schema for a finding"""

    agent_type: str
    severity: str
    issue_type: str
    line_number: Optional[int]
    message: str


class AnalyzeResponse(BaseModel):
    """Response schema for code analysis"""

    id: Optional[int] = None
    filename: str
    total_findings: int = Field(..., alias="totalFindings")
    findings: List[FindingOut]
