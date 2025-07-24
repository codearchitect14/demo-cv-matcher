from pydantic import BaseModel
from datetime import datetime
from models.interaction import InteractionTypeEnum


class InteractionLogBase(BaseModel):
    job_id: int
    candidate_id: int
    interaction_type: InteractionTypeEnum


class InteractionLogCreate(InteractionLogBase):
    pass


class InteractionLogResponse(InteractionLogBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
