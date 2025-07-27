from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.job import job as job_crud
from schemas.job import JobCreate, JobUpdate, JobResponse
from core.exceptions import NotFoundException, ValidationException

class JobService:
    def __init__(self):
        self.crud = job_crud

    async def create_job(self, db: AsyncSession, job_data: JobCreate) -> JobResponse:
        try:
            job = await self.crud.create_with_skills(db, job_data)
            return JobResponse.model_validate(job)
        except Exception as e:
            raise ValidationException(f"Failed to create job: {str(e)}")

    async def get_job(self, db: AsyncSession, job_id: int) -> JobResponse:
        job = await self.crud.get_with_skills(db, job_id)
        if not job:
            raise NotFoundException(f"Job with ID {job_id} not found")
        return JobResponse.model_validate(job)

    async def update_job(self, db: AsyncSession, job_id: int, update_data: JobUpdate) -> JobResponse:
        job = await self.crud.get(db, job_id)
        if not job:
            raise NotFoundException(f"Job with ID {job_id} not found")
        updated_job = await self.crud.update(db, job, update_data)
        return JobResponse.model_validate(updated_job)

    async def delete_job(self, db: AsyncSession, job_id: int) -> bool:
        job = await self.crud.delete(db, job_id)
        if not job:
            raise NotFoundException(f"Job with ID {job_id} not found")
        return True

    async def get_jobs(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[JobResponse]:
        jobs = await self.crud.get_multi(db, skip=skip, limit=limit)
        return [JobResponse.model_validate(job) for job in jobs]

    async def search_jobs(self, db: AsyncSession, filters, skip: int = 0, limit: int = 100) -> List[JobResponse]:
        # filters: a Pydantic model or dict with search params (implement as needed)
        # Example: domain, location, salary_min, salary_max, etc.
        # You may need to implement a search_jobs method in CRUDJob
        raise NotImplementedError("Implement search_jobs logic based on your filter schema")

    async def get_jobs_by_domain(self, db: AsyncSession, domain: str) -> List[JobResponse]:
        jobs = await self.crud.get_by_domain(db, domain)
        return [JobResponse.model_validate(job) for job in jobs]

    async def get_jobs_by_location(self, db: AsyncSession, location: str) -> List[JobResponse]:
        jobs = await self.crud.get_by_location(db, location)
        return [JobResponse.model_validate(job) for job in jobs]

    async def get_jobs_by_salary_range(self, db: AsyncSession, min_salary: int, max_salary: int) -> List[JobResponse]:
        jobs = await self.crud.get_by_salary_range(db, min_salary, max_salary)
        return [JobResponse.model_validate(job) for job in jobs] 