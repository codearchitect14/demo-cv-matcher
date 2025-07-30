from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from models.audit import AuditLog, AuditActionType
from db.crud.base import CRUDBase

class CRUDAuditLog(CRUDBase[AuditLog, AuditLog, AuditLog]):
    async def create_audit_log(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        admin_id: Optional[int] = None,
        action_type: AuditActionType,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry"""
        audit_log = AuditLog(
            user_id=user_id,
            admin_id=admin_id,
            action_type=action_type,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        return audit_log
    
    async def get_user_audit_logs(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific user"""
        query = select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc())
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def get_audit_logs_by_action(
        self,
        db: AsyncSession,
        *,
        action_type: AuditActionType,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs by action type"""
        query = select(AuditLog).where(AuditLog.action_type == action_type).order_by(AuditLog.created_at.desc())
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

audit_log = CRUDAuditLog(AuditLog) 