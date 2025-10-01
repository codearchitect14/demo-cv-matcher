from pydantic import BaseModel, validator, Field, EmailStr
from typing import Optional, List
import re
from config.security import SecurityConfig, sanitize_input, validate_sql_injection

class BaseValidationModel(BaseModel):
    """Base model with common validation methods"""
    
    class Config:
        # Allow extra fields to be ignored
        extra = "forbid"
        # Use enum values
        use_enum_values = True
        # Validate assignment
        validate_assignment = True

class EmailValidation(BaseModel):
    """Email validation with sanitization"""
    email: EmailStr = Field(..., max_length=SecurityConfig.MAX_EMAIL_LENGTH)
    
    @validator('email')
    def validate_email(cls, v):
        if not v:
            raise ValueError('Email is required')
        
        # Sanitize email
        v = sanitize_input(v.lower().strip())
        
        # Check for SQL injection
        if not validate_sql_injection(v):
            raise ValueError('Invalid email format')
        
        # Validate email format with regex
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(v):
            raise ValueError('Invalid email format')
        
        return v

class PasswordValidation(BaseModel):
    """Password validation with strength requirements"""
    password: str = Field(..., min_length=SecurityConfig.PASSWORD_MIN_LENGTH, 
                         max_length=SecurityConfig.PASSWORD_MAX_LENGTH)
    
    @validator('password')
    def validate_password(cls, v):
        if not v:
            raise ValueError('Password is required')
        
        # Check for SQL injection
        if not validate_sql_injection(v):
            raise ValueError('Invalid password format')
        
        # Use improved password validation
        from config.security import validate_password_with_feedback
        is_valid, message = validate_password_with_feedback(v)
        if not is_valid:
            raise ValueError(message)
        
        return v

