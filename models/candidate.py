import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, String, Integer, Text, ARRAY, Float
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Candidate(BaseModel):
    """Candidate model"""
    __tablename__ = "candidates"
    
    name = Column(String(255), nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)
    expected_salary_min = Column(Integer, nullable=True)
    expected_salary_max = Column(Integer, nullable=True)
    domain = Column(String(100), nullable=False, index=True)
    summary_embedding = Column(ARRAY(Float), nullable=True)
    
    # Relationships
    experiences = relationship("CandidateExperience", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate")
    interactions = relationship("InteractionLog", back_populates="candidate")


class CandidateExperience(BaseModel):
    """Candidate experience model"""
    __tablename__ = "candidate_experience"
    
    candidate_id = Column(Integer, nullable=False, index=True)
    skill = Column(String(100), nullable=False, index=True)
    years = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    embedding = Column(ARRAY(Float), nullable=True)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="experiences")