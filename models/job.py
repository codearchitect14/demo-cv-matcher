from sqlalchemy import Column, String, Integer, Text, ARRAY, Float
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Job(BaseModel):
    """Job model"""
    __tablename__ = "jobs"
    
    title = Column(String(255), nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    domain = Column(String(100), nullable=False, index=True)
    total_years_required = Column(Integer, nullable=False, default=0)
    job_description = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float), nullable=True)
    
    # Relationships
    mandatory_skills = relationship("JobMandatorySkill", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job")
    interactions = relationship("InteractionLog", back_populates="job")


class JobMandatorySkill(BaseModel):
    """Job mandatory skills model"""
    __tablename__ = "job_mandatory_skills"
    
    job_id = Column(Integer, nullable=False, index=True)
    skill = Column(String(100), nullable=False, index=True)
    min_experience = Column(Integer, nullable=False, default=0)
    
    # Relationships
    job = relationship("Job", back_populates="mandatory_skills")