from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from enum import Enum

class CompanySize(str, Enum):
    """Company size enumeration"""
    SMALL_1_10 = "1-10"
    SMALL_11_50 = "11-50"
    MEDIUM_51_200 = "51-200"
    MEDIUM_201_500 = "201-500"
    LARGE_501_1000 = "501-1000"
    LARGE_1000_PLUS = "1000+"

class Domain(str, Enum):
    """Domain enumeration"""
    IT = "IT"
    HEALTHCARE = "Healthcare"
    FINANCE = "Finance"
    EDUCATION = "Education"
    MANUFACTURING = "Manufacturing"
    RETAIL = "Retail"
    CONSULTING = "Consulting"
    MEDIA = "Media"
    REAL_ESTATE = "Real Estate"
    TRANSPORTATION = "Transportation"
    ENERGY = "Energy"
    TELECOMMUNICATIONS = "Telecommunications"
    OTHER = "Other"

class RecruiterBase(BaseModel):
    """Base recruiter schema"""
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    company_name: str
    domain: Domain
    company_size: CompanySize
    company_description: Optional[str] = None

class RecruiterCreate(RecruiterBase):
    """Schema for creating a new recruiter"""
    password: str
    password_confirm: str
    
    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class RecruiterLogin(BaseModel):
    """Schema for recruiter login"""
    email: EmailStr
    password: str

class RecruiterResponse(RecruiterBase):
    """Schema for recruiter response"""
    id: int
    role: str
    is_active: bool
    email_verified: bool
    
    class Config:
        from_attributes = True

class RecruiterUpdate(BaseModel):
    """Schema for updating recruiter profile"""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    company_name: Optional[str] = None
    domain: Optional[Domain] = None
    company_size: Optional[CompanySize] = None
    company_description: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class RecruiterProfile(BaseModel):
    """Schema for recruiter profile with job statistics"""
    id: int
    full_name: str
    email: str
    phone_number: Optional[str] = None
    company_name: str
    domain: Domain
    company_size: CompanySize
    company_description: Optional[str] = None
    role: str
    is_active: bool
    email_verified: bool
    total_jobs_posted: int
    total_applications_received: int
    active_jobs: int
    
    class Config:
        from_attributes = True 