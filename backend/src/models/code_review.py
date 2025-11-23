""" Model for code_reviews table """
from sqlalchemy import Column, Integer, String, DateTime, func
from ..core.database import Base


class CodeReview(Base):
    """ Model for code_reviews table """
    __tablename__ = "code_reviews"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
