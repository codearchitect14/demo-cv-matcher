from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum

class AuditActionType(str, enum.Enum):
    """Audit action types for GDPR compliance"""
    DATA_DELETION = "data_deletion"
    CONSENT_UPDATE = "consent_update"
    ACCESS_LOG = "access_log"
    DATA_EXPORT = "data_export"

class AuditLog(BaseModel):
    """Audit log model for GDPR compliance"""
    __tablename__ = "audit_logs"
    
    user_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    admin_id = Column(Integer, nullable=True, index=True)  # Admin who performed the action
    action_type = Column(SQLEnum(AuditActionType), nullable=False, index=True)
    details = Column(Text, nullable=True)  # JSON string with action details
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("Candidate", foreign_keys=[user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action_type'),
        Index('idx_audit_timestamp', 'created_at'),
    ) 