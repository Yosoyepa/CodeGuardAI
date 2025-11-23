"""Repository for code review operations"""

from sqlalchemy.orm import Session
from ..models.code_review import CodeReview
from ..models.finding import Finding


class CodeReviewRepository:
    def __init__(self, db: Session):
        """Initialize repository with database session"""
        self.db = db

    def create_review(self, filename: str) -> CodeReview:
        """Create a new CodeReview"""
        review = CodeReview(filename=filename)
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def add_finding(
        self,
        review_id: int,
        agent_type: str,
        severity: str,
        issue_type: str,
        line_number: int,
        message: str,
    ) -> Finding:
        """Add a Finding to a CodeReview"""
        f = Finding(
            code_review_id=review_id,
            agent_type=agent_type,
            severity=severity,
            issue_type=issue_type,
            line_number=line_number,
            message=message,
        )
        self.db.add(f)
        self.db.commit()
        self.db.refresh(f)
        return f

    def get_review(self, review_id: int) -> CodeReview:
        """Retrieve a CodeReview by its ID"""
        return self.db.query(CodeReview).filter(CodeReview.id == review_id).first()
