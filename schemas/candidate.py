# File: schemas/candidate.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from schemas.validation import (
    NameValidation, EmailValidation, LocationValidation, DomainValidation, 
    DescriptionValidation, SalaryValidation, SkillValidation, ExperienceValidation
)

class CandidateExperienceBase(BaseModel):
    """Base schema for candidate experience with advanced validation"""
    skill: str = Field(..., min_length=1, max_length=100)
    years: int = Field(..., ge=0, le=50)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('skill')
    def validate_skill(cls, v):
        return SkillValidation(skill=v).skill

    @validator('years')
    def validate_years(cls, v):
        return ExperienceValidation(years=v).years

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return DescriptionValidation(description=v).description
        return v

class CandidateExperienceCreate(CandidateExperienceBase):
    """Schema for creating candidate experience"""
    pass

class CandidateExperienceUpdate(CandidateExperienceBase):
    """Schema for updating candidate experience"""
    skill: Optional[str] = Field(None, min_length=1, max_length=100)
    years: Optional[int] = Field(None, ge=0, le=50)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('skill')
    def validate_skill(cls, v):
        if v is not None:
            return SkillValidation(skill=v).skill
        return v

    @validator('years')
    def validate_years(cls, v):
        if v is not None:
            return ExperienceValidation(years=v).years
        return v

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return DescriptionValidation(description=v).description
        return v

class CandidateExperienceResponse(CandidateExperienceBase):
    """Schema for candidate experience response"""
    id: int
    candidate_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CandidateBase(BaseModel):
    """Base schema for candidate with comprehensive validation"""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254)
    location: str = Field(..., min_length=1, max_length=100)
    domain: str = Field(..., min_length=1, max_length=50)
    expected_salary_min: Optional[int] = Field(None, ge=0, le=1000000)
    expected_salary_max: Optional[int] = Field(None, ge=0, le=1000000)
    summary: str = Field(..., min_length=1, max_length=2000)
    role: str = Field("user", max_length=20)

    @validator('name')
    def validate_name(cls, v):
        return NameValidation(name=v).name

    @validator('email')
    def validate_email(cls, v):
        return EmailValidation(email=v).email

    @validator('location')
    def validate_location(cls, v):
        return LocationValidation(location=v).location

    @validator('domain')
    def validate_domain(cls, v):
        return DomainValidation(domain=v).domain

    @validator('summary')
    def validate_summary(cls, v):
        return DescriptionValidation(description=v).description

    @validator('expected_salary_min', 'expected_salary_max')
    def validate_salary(cls, v):
        if v is not None and v < 0:
            raise ValueError('Salary cannot be negative')
        if v is not None and v > 1000000:
            raise ValueError('Salary cannot exceed 1,000,000')
        return v

    @validator('expected_salary_max')
    def validate_salary_range(cls, v, values):
        min_salary = values.get('expected_salary_min')
        if v is not None and min_salary is not None and v < min_salary:
            raise ValueError('Maximum salary cannot be less than minimum salary')
        return v

    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ['user', 'admin', 'moderator']
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {allowed_roles}')
        return v

class CandidateCreate(CandidateBase):
    """Schema for creating a candidate"""
    password: str = Field(..., min_length=8, max_length=128)

    @validator('password')
    def validate_password(cls, v):
        from config.security import validate_password_strength
        if not validate_password_strength(v):
            raise ValueError('Password does not meet security requirements')
        return v

class CandidateUpdate(BaseModel):
    """Schema for updating a candidate"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=254)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    domain: Optional[str] = Field(None, min_length=1, max_length=50)
    expected_salary_min: Optional[int] = Field(None, ge=0, le=1000000)
    expected_salary_max: Optional[int] = Field(None, ge=0, le=1000000)
    summary: Optional[str] = Field(None, min_length=1, max_length=2000)
    role: Optional[str] = Field(None, max_length=20)

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            return NameValidation(name=v).name
        return v

    @validator('email')
    def validate_email(cls, v):
        if v is not None:
            return EmailValidation(email=v).email
        return v

    @validator('location')
    def validate_location(cls, v):
        if v is not None:
            return LocationValidation(location=v).location
        return v

    @validator('domain')
    def validate_domain(cls, v):
        if v is not None:
            return DomainValidation(domain=v).domain
        return v

    @validator('summary')
    def validate_summary(cls, v):
        if v is not None:
            return DescriptionValidation(description=v).description
        return v

    @validator('expected_salary_min', 'expected_salary_max')
    def validate_salary(cls, v):
        if v is not None and v < 0:
            raise ValueError('Salary cannot be negative')
        if v is not None and v > 1000000:
            raise ValueError('Salary cannot exceed 1,000,000')
        return v

    @validator('expected_salary_max')
    def validate_salary_range(cls, v, values):
        min_salary = values.get('expected_salary_min')
        if v is not None and min_salary is not None and v < min_salary:
            raise ValueError('Maximum salary cannot be less than minimum salary')
        return v

    @validator('role')
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ['user', 'admin', 'moderator']
            if v not in allowed_roles:
                raise ValueError(f'Role must be one of: {allowed_roles}')
        return v

class CandidateResponse(CandidateBase):
    """Schema for candidate response"""
    id: int
    created_at: datetime
    updated_at: datetime
    experiences: List[CandidateExperienceResponse] = []
    
    class Config:
        from_attributes = True

class CandidateSearchFilter(BaseModel):
    """Schema for candidate search filters with validation"""
    location: Optional[str] = Field(None, max_length=100)
    domain: Optional[str] = Field(None, max_length=50)
    salary_min: Optional[int] = Field(None, ge=0, le=1000000)
    salary_max: Optional[int] = Field(None, ge=0, le=1000000)
    required_skills: Optional[List[str]] = Field(None, max_items=20)
    
    @validator('location')
    def validate_location(cls, v):
        if v is not None:
            return LocationValidation(location=v).location
        return v

    @validator('domain')
    def validate_domain(cls, v):
        if v is not None:
            return DomainValidation(domain=v).domain
        return v

    @validator('salary_min', 'salary_max')
    def validate_salary(cls, v):
        if v is not None and v < 0:
            raise ValueError('Salary cannot be negative')
        if v is not None and v > 1000000:
            raise ValueError('Salary cannot exceed 1,000,000')
        return v

    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        min_salary = values.get('salary_min')
        if v is not None and min_salary is not None and v < min_salary:
            raise ValueError('Maximum salary cannot be less than minimum salary')
        return v

    @validator('required_skills')
    def validate_required_skills(cls, v):
        if v is not None:
            validated_skills = []
            for skill in v:
                if len(skill) > 100:
                    raise ValueError('Skill name too long')
                validated_skills.append(SkillValidation(skill=skill).skill)
            return validated_skills
        return v