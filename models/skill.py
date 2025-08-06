from sqlalchemy import Column, String, Integer, Text, Index, Boolean, DateTime, text, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
from datetime import datetime

class Skill(BaseModel):
    """Skill taxonomy model for standardizing skill names"""
    __tablename__ = "skills"
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_skill_name', 'name'),
        Index('idx_skill_category', 'category'),
        Index('idx_skill_is_active', 'is_active'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Skill information
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # e.g., "programming", "database", "framework"
    description = Column(Text, nullable=True)
    
    # Skill metadata
    aliases = Column(Text, nullable=True)  # JSON array of alternative names
    parent_skill_id = Column(Integer, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)  # For skill hierarchies (e.g., SQL -> PostgreSQL)
    
    # System fields
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=text('now()'), nullable=False)
    
    # Relationships
    parent_skill = relationship("Skill", remote_side=[id], backref="child_skills")
    job_skills = relationship("JobSkill", back_populates="skill", cascade="all, delete-orphan")
    candidate_skills = relationship("CandidateSkill", back_populates="skill", cascade="all, delete-orphan") 