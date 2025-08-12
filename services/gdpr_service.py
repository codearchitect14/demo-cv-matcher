import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, Request
from models.candidate import Candidate
from models.audit import AuditLog, AuditActionType
from db.crud.candidate import candidate as candidate_crud
from db.crud.audit import audit as audit_crud
from schemas.audit import DataDeletionRequest, ConsentUpdateRequest
from schemas.candidate import CandidateUpdate

logger = logging.getLogger(__name__)

class GDPRService:
    """Service for GDPR compliance operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def delete_user_data(
        self,
        db: AsyncSession,
        *,
        candidate_id: int,
        admin_id: Optional[int] = None,
        reason: Optional[str] = None,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Delete all user data for GDPR compliance"""
        try:
            # Get candidate with all relationships
            candidate = await candidate_crud.get_with_experiences(db, candidate_id)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
            
            # Log the deletion before actually deleting
            deletion_details = {
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                "reason": reason,
                "deleted_data": {
                    "profile": True,
                    "experiences": len(candidate.experiences),
                    "applications": len(candidate.applications),
                    "interactions": len(candidate.interactions)
                }
            }
            
            # Create audit log
            await audit_crud.create_audit_log(
                db=db,
                user_id=candidate_id,
                admin_id=admin_id,
                action_type=AuditActionType.DATA_DELETION,
                details=json.dumps(deletion_details),
                ip_address=request.client.host if request else None,
                user_agent=request.headers.get("user-agent") if request else None
            )
            
            # Delete candidate and all related data
            await candidate_crud.delete(db, candidate_id)
            
            self.logger.info(f"GDPR data deletion completed for candidate {candidate_id}")
            
            return {
                "message": "User data deleted successfully",
                "candidate_id": candidate_id,
                "deleted_data": deletion_details["deleted_data"]
            }
            
        except Exception as e:
            self.logger.error(f"Error during GDPR data deletion: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete user data")
    
    async def update_consent(
        self,
        db: AsyncSession,
        *,
        candidate_id: int,
        consent_given: bool,
        admin_id: Optional[int] = None,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Update candidate consent status"""
        try:
            # Get candidate
            candidate = await candidate_crud.get(db, candidate_id)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
            
            # Update consent
            update_data = CandidateUpdate(consent_given=consent_given)
            updated_candidate = await candidate_crud.update(db, candidate_id, update_data)
            
            # Log consent update
            consent_details = {
                "candidate_id": candidate_id,
                "previous_consent": candidate.consent_given,
                "new_consent": consent_given
            }
            
            await audit_crud.create_audit_log(
                db=db,
                user_id=candidate_id,
                admin_id=admin_id,
                action_type=AuditActionType.CONSENT_UPDATE,
                details=json.dumps(consent_details),
                ip_address=request.client.host if request else None,
                user_agent=request.headers.get("user-agent") if request else None
            )
            
            self.logger.info(f"Consent updated for candidate {candidate_id}: {consent_given}")
            
            return {
                "message": "Consent updated successfully",
                "candidate_id": candidate_id,
                "consent_given": consent_given
            }
            
        except Exception as e:
            self.logger.error(f"Error updating consent: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update consent")
    
    async def get_user_audit_logs(
        self,
        db: AsyncSession,
        *,
        candidate_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get audit logs for a specific user"""
        try:
            logs = await audit_crud.get_user_audit_logs(
                db=db,
                user_id=candidate_id,
                skip=skip,
                limit=limit
            )
            
            return {
                "candidate_id": candidate_id,
                "audit_logs": [
                    {
                        "id": log.id,
                        "action_type": log.action_type.value,
                        "details": json.loads(log.details) if log.details else None,
                        "created_at": log.created_at.isoformat(),
                        "ip_address": log.ip_address,
                        "admin_id": log.admin_id
                    }
                    for log in logs
                ],
                "total": len(logs)
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving audit logs: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")
    
    async def export_user_data(
        self,
        db: AsyncSession,
        *,
        candidate_id: int,
        admin_id: Optional[int] = None,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Export user data for GDPR right to data portability"""
        try:
            # Get candidate with all relationships
            candidate = await candidate_crud.get_with_experiences(db, candidate_id)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
            
            # Prepare export data
            export_data = {
                "candidate": {
                    "id": candidate.id,
                    "name": candidate.name,
                    "location": candidate.location,
                    "domain": candidate.domain,
                    "expected_salary_min": candidate.expected_salary_min,
                    "expected_salary_max": candidate.expected_salary_max,
                    "summary": candidate.summary,
                    "consent_given": candidate.consent_given,
                    "created_at": candidate.created_at.isoformat(),
                    "updated_at": candidate.updated_at.isoformat()
                },
                "experiences": [
                    {
                        "id": exp.id,
                        "skill": exp.skill,
                        "years": exp.years,
                        "description": exp.description,
                        "created_at": exp.created_at.isoformat()
                    }
                    for exp in candidate.experiences
                ],
                "applications": [
                    {
                        "id": app.id,
                        "job_id": app.job_id,
                        "status": app.status,
                        "created_at": app.created_at.isoformat()
                    }
                    for app in candidate.applications
                ],
                "interactions": [
                    {
                        "id": interaction.id,
                        "job_id": interaction.job_id,
                        "interaction_type": interaction.interaction_type.value,
                        "created_at": interaction.created_at.isoformat()
                    }
                    for interaction in candidate.interactions
                ]
            }
            
            # Log data export
            export_details = {
                "candidate_id": candidate_id,
                "export_size": len(json.dumps(export_data)),
                "data_types": ["profile", "experiences", "applications", "interactions"]
            }
            
            await audit_crud.create_audit_log(
                db=db,
                user_id=candidate_id,
                admin_id=admin_id,
                action_type=AuditActionType.DATA_EXPORT,
                details=json.dumps(export_details),
                ip_address=request.client.host if request else None,
                user_agent=request.headers.get("user-agent") if request else None
            )
            
            self.logger.info(f"Data export completed for candidate {candidate_id}")
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error exporting user data: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to export user data")

# Create service instance
gdpr_service = GDPRService() 