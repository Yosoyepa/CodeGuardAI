"""Schemas for findings detected during code analysis"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(BaseModel):
    severity: Severity
    issue_type: str
    message: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    agent_name: Optional[str] = None
    rule_id: Optional[str] = None

    @property
    def is_critical(self) -> bool:
        return self.severity == Severity.CRITICAL
