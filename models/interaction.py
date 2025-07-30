from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum


class InteractionTypeEnum(str, enum.Enum):
    """Interaction type enumeration"""
    VIEWED = "viewed"
    APPLIED = "applied"
    REJECTED = "rejected"


class InteractionLog(BaseModel):
    """User interaction log model"""
    __tablename__ = "interaction_log"
    
    user_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_type = Column(SQLEnum(InteractionTypeEnum), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="interactions")
    job = relationship("Job", back_populates="interactions")
