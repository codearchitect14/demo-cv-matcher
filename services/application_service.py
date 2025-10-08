from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.application import application as application_crud
from schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from core.exceptions import NotFoundException, ValidationException

class ApplicationService:
    def __init__(self):
        self.crud = application_crud

    async def create_application(self, db: AsyncSession, app_data: ApplicationCreate) -> ApplicationResponse:
        try:
            # Prevent duplicate applications
            existing = await self.crud.get_existing(db, app_data.job_id, app_data.candidate_id)
            if existing:
                raise ValidationException("Application already exists for this job and candidate")
            application = await self.crud.create(db, app_data)
            return ApplicationResponse.model_validate(application)
        except Exception as e:
            raise ValidationException(f"Failed to create application: {str(e)}")

    async def get_application(self, db: AsyncSession, application_id: int) -> ApplicationResponse:
        application = await self.crud.get(db, application_id)
        if not application:
            raise NotFoundException(f"Application with ID {application_id} not found")
        return ApplicationResponse.model_validate(application)

    async def update_application(self, db: AsyncSession, application_id: int, update_data: ApplicationUpdate) -> ApplicationResponse:
        application = await self.crud.get(db, application_id)
        if not application:
            raise NotFoundException(f"Application with ID {application_id} not found")
        updated_application = await self.crud.update(db, application, update_data)
        return ApplicationResponse.model_validate(updated_application)

    async def delete_application(self, db: AsyncSession, application_id: int) -> bool:
        application = await self.crud.delete(db, application_id)
        if not application:
            raise NotFoundException(f"Application with ID {application_id} not found")
        return True

    async def get_applications_by_candidate(self, db: AsyncSession, candidate_id: int) -> List[ApplicationResponse]:
        applications = await self.crud.get_by_candidate(db, candidate_id)
        return [ApplicationResponse.model_validate(app) for app in applications]

    async def get_applications_by_job(self, db: AsyncSession, job_id: int) -> List[ApplicationResponse]:
        applications = await self.crud.get_by_job(db, job_id)
        return [ApplicationResponse.model_validate(app) for app in applications]

    async def get_applications_by_status(self, db: AsyncSession, status) -> List[ApplicationResponse]:
        applications = await self.crud.get_by_status(db, status)
        return [ApplicationResponse.model_validate(app) for app in applications] 