from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models.application import ApplicationStatusEnum


class ApplicationCreate(BaseModel):
    job_id: int
    candidate_id: int
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
    
    class Config:
        from_attributes = True
