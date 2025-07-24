# File: schemas/candidate.py
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime


class CandidateExperienceBase(BaseModel):
    skill: str
    years: int
    description: Optional[str] = None

    @validator('years')
    def validate_years(cls, v):
        if v < 0:
            raise ValueError('Years of experience cannot be negative')
        return v


class CandidateExperienceCreate(CandidateExperienceBase):
    pass


class CandidateExperienceResponse(CandidateExperienceBase):
    id: int
    candidate_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CandidateBase(BaseModel):
    name: str
    location: str
    domain: str
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None

    @validator('expected_salary_min', 'expected_salary_max')
    def validate_salary(cls, v):
        if v is not None and v < 0:
            raise ValueError('Salary cannot be negative')
        return v

    @validator('expected_salary_max')
    def validate_salary_range(cls, v, values):
        min_salary = values.get('expected_salary_min')
        if v is not None and min_salary is not None and v < min_salary:
            raise ValueError('Maximum salary cannot be less than minimum salary')
        return v


class CandidateCreate(CandidateBase):
    experiences: Optional[List[CandidateExperienceCreate]] = []


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    domain: Optional[str] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None


class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    experiences: List[CandidateExperienceResponse] = []
    
    class Config:
        from_attributes = True