from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum


class ApplicationStatusEnum(str, enum.Enum):
    """Application status enumeration"""
    APPLIED = "applied"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    PENDING = "pending"


class Application(BaseModel):
    """Application model"""
    __tablename__ = "applications"
    
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(SQLEnum(ApplicationStatusEnum), nullable=False, default=ApplicationStatusEnum.APPLIED, index=True)
    
    # Relationships
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    recruiter = relationship("Recruiter", back_populates="applications")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_application_candidate_job', 'candidate_id', 'job_id'),
        Index('idx_application_job_status', 'job_id', 'status'),
        Index('idx_application_candidate_status', 'candidate_id', 'status'),
        Index('idx_application_status_date', 'status', 'created_at'),
        Index('idx_application_recruiter', 'recruiter_id'),
    )