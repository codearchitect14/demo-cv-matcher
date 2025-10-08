from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import logging

from db.crud.candidate import candidate as candidate_crud
from db.crud.job import job as job_crud
from db.crud.application import application as application_crud
from schemas.candidate import CandidateCreate, CandidateUpdate, CandidateExperienceCreate, CandidateExperienceUpdate
from schemas.job import JobCreate, JobUpdate, JobMandatorySkillCreate
from schemas.application import ApplicationCreate, ApplicationUpdate
from models.candidate import Candidate
from models.job import Job

logger = logging.getLogger(__name__)

class APIService:
    """Service layer for API operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # Candidate Service Methods
    async def create_candidate(self, db: AsyncSession, candidate_data: CandidateCreate) -> Candidate:
        """Create candidate with business logic validation"""
        try:
            # Validate business rules
            if candidate_data.expected_salary_min and candidate_data.expected_salary_max:
                if candidate_data.expected_salary_min > candidate_data.expected_salary_max:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Minimum salary cannot be greater than maximum salary"
                    )
            
            candidate = await candidate_crud.create(db, obj_in=candidate_data)
            self.logger.info(f"Created candidate: {candidate.id}")
            return candidate
            
        except Exception as e:
            self.logger.error(f"Failed to create candidate: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create candidate: {str(e)}"
            )
    
    async def get_candidate(self, db: AsyncSession, candidate_id: int) -> Candidate:
        """Get candidate with validation"""
        try:
            candidate = await candidate_crud.get_with_experiences(db, id=candidate_id)
            if not candidate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Candidate not found"
                )
            return candidate
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get candidate {candidate_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve candidate: {str(e)}"
            )
    
    async def update_candidate(self, db: AsyncSession, candidate_id: int, candidate_data: CandidateUpdate, current_user: Candidate) -> Candidate:
        """Update candidate with authorization check"""
        try:
            if current_user.id != candidate_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only update own profile"
                )
            
            candidate = await candidate_crud.update(db, db_obj=current_user, obj_in=candidate_data)
            self.logger.info(f"Updated candidate: {candidate_id}")
            return candidate
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update candidate {candidate_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update candidate: {str(e)}"
            )
    
    async def add_candidate_experience(self, db: AsyncSession, candidate_id: int, experience_data: CandidateExperienceCreate, current_user: Candidate) -> Candidate:
        """Add experience with authorization check"""
        try:
            if current_user.id != candidate_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only add experience to own profile"
                )
            
            candidate = await candidate_crud.add_experience(db, candidate_id, experience_data.dict())
            self.logger.info(f"Added experience to candidate: {candidate_id}")
            return candidate
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to add experience to candidate {candidate_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add experience: {str(e)}"
            )
    
    # Job Service Methods
    async def create_job(self, db: AsyncSession, job_data: JobCreate) -> Job:
        """Create job with business logic validation"""
        try:
            # Validate business rules
            if job_data.salary_min and job_data.salary_max:
                if job_data.salary_min > job_data.salary_max:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Minimum salary cannot be greater than maximum salary"
                    )
            
            job = await job_crud.create_with_skills(db, obj_in=job_data)
            self.logger.info(f"Created job: {job.id}")
            return job
            
        except Exception as e:
            self.logger.error(f"Failed to create job: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create job: {str(e)}"
            )
    
    async def get_job(self, db: AsyncSession, job_id: int) -> Job:
        """Get job with validation"""
        try:
            job = await job_crud.get_with_mandatory_skills(db, id=job_id)
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job not found"
                )
            return job
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get job {job_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve job: {str(e)}"
            )
    
    async def list_jobs(self, db: AsyncSession, filters: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[Job]:
        """List jobs with filtering"""
        try:
            jobs = await job_crud.get_multi_with_filters(db, filters=filters, skip=skip, limit=limit)
            self.logger.info(f"Retrieved {len(jobs)} jobs with filters: {filters}")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Failed to list jobs: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve jobs: {str(e)}"
            )
    
    # Application Service Methods
    async def create_application(self, db: AsyncSession, application_data: ApplicationCreate, current_user: Candidate) -> Dict[str, Any]:
        """Create application with duplicate check"""
        try:
            # Check if already applied
            existing_application = await application_crud.get_by_candidate_and_job(
                db, candidate_id=current_user.id, job_id=application_data.job_id
            )
            if existing_application:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Already applied for this job"
                )
            
            # Create application
            application_dict = application_data.dict()
            application_dict["candidate_id"] = current_user.id
            
            application = await application_crud.create(db, obj_in=application_dict)
            
            # Log interaction
            from services.interaction_service import interaction_service
            await interaction_service.log_interaction(
                db, current_user.id, application_data.job_id, "applied"
            )
            
            self.logger.info(f"Created application: {application.id}")
            return {"application": application, "message": "Application submitted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create application: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to apply for job: {str(e)}"
            )

# Create service instance
api_service = APIService() 