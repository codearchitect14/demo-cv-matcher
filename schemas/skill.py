from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SkillBase(BaseModel):
    """Base skill schema"""
    name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    description: Optional[str] = None
    aliases: Optional[str] = None  # JSON array of alternative names
    parent_skill_id: Optional[int] = None

class SkillCreate(SkillBase):
    """Schema for creating a new skill"""
    pass

class SkillUpdate(BaseModel):
    """Schema for updating a skill"""
    name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    aliases: Optional[str] = None
    parent_skill_id: Optional[int] = None
    is_active: Optional[bool] = None

class SkillResponse(SkillBase):
    """Schema for skill response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobSkillBase(BaseModel):
    """Base job skill schema"""
    skill_id: int
    min_years_experience: float = Field(..., ge=0.0)
    priority: str = Field(..., regex="^(required|preferred|nice_to_have)$")
    description: Optional[str] = None

class JobSkillCreate(JobSkillBase):
    """Schema for creating a new job skill requirement"""
    pass

class JobSkillUpdate(BaseModel):
    """Schema for updating a job skill requirement"""
    skill_id: Optional[int] = None
    min_years_experience: Optional[float] = Field(None, ge=0.0)
    priority: Optional[str] = Field(None, regex="^(required|preferred|nice_to_have)$")
    description: Optional[str] = None

class JobSkillResponse(JobSkillBase):
    """Schema for job skill response"""
    id: int
    job_id: int
    skill: SkillResponse
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CandidateSkillBase(BaseModel):
    """Base candidate skill schema"""
    skill_id: int
    years_experience: float = Field(..., ge=0.0)
    proficiency_level: str = Field(..., regex="^(beginner|intermediate|advanced|expert)$")
    last_used: Optional[datetime] = None
    experience_description: Optional[str] = None
    projects_worked: Optional[str] = None  # JSON array

class CandidateSkillCreate(CandidateSkillBase):
    """Schema for creating a new candidate skill experience"""
    pass

class CandidateSkillUpdate(BaseModel):
    """Schema for updating a candidate skill experience"""
    skill_id: Optional[int] = None
    years_experience: Optional[float] = Field(None, ge=0.0)
    proficiency_level: Optional[str] = Field(None, regex="^(beginner|intermediate|advanced|expert)$")
    last_used: Optional[datetime] = None
    experience_description: Optional[str] = None
    projects_worked: Optional[str] = None

class CandidateSkillResponse(CandidateSkillBase):
    """Schema for candidate skill response"""
    id: int
    candidate_id: int
    skill: SkillResponse
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 