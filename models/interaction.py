from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum


class InteractionTypeEnum(str, enum.Enum):
    """Interaction type enumeration"""
    VIEWED = "viewed"
    APPLIED = "applied"
    REJECTED = "rejected"
    POSTED = "posted"
    EDITED = "edited"


class InteractionLog(BaseModel):
    """User interaction log model"""
    __tablename__ = "interaction_log"
    
    user_id = Column(Integer, nullable=False, index=True)  # Can be candidate_id or recruiter_id
    user_type = Column(String(20), nullable=False, index=True)  # "candidate" or "recruiter"
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_type = Column(SQLEnum(InteractionTypeEnum), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    # Removed candidate and recruiter relationships since we use generic user_id
    job = relationship("Job", back_populates="interactions")
