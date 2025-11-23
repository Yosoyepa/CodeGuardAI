"""Router for code analysis operations"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..core.config.settings import settings
from ..agents.security_agent import SecurityAgent
from ..repositories.code_review_repo import CodeReviewRepository
from ..schemas.analysis import AnalyzeResponse, FindingOut, AnalysisContext
from ..schemas.finding import Finding as FindingSchema
from typing import List

router = APIRouter(prefix="/api/v1", tags=["analysis"])


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


""" Endpoint to analyze uploaded code file """


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Validate and analyze uploaded code file"""
    # Validate extension
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are supported")
    # Validate size
    contents = await file.read()
    size = len(contents)
    if size == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")
    if size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    source = contents.decode("utf-8", errors="ignore")

    # Create review record
    repo = CodeReviewRepository(db)
    review = repo.create_review(file.filename)

    # Build analysis context and run security agent
    context = AnalysisContext(code_content=source, filename=file.filename)
    agent = SecurityAgent()
    findings = agent.analyze(context)

    # Persist findings
    for f in findings:
        # f is a Finding Pydantic model
        repo.add_finding(
            review_id=review.id,
            agent_type=f.agent_name if getattr(f, "agent_name", None) else "security",
            severity=f.severity.value if getattr(f, "severity", None) else "medium",
            issue_type=f.issue_type,
            line_number=f.line_number,
            message=f.message,
        )
    # Prepare response
    out_findings: List[FindingOut] = [
        FindingOut(
            agent_type=(f.agent_name if getattr(f, "agent_name", None) else "security"),
            severity=(f.severity.value if getattr(f, "severity", None) else "medium"),
            issue_type=f.issue_type,
            line_number=f.line_number,
            message=f.message,
        )
        for f in findings
    ]
    # Prepare and return response
    response = AnalyzeResponse(
        id=review.id, filename=file.filename, totalFindings=len(out_findings), findings=out_findings
    )
    return JSONResponse(status_code=200, content=response.model_dump(by_alias=True))
