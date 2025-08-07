from pydantic import BaseModel, validator, Field
from typing import List, Optional
from datetime import datetime
from schemas.validation import (
    NameValidation, LocationValidation, DomainValidation, DescriptionValidation,
    SalaryValidation, SkillValidation, ExperienceValidation
)

class JobMandatorySkillBase(BaseModel):
    """Base schema for job mandatory skills with advanced validation"""
    skill: str = Field(..., min_length=1, max_length=100)
    min_experience: int = Field(..., ge=0, le=50)

    @validator('skill')
    def validate_skill(cls, v):
        return SkillValidation(skill=v).skill

    @validator('min_experience')
    def validate_min_experience(cls, v):
        return ExperienceValidation(years=v).years

class JobMandatorySkillCreate(JobMandatorySkillBase):
    """Schema for creating job mandatory skills"""
    pass

class JobMandatorySkillUpdate(JobMandatorySkillBase):
    """Schema for updating job mandatory skills"""
    skill: Optional[str] = Field(None, min_length=1, max_length=100)
    min_experience: Optional[int] = Field(None, ge=0, le=50)

    @validator('skill')
    def validate_skill(cls, v):
        if v is not None:
            return SkillValidation(skill=v).skill
        return v

    @validator('min_experience')
    def validate_min_experience(cls, v):
        if v is not None:
            return ExperienceValidation(years=v).years
        return v

class JobMandatorySkillResponse(JobMandatorySkillBase):
    """Schema for job mandatory skills response"""
    id: int
    job_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobBase(BaseModel):
    """Base schema for job with comprehensive validation"""
    title: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    domain: str = Field(..., min_length=1, max_length=50)
    job_description: str = Field(..., min_length=1, max_length=2000)
    total_years_required: int = Field(0, ge=0, le=50)
    salary_min: Optional[int] = Field(None, ge=0, le=1000000)
    salary_max: Optional[int] = Field(None, ge=0, le=1000000)

    @validator('title')
    def validate_title(cls, v):
        if not v:
            raise ValueError('Job title is required')
        from config.security import sanitize_input, validate_sql_injection
        v = sanitize_input(v.strip())
        if not validate_sql_injection(v):
            raise ValueError('Invalid job title format')
        return v.title()

    @validator('company')
    def validate_company(cls, v):
        if v is not None:
            from config.security import sanitize_input, validate_sql_injection
            v = sanitize_input(v.strip())
            if not validate_sql_injection(v):
                raise ValueError('Invalid company name format')
            return v.title()
        return v

    @validator('location')
    def validate_location(cls, v):
        return LocationValidation(location=v).location

    @validator('domain')
    def validate_domain(cls, v):
        return DomainValidation(domain=v).domain

    @validator('job_description')
    def validate_job_description(cls, v):
        return DescriptionValidation(description=v).description

    @validator('total_years_required')
    def validate_total_years(cls, v):
        return ExperienceValidation(years=v).years

    @validator('salary_min', 'salary_max')
    def validate_salary(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Salary cannot be negative')
            if v > 1000000:
                raise ValueError('Salary cannot exceed 1,000,000')
        return v

    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('Maximum salary must be greater than or equal to minimum salary')
        return v

class JobCreate(JobBase):
    """Schema for creating a job"""
    mandatory_skills: List[JobMandatorySkillCreate] = Field(default_factory=list)

    @validator('mandatory_skills')
    def validate_mandatory_skills(cls, v):
        if len(v) > 20:
            raise ValueError('Cannot have more than 20 mandatory skills')
        return v

class JobUpdate(BaseModel):
    """Schema for updating a job"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    domain: Optional[str] = Field(None, min_length=1, max_length=50)
    job_description: Optional[str] = Field(None, min_length=1, max_length=2000)
    total_years_required: Optional[int] = Field(None, ge=0, le=50)
    salary_min: Optional[int] = Field(None, ge=0, le=1000000)
    salary_max: Optional[int] = Field(None, ge=0, le=1000000)

    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            from config.security import sanitize_input, validate_sql_injection
            v = sanitize_input(v.strip())
            if not validate_sql_injection(v):
                raise ValueError('Invalid job title format')
            return v.title()
        return v

    @validator('company')
    def validate_company(cls, v):
        if v is not None:
            from config.security import sanitize_input, validate_sql_injection
            v = sanitize_input(v.strip())
            if not validate_sql_injection(v):
                raise ValueError('Invalid company name format')
            return v.title()
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

    @validator('job_description')
    def validate_job_description(cls, v):
        if v is not None:
            return DescriptionValidation(description=v).description
        return v

    @validator('total_years_required')
    def validate_total_years(cls, v):
        if v is not None:
            return ExperienceValidation(years=v).years
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

class JobResponse(JobBase):
    """Schema for job response"""
    id: int
    created_at: datetime
    updated_at: datetime
    mandatory_skills: List[JobMandatorySkillResponse] = []
    
    class Config:
        from_attributes = True

class JobResponseSimple(JobBase):
    """Simple schema for job response without mandatory_skills (for public endpoints)"""
    id: int
    created_at: datetime
    updated_at: datetime
    company: Optional[str] = Field(None, max_length=100)  # Make company optional
    salary_min: Optional[int] = Field(None, ge=0, le=1000000)  # Make salary fields optional
    salary_max: Optional[int] = Field(None, ge=0, le=1000000)
    
    class Config:
        from_attributes = True

class JobSearchFilter(BaseModel):
    """Schema for job search filters with validation"""
    location: Optional[str] = Field(None, max_length=100)
    domain: Optional[str] = Field(None, max_length=50)
    salary_min: Optional[int] = Field(None, ge=0, le=1000000)
    salary_max: Optional[int] = Field(None, ge=0, le=1000000)
    required_skills: Optional[List[str]] = Field(None, max_items=20)
    company: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    
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

    @validator('company')
    def validate_company(cls, v):
        if v is not None:
            from config.security import sanitize_input, validate_sql_injection
            v = sanitize_input(v.strip())
            if not validate_sql_injection(v):
                raise ValueError('Invalid company name format')
            return v.title()
        return v

    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            from config.security import sanitize_input, validate_sql_injection
            v = sanitize_input(v.strip())
            if not validate_sql_injection(v):
                raise ValueError('Invalid job title format')
            return v.title()
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
