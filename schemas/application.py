from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models.application import ApplicationStatusEnum


class ApplicationBase(BaseModel):
    job_id: int
    status: ApplicationStatusEnum = ApplicationStatusEnum.APPLIED


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    status: ApplicationStatusEnum


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    recruiter_id: Optional[int] = None
    status: ApplicationStatusEnum
    created_at: datetime
    updated_at: datetime
    job: Optional[dict] = None  # Include job details
    
    class Config:
        from_attributes = True
