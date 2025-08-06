from sqlalchemy import Column, String, Integer, Float, Text, Index, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship
from .base import BaseModel

class JobSkill(BaseModel):
    """Job skill requirements model - links jobs to required skills with experience levels"""
    __tablename__ = "job_skills"
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_job_skill_job_id', 'job_id'),
        Index('idx_job_skill_skill_id', 'skill_id'),
        Index('idx_job_skill_min_years', 'min_years_experience'),
        Index('idx_job_skill_priority', 'priority'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Skill requirements
    min_years_experience = Column(Float, nullable=False, default=0.0)  # Minimum years required
    priority = Column(String(20), nullable=False, default="required")  # "required", "preferred", "nice_to_have"
    description = Column(Text, nullable=True)  # Additional context about the skill requirement
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'), nullable=False)
    
    # Relationships
    job = relationship("Job", back_populates="job_skills")
    skill = relationship("Skill", back_populates="job_skills") 