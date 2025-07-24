from pydantic import BaseModel, validator
from typing import Optional, List
from enum import Enum


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class JobSearchFilter(BaseModel):
    location: Optional[str] = None
    domain: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    required_skills: Optional[List[str]] = []
    
    @validator('salary_min', 'salary_max')
    def validate_salary(cls, v):
        if v is not None and v < 0:
            raise ValueError('Salary cannot be negative')
        return v


class CandidateSearchFilter(BaseModel):
    location: Optional[str] = None
    domain: Optional[str] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    skills: Optional[List[str]] = []
    min_experience: Optional[int] = None
    
    @validator('expected_salary_min', 'expected_salary_max', 'min_experience')
    def validate_positive_values(cls, v):
        if v is not None and v < 0:
            raise ValueError('Value cannot be negative')
        return v


class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    offset: int = 0
    
    @validator('limit')
    def validate_limit(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        if v < 0:
            raise ValueError('Offset cannot be negative')
        return v
