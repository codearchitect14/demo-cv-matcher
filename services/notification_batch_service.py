import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationPriority(Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

@dataclass
class NotificationBatch:
    """Represents a batch of notifications to be sent"""
    user_id: int
    user_type: str
    notifications: List[Dict[str, Any]]
    priority: NotificationPriority
    created_at: datetime
    expires_at: datetime

class NotificationBatchService:
    """Service for batching notifications to improve UX and performance"""
    
    def __init__(self, max_batch_size: int = 10, batch_timeout: float = 5.0, 
                 max_batch_age: float = 30.0):
        """
        Initialize notification batch service
        
        Args:
            max_batch_size: Maximum notifications per batch
            batch_timeout: Time to wait before processing batch (seconds)
            max_batch_age: Maximum age of batch before forcing processing (seconds)
        """
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        self.max_batch_age = max_batch_age
        
        # Batch storage: {user_key: NotificationBatch}
        self.pending_batches = {}
        self._lock = asyncio.Lock()
        
        # Initialize batch processor task (will be started when needed)
        self.batch_processor_task = None
        
        logger.info("Notification Batch Service initialized")
    
    def _get_user_key(self, user_id: int, user_type: str) -> str:
        """Generate unique key for user"""
        return f"{user_type}:{user_id}"
    
    async def add_notification(self, user_id: int, user_type: str, title: str, 
                              message: str, notification_type: str = "info",
                              priority: NotificationPriority = NotificationPriority.NORMAL,
                              related_entity_type: Optional[str] = None,
                              related_entity_id: Optional[int] = None) -> bool:
        """
        Add notification to batch
        
        Args:
            user_id: User ID
            user_type: User type (candidate, recruiter, admin)
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Notification priority
            related_entity_type: Related entity type
            related_entity_id: Related entity ID
            
        Returns:
            bool: True if notification added successfully
        """
        try:
            async with self._lock:
                user_key = self._get_user_key(user_id, user_type)
                
                # Create notification data
                notification_data = {
                    "title": title,
                    "message": message,
                    "notification_type": notification_type,
                    "related_entity_type": related_entity_type,
                    "related_entity_id": related_entity_id,
                    "created_at": datetime.now()
                }
                
                # Check if batch exists for this user
                if user_key in self.pending_batches:
                    batch = self.pending_batches[user_key]
                    
                    # Check if batch is full or expired
                    if (len(batch.notifications) >= self.max_batch_size or 
                        datetime.now() > batch.expires_at):
                        # Process existing batch
                        await self._process_batch(user_key, batch)
                        # Create new batch
                        batch = self._create_new_batch(user_id, user_type, priority)
                        self.pending_batches[user_key] = batch
                    
                    batch.notifications.append(notification_data)
                else:
                    # Create new batch
                    batch = self._create_new_batch(user_id, user_type, priority)
                    batch.notifications.append(notification_data)
                    self.pending_batches[user_key] = batch
                
                logger.debug(f"Added notification to batch for {user_key}")
                
                # Start batch processor if not already running
                if self.batch_processor_task is None or self.batch_processor_task.done():
                    self.batch_processor_task = asyncio.create_task(self._batch_processor())
                
                # For high priority notifications, process immediately
                if priority == NotificationPriority.HIGH:
                    await self._process_batch(user_key, batch)
                    if user_key in self.pending_batches:
                        del self.pending_batches[user_key]
                
                return True
                
        except Exception as e:
            logger.error(f"Error adding notification to batch: {e}")
            return False
    
    def _create_new_batch(self, user_id: int, user_type: str, 
                         priority: NotificationPriority) -> NotificationBatch:
        """Create new notification batch"""
        now = datetime.now()
        expires_at = now + timedelta(seconds=self.batch_timeout)
        
        return NotificationBatch(
            user_id=user_id,
            user_type=user_type,
            notifications=[],
            priority=priority,
            created_at=now,
            expires_at=expires_at
        )
    
    async def _batch_processor(self) -> None:
        """Background task to process notification batches"""
        while True:
            try:
                await asyncio.sleep(1.0)  # Check every second
                
                async with self._lock:
                    current_time = datetime.now()
                    batches_to_process = []
                    
                    # Find batches that need processing
                    for user_key, batch in self.pending_batches.items():
                        if (len(batch.notifications) >= self.max_batch_size or
                            current_time > batch.expires_at):
                            batches_to_process.append((user_key, batch))
                    
                    # Process batches
                    for user_key, batch in batches_to_process:
                        await self._process_batch(user_key, batch)
                        if user_key in self.pending_batches:
                            del self.pending_batches[user_key]
                
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(5.0)  # Wait longer on error
    
    async def _process_batch(self, user_key: str, batch: NotificationBatch) -> None:
        """Process a notification batch"""
        try:
            if not batch.notifications:
                return
            
            logger.info(f"Processing batch of {len(batch.notifications)} notifications for {user_key}")
            
            # Import here to avoid circular imports
            from services.notification_service import notification_service
            
            # Process notifications concurrently
            tasks = []
            for notification_data in batch.notifications:
                task = asyncio.create_task(
                    notification_service.create_notification(
                        user_id=batch.user_id,
                        user_type=batch.user_type,
                        title=notification_data["title"],
                        message=notification_data["message"],
                        notification_type=notification_data["notification_type"],
                        related_entity_type=notification_data["related_entity_type"],
                        related_entity_id=notification_data["related_entity_id"]
                    )
                )
                tasks.append(task)
            
            # Wait for all notifications to be created
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            success_count = sum(1 for result in results if result is True)
            error_count = len(results) - success_count
            
            logger.info(f"Batch processing complete: {success_count} successful, {error_count} failed")
            
        except Exception as e:
            logger.error(f"Error processing notification batch: {e}")
    
    async def force_process_all_batches(self) -> None:
        """Force process all pending batches (useful for shutdown)"""
        async with self._lock:
            for user_key, batch in list(self.pending_batches.items()):
                await self._process_batch(user_key, batch)
            self.pending_batches.clear()
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics"""
        total_pending = sum(len(batch.notifications) for batch in self.pending_batches.values())
        
        return {
            "pending_batches": len(self.pending_batches),
            "total_pending_notifications": total_pending,
            "max_batch_size": self.max_batch_size,
            "batch_timeout": self.batch_timeout
        }
    
    async def shutdown(self) -> None:
        """Shutdown batch service and process remaining batches"""
        logger.info("Shutting down notification batch service")
        
        # Cancel batch processor
        if self.batch_processor_task and not self.batch_processor_task.done():
            self.batch_processor_task.cancel()
            try:
                await self.batch_processor_task
            except asyncio.CancelledError:
                pass
        
        # Process remaining batches
        await self.force_process_all_batches()

# Global instance
notification_batch_service = NotificationBatchService()
