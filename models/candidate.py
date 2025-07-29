# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from sqlalchemy import Column, String, Integer, Text, ARRAY, Float
# from sqlalchemy.orm import relationship
# from models.base import BaseModel

# class Candidate(BaseModel):
#     """Candidate model"""
#     __tablename__ = "candidates"
    
#     name = Column(String(255), nullable=False, index=True)
#     location = Column(String(100), nullable=False, index=True)
#     expected_salary_min = Column(Integer, nullable=True)
#     expected_salary_max = Column(Integer, nullable=True)
#     domain = Column(String(100), nullable=False, index=True)
#     summary_embedding = Column(ARRAY(Float), nullable=True)
    
#     # Relationships
#     experiences = relationship("CandidateExperience", back_populates="candidate", cascade="all, delete-orphan")
#     applications = relationship("Application", back_populates="candidate")
#     interactions = relationship("InteractionLog", back_populates="candidate")


# class CandidateExperience(BaseModel):
#     """Candidate experience model"""
#     __tablename__ = "candidate_experience"
    
#     candidate_id = Column(Integer, nullable=False, index=True)
#     skill = Column(String(100), nullable=False, index=True)
#     years = Column(Integer, nullable=False)
#     description = Column(Text, nullable=True)
#     embedding = Column(ARRAY(Float), nullable=True)
    
#     # Relationships
#     candidate = relationship("Candidate", back_populates="experiences")

# Removed manual path manipulation (Issue #3)
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel  # Use relative import

class Candidate(BaseModel):
    """Candidate model"""
    __tablename__ = "candidates"
    
    # Add composite indexes for better query performance (Issue #10)
    __table_args__ = (
        Index('idx_candidate_domain_location', 'domain', 'location'),
        Index('idx_candidate_salary', 'expected_salary_min', 'expected_salary_max'),
    )
    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)
    password = Column(String(255), nullable=False)
    expected_salary_min = Column(Integer, nullable=True)
    expected_salary_max = Column(Integer, nullable=True)
    domain = Column(String(100), nullable=False, index=True)
    summary = Column(Text, nullable=True)  # Only summary, no embedding
    email = Column(String(255), nullable=False, unique=True, index=True)
    
    # Relationships
    experiences = relationship("CandidateExperience", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    interactions = relationship("InteractionLog", back_populates="candidate", cascade="all, delete-orphan")

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