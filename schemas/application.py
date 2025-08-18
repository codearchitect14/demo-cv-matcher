from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models.application import ApplicationStatusEnum


class ApplicationCreate(BaseModel):
    job_id: int
    candidate_id: Optional[int] = None
    status: ApplicationStatusEnum = ApplicationStatusEnum.APPLIED


class ApplicationUpdate(BaseModel):
    status: ApplicationStatusEnum


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    status: ApplicationStatusEnum
    created_at: datetime
    updated_at: datetime
    applied_at: Optional[datetime] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    
    class Config:
        from_attributes = True
