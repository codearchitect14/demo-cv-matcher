from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum


class ApplicationStatusEnum(str, enum.Enum):
    """Application status enumeration"""
    APPLIED = "Applied"
    REJECTED = "Rejected"
    ACCEPTED = "Accepted"


class Application(BaseModel):
    """Application model"""
    __tablename__ = "applications"
    
    job_id = Column(Integer, nullable=False, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    status = Column(
        SQLEnum(ApplicationStatusEnum),
        nullable=False,
        default=ApplicationStatusEnum.APPLIED,
        index=True
    )
    
    # Relationships
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")