from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from services.application_service import ApplicationService
from config.database import get_db
from core.exceptions import NotFoundException, ValidationException
from typing import List

router = APIRouter(prefix="/applications", tags=["applications"])
service = ApplicationService()

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(app_data: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await service.create_application(db, app_data)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await service.get_application(db, application_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(application_id: int, update_data: ApplicationUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await service.update_application(db, application_id, update_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(application_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await service.delete_application(db, application_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/candidate/{candidate_id}", response_model=List[ApplicationResponse])
async def get_applications_by_candidate(candidate_id: int, db: AsyncSession = Depends(get_db)):
    return await service.get_applications_by_candidate(db, candidate_id)

@router.get("/job/{job_id}", response_model=List[ApplicationResponse])
async def get_applications_by_job(job_id: int, db: AsyncSession = Depends(get_db)):
    return await service.get_applications_by_job(db, job_id)

@router.get("/status/{status}", response_model=List[ApplicationResponse])
async def get_applications_by_status(status: str, db: AsyncSession = Depends(get_db)):
    return await service.get_applications_by_status(db, status) 