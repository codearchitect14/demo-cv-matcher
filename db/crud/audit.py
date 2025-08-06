from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from models.audit import AuditLog
from db.crud.base import CRUDBase

class CRUDAudit(CRUDBase[AuditLog, Dict[str, Any], Dict[str, Any]]):
    """CRUD operations for AuditLog model"""
    
    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> List[AuditLog]:
        """Get audit logs by user ID"""
        result = await db.execute(
            select(AuditLog).where(AuditLog.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_by_action_type(self, db: AsyncSession, action_type: str) -> List[AuditLog]:
        """Get audit logs by action type"""
        result = await db.execute(
            select(AuditLog).where(AuditLog.action_type == action_type)
        )
        return result.scalars().all()
    
    async def get_recent_logs(self, db: AsyncSession, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs"""
        result = await db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

# Create audit CRUD instance
audit = CRUDAudit(AuditLog) 