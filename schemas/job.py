from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime


class JobMandatorySkillBase(BaseModel):
    skill: str
    min_experience: int

    @validator('min_experience')
    def validate_min_experience(cls, v):
        if v < 0:
            raise ValueError('Minimum experience cannot be negative')
        return v


class JobMandatorySkillCreate(JobMandatorySkillBase):
    pass


class JobMandatorySkillResponse(JobMandatorySkillBase):
    id: int
    job_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobBase(BaseModel):
    title: str
    location: str
    domain: str
    job_description: str
    total_years_required: int = 0
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None

    @validator('total_years_required')
    def validate_total_years(cls, v):
        if v < 0:
            raise ValueError('Total years required cannot be negative')
        return v

    @validator('salary_min', 'salary_max')
    def validate_salary(cls, v):
        if v is not None and v < 0:
            raise ValueError('Salary cannot be negative')
        return v

    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        min_salary = values.get('salary_min')
        if v is not None and min_salary is not None and v < min_salary:
            raise ValueError('Maximum salary cannot be less than minimum salary')
        return v


class JobCreate(JobBase):
    mandatory_skills: Optional[List[JobMandatorySkillCreate]] = []


class JobUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    domain: Optional[str] = None
    job_description: Optional[str] = None
    total_years_required: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None


class JobResponse(JobBase):
    id: int
    created_at: datetime
    mandatory_skills: List[JobMandatorySkillResponse] = []
    
    class Config:
        from_attributes = True
