from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.audit import AuditActionType

class AuditLogCreate(BaseModel):
    """Schema for creating audit log entries"""
    user_id: int = Field(..., description="ID of the user affected")
    admin_id: Optional[int] = Field(None, description="ID of admin performing action")
    action_type: AuditActionType = Field(..., description="Type of audit action")
    details: Optional[str] = Field(None, description="JSON string with action details")
    ip_address: Optional[str] = Field(None, description="IP address of the request")
    user_agent: Optional[str] = Field(None, description="User agent string")

class AuditLogResponse(BaseModel):
    """Schema for audit log responses"""
    id: int
    user_id: int
    admin_id: Optional[int]
    action_type: AuditActionType
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class DataDeletionRequest(BaseModel):
    """Schema for data deletion requests"""
    candidate_id: int = Field(..., description="ID of candidate to delete")
    reason: Optional[str] = Field(None, description="Reason for deletion")
    admin_id: Optional[int] = Field(None, description="ID of admin performing deletion")

class ConsentUpdateRequest(BaseModel):
    """Schema for consent updates"""
    candidate_id: int = Field(..., description="ID of candidate")
    consent_given: bool = Field(..., description="Whether consent is given")
    admin_id: Optional[int] = Field(None, description="ID of admin updating consent") 