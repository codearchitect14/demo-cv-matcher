"""
Recruiter notification endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import logging

from config.database import get_db_session
from middleware.recruiter_auth import get_current_recruiter as get_recruiter_context, RecruiterContext
from services.notification_service import notification_service
from sqlalchemy import text

router = APIRouter(tags=["Recruiter Notifications"])
logger = logging.getLogger(__name__)

class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    notification_type: str
    related_entity_id: Optional[int] = None
    related_entity_type: Optional[str] = None

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    created_at: str
    read_at: Optional[str] = None

@router.post("/create")
async def create_notification(
    request: CreateNotificationRequest,
    recruiter_context: RecruiterContext = Depends(get_recruiter_context),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new notification for the current recruiter"""
    try:
        success = await notification_service.create_notification(
            user_id=recruiter_context.recruiter_id,
            user_type="recruiter",
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            related_entity_type=request.related_entity_type,
            related_entity_id=request.related_entity_id
        )
        
        if success:
            return {"message": "Notification created successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notification"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating recruiter notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )

@router.get("/my-notifications", response_model=List[NotificationResponse])
async def get_my_notifications(
    recruiter_context: RecruiterContext = Depends(get_recruiter_context),
    db: AsyncSession = Depends(get_db_session)
):
    """Get notifications for the current recruiter"""
    try:
        async with db.begin():
            # Get notifications for the current recruiter
            result = await db.execute(text("""
                SELECT id, title, message, notification_type, is_read, 
                       related_entity_type, related_entity_id, created_at, read_at
                FROM notifications 
                WHERE user_id = :user_id AND user_type = 'recruiter'
                ORDER BY created_at DESC
                LIMIT 50
            """), {"user_id": recruiter_context.recruiter_id})
            
            notifications = []
            for row in result.fetchall():
                notifications.append(NotificationResponse(
                    id=str(row[0]),
                    title=row[1],
                    message=row[2],
                    notification_type=row[3],
                    is_read=row[4],
                    related_entity_type=row[5],
                    related_entity_id=row[6],
                    created_at=row[7].isoformat() if row[7] else "",
                    read_at=row[8].isoformat() if row[8] else None
                ))
            
            return notifications
            
    except Exception as e:
        logger.error(f"Error fetching recruiter notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications"
        )

@router.put("/{notification_id}/mark-read")
async def mark_notification_as_read(
    notification_id: str,
    recruiter_context: RecruiterContext = Depends(get_recruiter_context),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark a specific notification as read"""
    try:
        async with db.begin():
            # Update notification as read
            result = await db.execute(text("""
                UPDATE notifications 
                SET is_read = true, read_at = NOW()
                WHERE id = :notification_id AND user_id = :user_id AND user_type = 'recruiter'
                RETURNING id
            """), {
                "notification_id": notification_id,
                "user_id": recruiter_context.recruiter_id
            })
            
            if result.fetchone():
                return {"message": "Notification marked as read"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking recruiter notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

@router.put("/mark-all-read")
async def mark_all_notifications_as_read(
    recruiter_context: RecruiterContext = Depends(get_recruiter_context),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark all notifications as read for the current recruiter"""
    try:
        async with db.begin():
            # Update all notifications as read
            result = await db.execute(text("""
                UPDATE notifications 
                SET is_read = true, read_at = NOW()
                WHERE user_id = :user_id AND user_type = 'recruiter' AND is_read = false
                RETURNING COUNT(*)
            """), {"user_id": recruiter_context.recruiter_id})
            
            count = result.fetchone()[0] if result.fetchone() else 0
            
            return {
                "message": f"Marked {count} notifications as read",
                "count": count
            }
            
    except Exception as e:
        logger.error(f"Error marking all recruiter notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )

@router.get("/unread-count")
async def get_unread_count(
    recruiter_context: RecruiterContext = Depends(get_recruiter_context),
    db: AsyncSession = Depends(get_db_session)
):
    """Get count of unread notifications for the current recruiter"""
    try:
        async with db.begin():
            # Count unread notifications
            result = await db.execute(text("""
                SELECT COUNT(*) 
                FROM notifications 
                WHERE user_id = :user_id AND user_type = 'recruiter' AND is_read = false
            """), {"user_id": recruiter_context.recruiter_id})
            
            count = result.fetchone()[0]
            
            return {
                "unread_count": count
            }
            
    except Exception as e:
        logger.error(f"Error getting recruiter unread count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )
