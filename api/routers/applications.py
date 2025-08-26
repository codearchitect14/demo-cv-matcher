from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db_session
from models.application import Application, ApplicationStatusEnum
from models.candidate import Candidate
from models.job import Job
from db.crud.application import application as application_crud
from api.routers.auth import get_current_user
from schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse

router = APIRouter(tags=["Applications"])

@router.get("/public", response_model=List[dict])
async def get_all_applications_public(
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by candidate name, email, job title, or company"),
    candidate_id: Optional[int] = Query(None, description="Filter by specific candidate ID"),
    job_id: Optional[int] = Query(None, description="Filter by specific job ID"),
    location: Optional[str] = Query(None, description="Filter by location"),
    experience_range: Optional[str] = Query(None, description="Filter by experience range (0-2, 3-5, 6-8, 9+)")
):
    """Get all applications with candidate and job details (public endpoint for management)"""
    try:
        # Use a single JOIN query to get all data at once, avoiding multiple queries
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                a.id, a.job_id, a.candidate_id, a.status, a.created_at, a.updated_at,
                c.name as candidate_name, c.email as candidate_email, c.location as candidate_location,
                c.domain as candidate_domain, c.expected_salary_min, c.expected_salary_max,
                j.title as job_title, j.company, j.location as job_location, j.domain as job_domain,
                j.salary_min, j.salary_max, j.total_years_required
            FROM applications a
            LEFT JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN jobs j ON a.job_id = j.id
            ORDER BY a.created_at DESC
            LIMIT :limit OFFSET :skip
        """)
        
        result = await db.execute(query, {"limit": limit, "skip": skip})
        rows = result.fetchall()
        
        response_applications = []
        for row in rows:
            app_data = {
                "id": row[0],
                "job_id": row[1],
                "candidate_id": row[2],
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            }
            
            # Add candidate data if available
            if row[6]:  # candidate_name exists
                app_data["candidate"] = {
                    "id": row[2],  # candidate_id
                    "name": row[6],
                    "email": row[7],
                    "location": row[8],
                    "domain": row[9],
                    "expected_salary_min": row[10],
                    "expected_salary_max": row[11]
                }
            
            # Add job data if available
            if row[12]:  # job_title exists
                app_data["job"] = {
                    "id": row[1],  # job_id
                    "title": row[12],
                    "company": row[13],
                    "location": row[14],
                    "domain": row[15],
                    "salary_min": row[16],
                    "salary_max": row[17],
                    "total_years_required": row[18]
                }
            
            response_applications.append(app_data)
        
        return response_applications
    except Exception as e:
        print(f"Get all applications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve applications. Please try again later."
        )

@router.put("/{application_id}/status/public")
async def update_application_status_public(
    application_id: int,
    status_update: ApplicationUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update application status (public endpoint for testing)"""
    try:
        # Use raw SQL to avoid transaction issues
        from sqlalchemy import text
        
        # First check if application exists
        check_query = text("SELECT id FROM applications WHERE id = :application_id")
        result = await db.execute(check_query, {"application_id": application_id})
        application = result.fetchone()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Update the status using raw SQL
        update_query = text("""
            UPDATE applications 
            SET status = :status, updated_at = NOW() 
            WHERE id = :application_id
            RETURNING id, job_id, candidate_id, status, created_at, updated_at
        """)
        
        result = await db.execute(update_query, {
            "application_id": application_id,
            "status": status_update.status
        })
        
        updated_application = result.fetchone()
        await db.commit()
        
        if updated_application:
            return {
                "id": updated_application[0],
                "job_id": updated_application[1],
                "candidate_id": updated_application[2],
                "status": updated_application[3],
                "created_at": updated_application[4],
                "updated_at": updated_application[5]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update application"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update application error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update application: {str(e)}"
        )

@router.post("/public", response_model=ApplicationResponse)
async def create_application_public(
    application_data: ApplicationCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create application for testing (public endpoint)"""
    try:
        print(f"DEBUG: Creating application - candidate_id: {application_data.candidate_id}, job_id: {application_data.job_id}")
        
        # Ensure candidate_id is provided for public endpoint
        if not application_data.candidate_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="candidate_id is required for public endpoint"
            )
        
        # Check if already applied
        existing_application = await application_crud.get_by_candidate_and_job(
            db, candidate_id=application_data.candidate_id, job_id=application_data.job_id
        )
        
        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already applied for this job"
            )
        
        # Create application with proper status handling
        application_data_dict = application_data.model_dump()
        # Ensure status is properly set
        if 'status' not in application_data_dict or not application_data_dict['status']:
            application_data_dict['status'] = ApplicationStatusEnum.APPLIED
        
        application = await application_crud.create(db, obj_in=application_data_dict)
        
        return application
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )

@router.get("/my-applications", response_model=List[ApplicationResponse])
async def get_my_applications(
    current_user: Candidate = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get applications for the current authenticated user"""
    try:
        # Use raw SQL to avoid enum issues
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                a.id, a.job_id, a.candidate_id, a.status, a.created_at, a.updated_at,
                j.title as job_title, j.company, j.location as job_location, j.domain as job_domain,
                j.salary_min, j.salary_max, j.total_years_required
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE a.candidate_id = :candidate_id
            ORDER BY a.created_at DESC
            LIMIT :limit OFFSET :skip
        """)
        
        result = await db.execute(query, {
            "candidate_id": current_user.id,
            "limit": limit,
            "skip": skip
        })
        rows = result.fetchall()
        
        applications = []
        for row in rows:
            app_data = {
                "id": row[0],
                "job_id": row[1],
                "candidate_id": row[2],
                "status": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "job": {
                    "id": row[1],
                    "title": row[6],
                    "company": row[7],
                    "location": row[8],
                    "domain": row[9],
                    "salary_min": row[10],
                    "salary_max": row[11],
                    "total_years_required": row[12]
                } if row[6] else None
            }
            applications.append(app_data)
        
        return applications
    except Exception as e:
        print(f"Get my applications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve your applications. Please try again later."
        )
