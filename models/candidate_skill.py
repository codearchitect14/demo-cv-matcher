from sqlalchemy import Column, String, Integer, Float, Text, Index, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship
from .base import BaseModel
from datetime import datetime

class CandidateSkill(BaseModel):
    """Candidate skill experience model - links candidates to skills with experience duration"""
    __tablename__ = "candidate_skills"
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_candidate_skill_candidate_id', 'candidate_id'),
        Index('idx_candidate_skill_skill_id', 'skill_id'),
        Index('idx_candidate_skill_years_experience', 'years_experience'),
        Index('idx_candidate_skill_last_used', 'last_used'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Skill experience
    years_experience = Column(Float, nullable=False, default=0.0)  # Total years of experience
    proficiency_level = Column(String(20), nullable=False, default="beginner")  # "beginner", "intermediate", "advanced", "expert"
    last_used = Column(DateTime(timezone=True), nullable=True)  # When they last used this skill
    
    # Experience context
    experience_description = Column(Text, nullable=True)  # Description of experience with this skill
    projects_worked = Column(Text, nullable=True)  # JSON array of projects where this skill was used
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'), nullable=False)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="candidate_skills")
    skill = relationship("Skill", back_populates="candidate_skills") 