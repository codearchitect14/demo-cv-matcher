from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime

class InteractionTypeEnum(str, Enum):
    VIEWED = "viewed"
    APPLIED = "applied"
    REJECTED = "rejected"

class InteractionLogCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    job_id: int = Field(..., gt=0)
    interaction_type: InteractionTypeEnum

class InteractionLogResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    interaction_type: InteractionTypeEnum
    timestamp: datetime
