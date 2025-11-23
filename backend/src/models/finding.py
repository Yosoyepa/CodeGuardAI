"""Model for findings detected during code analysis"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class Finding(Base):
    """Model for agent_findings table"""

    __tablename__ = "agent_findings"

    id = Column(Integer, primary_key=True, index=True)
    code_review_id = Column(Integer, ForeignKey("code_reviews.id"), nullable=False)
    agent_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # Severity level of the finding
    issue_type = Column(String, nullable=False)  # Category of the issue found
    line_number = Column(Integer, nullable=True)  # Can be null for file-level issues
    message = Column(Text, nullable=False)  # Detailed message about the finding
    # Establish relationship with CodeReview
    review = relationship("CodeReview", backref="findings")
