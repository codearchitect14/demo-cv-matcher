from sqlalchemy import Column, String, Integer, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class Candidate(BaseModel):
    """Candidate model with role-based access control"""
    __tablename__ = "candidates"
    
    # Add composite indexes for better query performance (Issue #10)
    __table_args__ = (
        Index('idx_candidate_domain_location', 'domain', 'location'),
        Index('idx_candidate_salary', 'expected_salary_min', 'expected_salary_max'),
        Index('idx_candidate_role', 'role'),
        Index('idx_candidate_email', 'email'),  # Single column index for email lookups
        Index('idx_candidate_created_at', 'created_at'),  # Index for time-based queries
        Index('idx_candidate_updated_at', 'updated_at'),  # Index for update tracking
    )
    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    expected_salary_min = Column(Integer, nullable=True)
    expected_salary_max = Column(Integer, nullable=True)
    domain = Column(String(100), nullable=False, index=True)
    summary = Column(Text, nullable=True)  # Only summary, no embedding
    email = Column(String(255), nullable=False, unique=True, index=True)
    consent_given = Column(Boolean, nullable=False, default=False, index=True)
    role = Column(String(20), nullable=False, default="user", index=True)  # user, admin, moderator
    
    # Relationships
    experiences = relationship("CandidateExperience", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    candidate_skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    # interactions relationship removed - InteractionLog uses generic user_id approach
    
    @property
    def total_years_experience(self) -> float:
        """Calculate total years of experience from experiences"""
        if not self.experiences:
            return 0.0
        return sum(exp.years for exp in self.experiences)

class CandidateExperience(BaseModel):
    """Candidate experience model"""
    __tablename__ = "candidate_experience"
    
    # Add proper foreign key constraint with cascade delete (Issue #7)
    candidate_id = Column(
        Integer, 
        ForeignKey("candidates.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    skill = Column(String(100), nullable=False, index=True)
    years = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    # No embedding column
    candidate = relationship("Candidate", back_populates="experiences")