from sqlalchemy import Column, String, Integer, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Job(BaseModel):
    """Job model"""
    __tablename__ = "jobs"
    
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(100), nullable=True, index=True)
    location = Column(String(100), nullable=False, index=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    domain = Column(String(100), nullable=False, index=True)
    total_years_required = Column(Integer, nullable=False, default=0)
    job_description = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Relationships
    mandatory_skills = relationship("JobMandatorySkill", back_populates="job", cascade="all, delete-orphan")
    job_skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job")
    interactions = relationship("InteractionLog", back_populates="job")
    recruiter = relationship("Recruiter", back_populates="jobs")
    company = relationship("Company", back_populates="jobs")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_job_location_domain', 'location', 'domain'),
        Index('idx_job_salary_range', 'salary_min', 'salary_max'),
        Index('idx_job_domain_years', 'domain', 'total_years_required'),
        Index('idx_job_created_at', 'created_at'),  # Index for time-based queries
        Index('idx_job_updated_at', 'updated_at'),  # Index for update tracking
        Index('idx_job_title', 'title'),  # Index for title searches
        Index('idx_job_location', 'location'),  # Index for location filtering
        Index('idx_job_domain', 'domain'),  # Index for domain filtering
        Index('idx_job_recruiter', 'recruiter_id'),  # Index for recruiter-based job filtering
        Index('idx_job_company_id', 'company_id'),  # Index for company-based job filtering
    )


class JobMandatorySkill(BaseModel):
    """Job mandatory skills model"""
    __tablename__ = "job_mandatory_skills"
    
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill = Column(String(100), nullable=False, index=True)
    min_experience = Column(Integer, nullable=False, default=0)
    
    # Relationships
    job = relationship("Job", back_populates="mandatory_skills")