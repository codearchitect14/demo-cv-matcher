import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from config.connection_pool import global_pool

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        """Initialize notification service"""
        pass
    
    async def create_notification(self, user_id: int, user_type: str, title: str, 
                                message: str, notification_type: str = "info",
                                related_entity_type: Optional[str] = None,
                                related_entity_id: Optional[int] = None,
                                expires_at: Optional[datetime] = None) -> bool:
        """
        Create a new notification
        
        Args:
            user_id: ID of the user to notify
            user_type: Type of user ('candidate', 'recruiter', 'admin')
            title: Notification title
            message: Notification message
            notification_type: Type of notification ('success', 'info', 'warning', 'error')
            related_entity_type: Type of related entity (optional)
            related_entity_id: ID of related entity (optional)
            expires_at: Optional expiration date
            
        Returns:
            bool: True if notification created successfully
        """
        try:
            async with global_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO notifications (user_id, user_type, title, message, notification_type, 
                                             related_entity_type, related_entity_id, expires_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    user_id, user_type, title, message, notification_type,
                    related_entity_type, related_entity_id, expires_at
                )
                
                logger.info(f"Notification created for user {user_id} ({user_type})")
                return True
                
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return False
    
    async def get_user_notifications(self, user_id: int, user_type: str, 
                                   limit: int = 50, offset: int = 0,
                                   unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get notifications for a specific user
        
        Args:
            user_id: ID of the user
            user_type: Type of user
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            unread_only: If True, only return unread notifications
            
        Returns:
            List of notification dictionaries
        """
        try:
            async with global_pool.acquire() as conn:
                where_clause = "WHERE user_id = $1 AND user_type = $2"
                params = [user_id, user_type]
                
                if unread_only:
                    where_clause += " AND is_read = FALSE"
                
                # Add expiration check
                where_clause += " AND (expires_at IS NULL OR expires_at > NOW())"
                
                query = f"""
                    SELECT id, title, message, notification_type, is_read, 
                           related_entity_type, related_entity_id, created_at, read_at
                    FROM notifications
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT $3 OFFSET $4
                """
                
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                return [
                    {
                        "id": str(row["id"]),
                        "title": row["title"],
                        "message": row["message"],
                        "notification_type": row["notification_type"],
                        "is_read": row["is_read"],
                        "related_entity_type": row["related_entity_type"],
                        "related_entity_id": row["related_entity_id"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        "read_at": row["read_at"].isoformat() if row["read_at"] else None
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            return []
    
    async def mark_notification_as_read(self, notification_id: str, user_id: int) -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: ID of the notification
            user_id: ID of the user (for security)
            
        Returns:
            bool: True if notification marked as read
        """
        try:
            async with global_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE notifications 
                    SET is_read = TRUE, read_at = NOW()
                    WHERE id = $1 AND user_id = $2
                    """,
                    notification_id, user_id
                )
                
                if result == "UPDATE 1":
                    logger.info(f"Notification {notification_id} marked as read")
                    return True
                else:
                    logger.warning(f"Notification {notification_id} not found or already read")
                    return False
                    
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    async def mark_all_notifications_as_read(self, user_id: int, user_type: str) -> bool:
        """
        Mark all notifications as read for a user
        
        Args:
            user_id: ID of the user
            user_type: Type of user
            
        Returns:
            bool: True if notifications marked as read
        """
        try:
            async with global_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE notifications 
                    SET is_read = TRUE, read_at = NOW()
                    WHERE user_id = $1 AND user_type = $2 AND is_read = FALSE
                    """,
                    user_id, user_type
                )
                
                logger.info(f"All notifications marked as read for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return False
    
    async def get_unread_count(self, user_id: int, user_type: str) -> int:
        """
        Get count of unread notifications for a user
        
        Args:
            user_id: ID of the user
            user_type: Type of user
            
        Returns:
            int: Number of unread notifications
        """
        try:
            async with global_pool.acquire() as conn:
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*) 
                    FROM notifications 
                    WHERE user_id = $1 AND user_type = $2 AND is_read = FALSE
                    AND (expires_at IS NULL OR expires_at > NOW())
                    """,
                    user_id, user_type
                )
                
                return count or 0
                
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    async def cleanup_expired_notifications(self) -> int:
        """
        Clean up expired notifications
        
        Returns:
            int: Number of notifications cleaned up
        """
        try:
            async with global_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM notifications WHERE expires_at < NOW()"
                )
                
                # Extract number from result string like "DELETE 5"
                deleted_count = int(result.split()[-1]) if result.startswith("DELETE") else 0
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired notifications")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up expired notifications: {str(e)}")
            return 0

# Create global instance
notification_service = NotificationService()
