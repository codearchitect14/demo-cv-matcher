"""
Candidate contact endpoints for Company Admin functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel, EmailStr
import logging

from config.database import get_db_session
from middleware.recruiter_auth import get_current_recruiter as get_recruiter_context, RecruiterContext
from services.email_service import email_service
from services.notification_service import notification_service
from sqlalchemy import text

router = APIRouter(tags=["Candidate Contact"])
logger = logging.getLogger(__name__)

class CandidateContactRequest(BaseModel):
    candidate_email: EmailStr
    candidate_name: str
    message: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None

@router.post("/send-message")
async def send_candidate_contact_message(
    contact_request: CandidateContactRequest,
    db: AsyncSession = Depends(get_db_session),
    recruiter_context: RecruiterContext = Depends(get_recruiter_context)
):
    """Send a contact message from Company Admin to a candidate"""
    try:
        # Only admins can contact candidates
        if not recruiter_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required to contact candidates"
            )
        
        # Get company name from recruiter context or request
        company_name = contact_request.company_name
        if not company_name:
            # Get company name from database
            company_query = await db.execute(text("""
                SELECT c.name FROM companies c 
                JOIN recruiters r ON c.id = r.company_id 
                WHERE r.id = :recruiter_id
            """), {"recruiter_id": recruiter_context.recruiter_id})
            company_result = company_query.fetchone()
            if company_result:
                company_name = company_result[0]
            else:
                company_name = "Your Company"  # Default fallback
        
        # Send email to candidate
        try:
            await email_service.send_candidate_contact_email(
                candidate_email=contact_request.candidate_email,
                candidate_name=contact_request.candidate_name,
                admin_name=recruiter_context.full_name,
                company_name=company_name,
                message=contact_request.message,
                job_title=contact_request.job_title
            )
            logger.info(f"Contact email sent to candidate: {contact_request.candidate_email}")
        except Exception as email_error:
            logger.error(f"Failed to send contact email: {email_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email to candidate"
            )
        
        # Create notification for admin (confirmation)
        try:
            await notification_service.create_notification(
                user_id=recruiter_context.recruiter_id,
                user_type="recruiter",
                title="Message Sent to Candidate",
                message=f"Your message has been successfully sent to {contact_request.candidate_name} ({contact_request.candidate_email}).",
                notification_type="success",
                related_entity_type="candidate_contact",
                related_entity_id=None  # No specific entity ID for contact messages
            )
            logger.info(f"Admin confirmation notification created for candidate contact")
        except Exception as notification_error:
            logger.error(f"Failed to create admin confirmation notification: {notification_error}")
        
        return {
            "message": "Contact message sent successfully",
            "candidate_email": contact_request.candidate_email,
            "candidate_name": contact_request.candidate_name,
            "sent_by": recruiter_context.full_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending candidate contact message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send contact message. Please try again later."
        )

@router.get("/candidate-info/{candidate_id}")
async def get_candidate_info_for_contact(
    candidate_id: int,
    db: AsyncSession = Depends(get_db_session),
    recruiter_context: RecruiterContext = Depends(get_recruiter_context)
):
    """Get candidate information for contact purposes"""
    try:
        # Only admins can view candidate info for contact
        if not recruiter_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required to view candidate information"
            )
        
        # Get candidate details
        candidate_query = await db.execute(text("""
            SELECT id, name, email, location, domain, total_experience_years
            FROM candidates 
            WHERE id = :candidate_id
        """), {"candidate_id": candidate_id})
        
        candidate_result = candidate_query.fetchone()
        if not candidate_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        return {
            "id": candidate_result[0],
            "name": candidate_result[1],
            "email": candidate_result[2],
            "location": candidate_result[3],
            "domain": candidate_result[4],
            "total_experience_years": candidate_result[5]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get candidate information"
        )
