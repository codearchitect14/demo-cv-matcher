from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class CompanyBase(BaseModel):
    """Base schema for company"""
    name: str = Field(..., min_length=2, max_length=255, description="Company name")
    domain: str = Field(..., min_length=2, max_length=100, description="Company domain/industry")
    description: Optional[str] = Field(None, max_length=1000, description="Company description")
    max_recruiters: int = Field(10, ge=1, le=1000, description="Maximum recruiters allowed")
    max_jobs: int = Field(100, ge=1, le=10000, description="Maximum active jobs allowed")
    contact_email: Optional[str] = Field(None, description="Company contact email")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Company contact phone")
    address: Optional[str] = Field(None, max_length=500, description="Company address")
    subscription_plan: str = Field("basic", description="Subscription plan")
    status: str = Field("ACTIVE", description="Company status: PENDING, ACTIVE, REJECTED, SUSPENDED")

    @validator('subscription_plan')
    def validate_subscription_plan(cls, v):
        allowed_plans = ['basic', 'premium', 'enterprise']
        if v not in allowed_plans:
            raise ValueError(f'Subscription plan must be one of: {allowed_plans}')
        return v

    @validator('contact_email')
    def validate_contact_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class CompanyCreate(CompanyBase):
    """Schema for creating a company"""
    pass

class CompanyUpdate(BaseModel):
    """Schema for updating a company"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    domain: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    max_recruiters: Optional[int] = Field(None, ge=1, le=1000)
    max_jobs: Optional[int] = Field(None, ge=1, le=10000)
    contact_email: Optional[str] = Field(None)
    contact_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = Field(None)
    status: Optional[str] = Field(None, description="PENDING, ACTIVE, REJECTED, SUSPENDED")
    subscription_plan: Optional[str] = Field(None)

    @validator('subscription_plan')
    def validate_subscription_plan(cls, v):
        if v is not None:
            allowed_plans = ['basic', 'premium', 'enterprise']
            if v not in allowed_plans:
                raise ValueError(f'Subscription plan must be one of: {allowed_plans}')
        return v

    @validator('contact_email')
    def validate_contact_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class CompanyResponse(CompanyBase):
    """Schema for company response"""
    id: int
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CompanyStats(BaseModel):
    """Schema for company statistics"""
    total_recruiters: int
    active_recruiters: int
    total_jobs: int
    active_jobs: int
    total_applications: int
    pending_applications: int