class NameValidation(BaseModel):
    """Name validation with sanitization"""
    name: str = Field(..., min_length=1, max_length=SecurityConfig.MAX_NAME_LENGTH)
    
    @validator('name')
    def validate_name(cls, v):
        if not v:
            raise ValueError('Name is required')
        
        # Sanitize name
        v = sanitize_input(v.strip())
        
        # Check for SQL injection
        if not validate_sql_injection(v):
            raise ValueError('Invalid name format')
        
        # Validate name format (letters, spaces, hyphens, apostrophes only)
        name_pattern = re.compile(r'^[a-zA-Z\s\'-]+$')
        if not name_pattern.match(v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        
        # Check length
        if len(v) > SecurityConfig.MAX_NAME_LENGTH:
            raise ValueError(f'Name must be no more than {SecurityConfig.MAX_NAME_LENGTH} characters')
        
        return v.title()

class LocationValidation(BaseModel):
    """Location validation with sanitization"""
    location: str = Field(..., min_length=1, max_length=SecurityConfig.MAX_NAME_LENGTH)
    
    @validator('location')
    def validate_location(cls, v):
        if not v:
            raise ValueError('Location is required')
        
        # Sanitize location
        v = sanitize_input(v.strip())
        
        # Check for SQL injection
        if not validate_sql_injection(v):
            raise ValueError('Invalid location format')
        
        # Validate location format (letters, numbers, spaces, commas, hyphens, periods)
        location_pattern = re.compile(r'^[a-zA-Z0-9\s,\-\.]+$')
        if not location_pattern.match(v):
            raise ValueError('Location can only contain letters, numbers, spaces, commas, hyphens, and periods')
        
        return v.title()

class DomainValidation(BaseModel):
    """Domain validation with sanitization"""
    domain: str = Field(..., min_length=1, max_length=50)
    
    @validator('domain')
    def validate_domain(cls, v):
        if not v:
            raise ValueError('Domain is required')
        
        # Sanitize domain
        v = sanitize_input(v.strip())
        
        # Check for SQL injection
        if not validate_sql_injection(v):
            raise ValueError('Invalid domain format')
        
        # Allow any reasonable domain name
        if len(v) > 50:
            raise ValueError('Domain must be 50 characters or less')
        
        return v

class DescriptionValidation(BaseModel):
    """Description validation with sanitization"""
    description: str = Field(..., min_length=1, max_length=SecurityConfig.MAX_DESCRIPTION_LENGTH)
    
    @validator('description')
    def validate_description(cls, v):
        if not v:
            raise ValueError('Description is required')
        
        # Sanitize description
        v = sanitize_input(v.strip())
        
        # Temporarily disable strict SQL injection check for development
        # if not validate_sql_injection(v):
        #     raise ValueError('Invalid description format')
        
        # Check length
        if len(v) > SecurityConfig.MAX_DESCRIPTION_LENGTH:
            raise ValueError(f'Description must be no more than {SecurityConfig.MAX_DESCRIPTION_LENGTH} characters')
        
        return v

class SalaryValidation(BaseModel):
    """Salary validation"""
    salary_min: Optional[int] = Field(None, ge=0, le=1000000)
    salary_max: Optional[int] = Field(None, ge=0, le=1000000)
    
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

class SkillValidation(BaseModel):
    """Skill validation with sanitization"""
    skill: str = Field(..., min_length=1, max_length=100)
    
    @validator('skill')
    def validate_skill(cls, v):
        if not v:
            raise ValueError('Skill is required')
        
        # Sanitize skill
        v = sanitize_input(v.strip())
        
        # Temporarily disable strict SQL injection check for development
        # if not validate_sql_injection(v):
        #     raise ValueError('Invalid skill format')
        
        # Allow any reasonable skill name
        if len(v) > 100:
            raise ValueError('Skill must be 100 characters or less')
        
        return v.title()

class ExperienceValidation(BaseModel):
    """Experience years validation"""
    years: int = Field(..., ge=0, le=50)
    
    @validator('years')
    def validate_years(cls, v):
        if v < 0:
            raise ValueError('Years of experience cannot be negative')
        if v > 50:
            raise ValueError('Years of experience cannot exceed 50')
        return v

class SearchQueryValidation(BaseModel):
    """Search query validation with sanitization"""
    query: str = Field(..., min_length=1, max_length=200)
    
    @validator('query')
    def validate_query(cls, v):
        if not v:
            raise ValueError('Search query is required')
        
        # Sanitize query
        v = sanitize_input(v.strip())
        
        # Check for SQL injection
        if not validate_sql_injection(v):
            raise ValueError('Invalid search query format')
        
        # Check length
        if len(v) > 200:
            raise ValueError('Search query must be no more than 200 characters')
        
        return v

class PaginationValidation(BaseModel):
    """Pagination parameters validation"""
    skip: int = Field(0, ge=0, le=10000)
    limit: int = Field(100, ge=1, le=1000)
    
    @validator('skip')
    def validate_skip(cls, v):
        if v < 0:
            raise ValueError('Skip value cannot be negative')
        if v > 10000:
            raise ValueError('Skip value cannot exceed 10,000')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1:
            raise ValueError('Limit must be at least 1')
        if v > 1000:
            raise ValueError('Limit cannot exceed 1,000')
        return v

class UserRegistrationValidation(BaseValidationModel):
    """Comprehensive user registration validation"""
    name: str = Field(..., min_length=1, max_length=SecurityConfig.MAX_NAME_LENGTH)
    email: EmailStr = Field(..., max_length=SecurityConfig.MAX_EMAIL_LENGTH)
    password: str = Field(..., min_length=SecurityConfig.PASSWORD_MIN_LENGTH, 
                         max_length=SecurityConfig.PASSWORD_MAX_LENGTH)
    location: str = Field(..., min_length=1, max_length=SecurityConfig.MAX_NAME_LENGTH)
    domain: str = Field(..., min_length=1, max_length=50)
    expected_salary_min: Optional[int] = Field(None, ge=0, le=1000000)
    expected_salary_max: Optional[int] = Field(None, ge=0, le=1000000)
    summary: str = Field(..., min_length=1, max_length=SecurityConfig.MAX_DESCRIPTION_LENGTH)
    skills: Optional[List[dict]] = Field(default_factory=list, description="List of skills with years of experience")
    total_experience_years: Optional[float] = Field(None, ge=0, le=50, description="Total years of professional experience")
    
    @validator('name')
    def validate_name(cls, v):
        return NameValidation(name=v).name
    
    @validator('email')
    def validate_email(cls, v):
        return EmailValidation(email=v).email
    
    @validator('password')
    def validate_password(cls, v):
        return PasswordValidation(password=v).password
    
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
    
    @validator('skills')
    def validate_skills(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Skills must be a list')
            for skill in v:
                if not isinstance(skill, dict):
                    raise ValueError('Each skill must be a dictionary')
                if 'name' not in skill or 'years' not in skill:
                    raise ValueError('Each skill must have "name" and "years" fields')
                if not isinstance(skill['years'], (int, float)) or skill['years'] < 0:
                    raise ValueError('Skill years must be a positive number')
        return v
    
    @validator('total_experience_years')
    def validate_total_experience(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError('Total experience years must be a number')
            if v < 0:
                raise ValueError('Total experience years cannot be negative')
            if v > 50:
                raise ValueError('Total experience years cannot exceed 50')
        return v

class JobCreationValidation(BaseValidationModel):
    """Comprehensive job creation validation"""
    title: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    domain: str = Field(..., min_length=1, max_length=50)
    job_description: str = Field(..., min_length=1, max_length=SecurityConfig.MAX_DESCRIPTION_LENGTH)
    total_years_required: int = Field(0, ge=0, le=50)
    salary_min: Optional[int] = Field(None, ge=0, le=1000000)
    salary_max: Optional[int] = Field(None, ge=0, le=1000000)
    
    @validator('title')
    def validate_title(cls, v):
        if not v:
            raise ValueError('Job title is required')
        v = sanitize_input(v.strip())
        if not validate_sql_injection(v):
            raise ValueError('Invalid job title format')
        return v.title()
    
    @validator('company')
    def validate_company(cls, v):
        if v is not None:
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
    def validate_years(cls, v):
        return ExperienceValidation(years=v).years
    
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