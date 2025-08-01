# File: schemas/candidate.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class CandidateExperienceBase(BaseModel):
    """Base schema for candidate experience"""
    skill: str = Field(..., min_length=1, max_length=100)
    years: int = Field(..., ge=0, le=50)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('years')
    def validate_years(cls, v):
        if v < 0:
            raise ValueError('Years of experience cannot be negative')
        if v > 50:
            raise ValueError('Years of experience cannot exceed 50')
        return v

    @validator('skill')
    def validate_skill(cls, v):
        if not v.strip():
            raise ValueError('Skill name cannot be empty')
        return v.strip()


class CandidateExperienceCreate(CandidateExperienceBase):
    """Schema for creating candidate experience"""
    pass


class CandidateExperienceUpdate(CandidateExperienceBase):
    """Schema for updating candidate experience"""
    skill: Optional[str] = Field(None, min_length=1, max_length=100)
    years: Optional[int] = Field(None, ge=0, le=50)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('years')
    def validate_years(cls, v):
        if v is not None and v < 0:
            raise ValueError('Years of experience cannot be negative')
        if v is not None and v > 50:
            raise ValueError('Years of experience cannot exceed 50')
        return v

    @validator('skill')
    def validate_skill(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Skill name cannot be empty')
        return v.strip() if v else v


class CandidateExperienceResponse(CandidateExperienceBase):
    """Schema for candidate experience response"""
    id: int
    candidate_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CandidateBase(BaseModel):
    """Base schema for candidate"""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., description="Email address")
    location: str = Field(..., min_length=1, max_length=100)
    domain: str = Field(..., min_length=1, max_length=100)
    expected_salary_min: Optional[float] = Field(None, ge=0)
    expected_salary_max: Optional[float] = Field(None, ge=0)
    summary: Optional[str] = Field(None, max_length=2000)
    consent_given: bool = Field(False, description="GDPR consent flag")

    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()

    @validator('expected_salary_max')
    def validate_salary_range(cls, v, values):
        if v is not None and 'expected_salary_min' in values and values['expected_salary_min'] is not None:
            if v < values['expected_salary_min']:
                raise ValueError('expected_salary_max must be greater than or equal to expected_salary_min')
        return v

    @validator('name', 'location', 'domain')
    def validate_non_empty_strings(cls, v):
        if v and v.strip() == '':
            raise ValueError('Field cannot be empty')
        return v.strip()


class CandidateCreate(CandidateBase):
    """Schema for creating candidate"""
    pass


class CandidateUpdate(CandidateBase):
    """Schema for updating candidate"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, description="Email address")
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    domain: Optional[str] = Field(None, min_length=1, max_length=100)
    expected_salary_min: Optional[float] = Field(None, ge=0)
    expected_salary_max: Optional[float] = Field(None, ge=0)
    summary: Optional[str] = Field(None, max_length=2000)
    consent_given: Optional[bool] = Field(None)


class CandidateResponse(CandidateBase):
    """Schema for candidate response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    experiences: Optional[List[CandidateExperienceResponse]] = []
    
    class Config:
        from_attributes = True


class CandidateListResponse(CandidateBase):
    """Schema for candidate list response (without relationships)"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True