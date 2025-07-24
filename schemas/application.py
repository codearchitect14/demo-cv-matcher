from pydantic import BaseModel
from datetime import datetime
from models.application import ApplicationStatusEnum


class ApplicationBase(BaseModel):
    job_id: int
    candidate_id: int
    status: ApplicationStatusEnum = ApplicationStatusEnum.APPLIED


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    status: ApplicationStatusEnum


class ApplicationResponse(ApplicationBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
