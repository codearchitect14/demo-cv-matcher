from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel
import logging

from api.routers.auth import get_current_user
from models.candidate import Candidate
from services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Notifications"])

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    created_at: str
    read_at: Optional[str]

class MarkAsReadRequest(BaseModel):
    notification_id: str

class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    notification_type: str
    related_entity_id: Optional[int] = None
    related_entity_type: Optional[str] = None

@router.post("/create")
async def create_notification(
    request: CreateNotificationRequest,
    current_user: Candidate = Depends(get_current_user)
):
    """Create a new notification for the current user"""
    try:
        notification_id = await notification_service.create_notification(
            user_id=current_user.id,
            user_type="candidate",
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            related_entity_id=request.related_entity_id,
            related_entity_type=request.related_entity_type
        )
        
        return {"message": "Notification created successfully", "notification_id": notification_id}
        
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )

@router.get("/my-notifications", response_model=List[NotificationResponse])
async def get_my_notifications(current_user: Candidate = Depends(get_current_user)):
    """Get all notifications for the current user"""
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            user_type="candidate",
            limit=100,
            offset=0,
            unread_only=False
        )
        
        return notifications
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications"
        )

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: Candidate = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False)
):
    """Get notifications for the current user"""
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            user_type="candidate",
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
        
        return notifications
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications"
        )

@router.get("/unread-count")
async def get_unread_count(current_user: Candidate = Depends(get_current_user)):
    """Get count of unread notifications for the current user"""
    try:
        count = await notification_service.get_unread_count(
            user_id=current_user.id,
            user_type="candidate"
        )
        
        return {"unread_count": count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )

@router.put("/{notification_id}/mark-read")
async def mark_single_notification_as_read(
    notification_id: str,
    current_user: Candidate = Depends(get_current_user)
):
    """Mark a specific notification as read by ID"""
    try:
        success = await notification_service.mark_notification_as_read(
            notification_id=notification_id,
            user_id=current_user.id
        )
        
        if success:
            return {"message": "Notification marked as read"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or already read"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

@router.put("/mark-as-read")
async def mark_notification_as_read(
    request: MarkAsReadRequest,
    current_user: Candidate = Depends(get_current_user)
):
    """Mark a specific notification as read"""
    try:
        success = await notification_service.mark_notification_as_read(
            notification_id=request.notification_id,
            user_id=current_user.id
        )
        
        if success:
            return {"message": "Notification marked as read"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or already read"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

@router.put("/mark-all-as-read")
async def mark_all_notifications_as_read(current_user: Candidate = Depends(get_current_user)):
    """Mark all notifications as read for the current user"""
    try:
        success = await notification_service.mark_all_notifications_as_read(
            user_id=current_user.id,
            user_type="candidate"
        )
        
        if success:
            return {"message": "All notifications marked as read"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to mark notifications as read"
            )
            
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )
