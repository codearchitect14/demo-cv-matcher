from pydantic import BaseModel, validator
from enum import Enum
from typing import Optional, List, Dict, Any



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

class SearchFilter(BaseModel):
    """Base search filter"""
    location: Optional[str] = None
    domain: Optional[str] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    skills: Optional[List[str]] = None
    min_experience: Optional[int] = None

class JobRecommendation(BaseModel):
    """Job recommendation from semantic search with filtering and ML ranking"""
    job_id: int
    title: str
    company: str
    location: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    domain: Optional[str]
    similarity_score: float
    combined_score: Optional[float] = None
    filter_score: Optional[float] = None
    ml_score: Optional[float] = None
    is_valid: Optional[bool] = True
    validation_reasons: Optional[List[str]] = []
    explanation: str

class CandidateRecommendation(BaseModel):
    """Candidate recommendation from semantic search with filtering and ML ranking"""
    candidate_id: int
    name: str
    location: str
    domain: Optional[str]
    expected_salary_min: Optional[int]
    expected_salary_max: Optional[int]
    similarity_score: float
    combined_score: Optional[float] = None
    filter_score: Optional[float] = None
    ml_score: Optional[float] = None
    is_valid: Optional[bool] = True
    validation_reasons: Optional[List[str]] = []
    explanation: str

class SearchResponse(BaseModel):
    """Generic search response"""
    results: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
