from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum


class InteractionTypeEnum(str, enum.Enum):
    """Interaction type enumeration"""
    APPLIED = "Applied"
    REJECTED = "Rejected"
    VIEW = "View"
    SAVED = "Saved"


class InteractionLog(BaseModel):
    """User interaction log model"""
    __tablename__ = "interaction_logs"
    
    job_id = Column(Integer, nullable=False, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    interaction_type = Column(
        SQLEnum(InteractionTypeEnum),
        nullable=False,
        index=True
    )
    
    # Relationships
    job = relationship("Job", back_populates="interactions")
    candidate = relationship("Candidate", back_populates="interactions")
