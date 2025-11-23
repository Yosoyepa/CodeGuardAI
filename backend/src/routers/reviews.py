""" Router for code review operations """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..repositories.code_review_repo import CodeReviewRepository
from ..schemas.analysis import AnalyzeResponse, FindingOut
from typing import List

router = APIRouter(prefix="/api/v1", tags=["reviews"])


def get_db():
    """ Dependency to get DB session """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# retrieve a code review and its findings by review ID
@router.get("/reviews/{review_id}", response_model=AnalyzeResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """ Retrieve a code review and its findings by review ID """
    repo = CodeReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    # Prepare findings for response
    findings = []
    for f in getattr(review, "findings", []):
        findings.append(
            FindingOut(
                agent_type=f.agent_type,
                severity=f.severity,
                issue_type=f.issue_type,
                line_number=f.line_number,
                message=f.message,
            )
        )

    return AnalyzeResponse(id=review.id, filename=review.filename, totalFindings=len(findings), findings=findings)
