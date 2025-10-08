"""
Integrated notification service that combines email and notification batching
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from services.enhanced_email_service import enhanced_email_service
from services.notification_batch_service import notification_batch_service, NotificationPriority
from services.notification_service import notification_service

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    EMAIL_ONLY = "email_only"
    NOTIFICATION_ONLY = "notification_only"
    BOTH = "both"

class IntegratedNotificationService:
    """Service that integrates email and notification sending with batching and caching"""
    
    def __init__(self):
        self.email_service = enhanced_email_service
        self.batch_service = notification_batch_service
        self.notification_service = notification_service
        logger.info("Integrated Notification Service initialized")
    
    async def send_sub_recruiter_welcome(
        self, 
        recruiter_email: str, 
        recruiter_name: str, 
        company_name: str,
        login_credentials: Optional[Dict] = None,
        admin_user_id: Optional[int] = None,
        admin_name: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Send sub-recruiter welcome email and admin notification
        
        Returns:
            Dict with success status for email and notification
        """
        results = {"email": False, "notification": False}
        
        try:
            # Send welcome email to sub-recruiter
            email_success = await self.email_service.send_template_email(
                template_name="sub_recruiter_welcome",
                to_email=recruiter_email,
                subject=f"Welcome to {company_name} - Your Sub-Recruiter Account is Ready!",
                recruiter_name=recruiter_name,
                company_name=company_name,
                recruiter_email=recruiter_email,
                login_credentials=login_credentials,
                priority="high"  # High priority for account creation
            )
            results["email"] = email_success
            
            # Send notification to admin
            if admin_user_id and admin_name:
                notification_success = await self.batch_service.add_notification(
                    user_id=admin_user_id,
                    user_type="recruiter",
                    title="Sub-Recruiter Created Successfully",
                    message=f"Sub-recruiter {recruiter_name} has been successfully created and welcome email sent.",
                    notification_type="success",
                    priority=NotificationPriority.NORMAL
                )
                results["notification"] = notification_success
            
            logger.info(f"Sub-recruiter welcome sent: email={email_success}, notification={results['notification']}")
            
        except Exception as e:
            logger.error(f"Error sending sub-recruiter welcome: {e}")
        
        return results
    
    async def send_job_assignment_notifications(
        self,
        recruiter_email: str,
        recruiter_name: str,
        job_title: str,
        company_name: str,
        job_id: int,
        admin_name: str,
        recruiter_user_id: int,
        admin_user_id: int
    ) -> Dict[str, bool]:
        """
        Send job assignment email and notifications
        
        Returns:
            Dict with success status for email and notifications
        """
        results = {"email": False, "recruiter_notification": False, "admin_notification": False}
        
        try:
            # Send email to assigned recruiter
            email_success = await self.email_service.send_template_email(
                template_name="job_assignment",
                to_email=recruiter_email,
                subject=f"New Job Assignment - {job_title}",
                recruiter_name=recruiter_name,
                job_title=job_title,
                company_name=company_name,
                job_id=job_id,
                admin_name=admin_name,
                priority="high"
            )
            results["email"] = email_success
            
            # Send notification to assigned recruiter
            recruiter_notification = await self.batch_service.add_notification(
                user_id=recruiter_user_id,
                user_type="recruiter",
                title="New Job Assigned",
                message=f"You've been assigned to manage '{job_title}' position.",
                notification_type="info",
                related_entity_type="job",
                related_entity_id=job_id,
                priority=NotificationPriority.HIGH
            )
            results["recruiter_notification"] = recruiter_notification
            
            # Send notification to admin
            admin_notification = await self.batch_service.add_notification(
                user_id=admin_user_id,
                user_type="recruiter",
                title="Job Successfully Assigned",
                message=f"Job '{job_title}' has been successfully assigned to {recruiter_name}.",
                notification_type="success",
                related_entity_type="job",
                related_entity_id=job_id,
                priority=NotificationPriority.NORMAL
            )
            results["admin_notification"] = admin_notification
            
            logger.info(f"Job assignment notifications sent: {results}")
            
        except Exception as e:
            logger.error(f"Error sending job assignment notifications: {e}")
        
        return results
    
    async def send_candidate_application_notification(
        self,
        recruiter_email: str,
        recruiter_name: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        application_id: int,
        recruiter_user_id: int
    ) -> Dict[str, bool]:
        """
        Send candidate application notification email and in-app notification
        
        Returns:
            Dict with success status for email and notification
        """
        results = {"email": False, "notification": False}
        
        try:
            # Send email to assigned recruiter
            email_success = await self.email_service.send_template_email(
                template_name="candidate_application_notification",
                to_email=recruiter_email,
                subject=f"New Candidate Application - {job_title}",
                recruiter_name=recruiter_name,
                candidate_name=candidate_name,
                job_title=job_title,
                company_name=company_name,
                application_id=application_id,
                priority="high"
            )
            results["email"] = email_success
            
            # Send in-app notification to recruiter
            notification_success = await self.batch_service.add_notification(
                user_id=recruiter_user_id,
                user_type="recruiter",
                title="New Candidate Application",
                message=f"Candidate {candidate_name} applied for '{job_title}' position.",
                notification_type="info",
                related_entity_type="application",
                related_entity_id=application_id,
                priority=NotificationPriority.HIGH
            )
            results["notification"] = notification_success
            
            logger.info(f"Candidate application notification sent: {results}")
            
        except Exception as e:
            logger.error(f"Error sending candidate application notification: {e}")
        
        return results
    
    async def send_candidate_status_update(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        new_status: str,
        company_name: str,
        recruiter_name: str,
        candidate_user_id: int,
        admin_user_id: Optional[int] = None,
        next_steps: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Send candidate status update email and notifications
        
        Returns:
            Dict with success status for email and notifications
        """
        results = {"email": False, "candidate_notification": False, "admin_notification": False}
        
        try:
            # Send email to candidate
            email_success = await self.email_service.send_template_email(
                template_name="candidate_status_update",
                to_email=candidate_email,
                subject=f"Application Status Update - {job_title}",
                candidate_name=candidate_name,
                job_title=job_title,
                new_status=new_status,
                company_name=company_name,
                recruiter_name=recruiter_name,
                next_steps=next_steps,
                priority="high"
            )
            results["email"] = email_success
            
            # Send notification to candidate
            candidate_notification = await self.batch_service.add_notification(
                user_id=candidate_user_id,
                user_type="candidate",
                title="Application Status Updated",
                message=f"Your application status for '{job_title}' has been updated to {new_status.replace('_', ' ').title()}.",
                notification_type="info",
                related_entity_type="application",
                priority=NotificationPriority.HIGH
            )
            results["candidate_notification"] = candidate_notification
            
            # Send notification to admin if provided
            if admin_user_id:
                admin_notification = await self.batch_service.add_notification(
                    user_id=admin_user_id,
                    user_type="recruiter",
                    title="Candidate Status Updated",
                    message=f"{recruiter_name} updated {candidate_name}'s status to {new_status.replace('_', ' ').title()} for '{job_title}'.",
                    notification_type="info",
                    priority=NotificationPriority.NORMAL
                )
                results["admin_notification"] = admin_notification
            
            logger.info(f"Candidate status update notifications sent: {results}")
            
        except Exception as e:
            logger.error(f"Error sending candidate status update: {e}")
        
        return results
    
    async def send_bulk_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Send multiple notifications in batch
        
        Args:
            notifications: List of notification data dictionaries
            
        Returns:
            Dict with counts of successful and failed notifications
        """
        results = {"success": 0, "failed": 0}
        
        try:
            tasks = []
            for notification in notifications:
                task = asyncio.create_task(
                    self.batch_service.add_notification(**notification)
                )
                tasks.append(task)
            
            # Wait for all notifications to be processed
            notification_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in notification_results:
                if result is True:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            
            logger.info(f"Bulk notifications processed: {results}")
            
        except Exception as e:
            logger.error(f"Error sending bulk notifications: {e}")
            results["failed"] = len(notifications)
        
        return results
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        return {
            "email_service": self.email_service.get_service_stats(),
            "notification_batch": self.batch_service.get_batch_stats(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        health_status = {
            "email_service": True,
            "notification_batch": True,
            "overall": True
        }
        
        try:
            # Check email service circuit breaker
            email_stats = self.email_service.get_service_stats()
            if email_stats.get("circuit_breaker_open", False):
                health_status["email_service"] = False
                health_status["overall"] = False
            
            # Check notification batch service
            batch_stats = self.batch_service.get_batch_stats()
            if batch_stats.get("total_pending_notifications", 0) > 100:  # Threshold
                health_status["notification_batch"] = False
                health_status["overall"] = False
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["overall"] = False
        
        return health_status
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all services"""
        logger.info("Shutting down integrated notification service")
        
        try:
            # Process remaining notification batches
            await self.batch_service.shutdown()
            
            # Clear email template cache
            self.email_service.template_cache.clear()
            
            logger.info("Integrated notification service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global instance
integrated_notification_service = IntegratedNotificationService()

