from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db_session
from models.candidate import Candidate
from api.routers.auth import get_current_user
from db.crud.job import job as job_crud
from db.crud.candidate import candidate as candidate_crud
from db.crud.application import application as application_crud

router = APIRouter(tags=["Analytics"])

class JobAnalytics(BaseModel):
    job_id: int
    title: str
    applications_count: int
    views_count: int
    days_posted: int
    status: str

class CandidateAnalytics(BaseModel):
    candidate_id: int
    name: str
    applications_count: int
    views_received: int
    last_activity: str
    visibility_score: float

class SkillGapAnalysis(BaseModel):
    skill: str
    demand_count: int
    supply_count: int
    gap: int
    avg_salary_demand: float
    avg_salary_supply: float

@router.get("/jobs-without-applicants")
async def get_jobs_without_applicants(
    db: AsyncSession = Depends(get_db_session),
    days_threshold: int = Query(7, ge=1, description="Days threshold for no applicants"),
    limit: int = Query(20, ge=1, le=100)
):
    """Get jobs with no applicants"""
    try:
        jobs = await job_crud.get_jobs_without_applicants(
            db, days_threshold=days_threshold, limit=limit
        )
        
        analytics = []
        for job in jobs:
            analytics.append(JobAnalytics(
                job_id=job.id,
                title=job.title,
                applications_count=0,
                views_count=0,  # Would need interaction tracking
                days_posted=(datetime.utcnow() - job.created_at).days,
                status="No Applicants"
            ))
        
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs without applicants: {str(e)}"
        )

@router.get("/candidates-zero-visibility")
async def get_candidates_zero_visibility(
    db: AsyncSession = Depends(get_db_session),
    days_threshold: int = Query(30, ge=1, description="Days threshold for no activity"),
    limit: int = Query(20, ge=1, le=100)
):
    """Get candidates with zero visibility/activity"""
    try:
        candidates = await candidate_crud.get_candidates_zero_visibility(
            db, days_threshold=days_threshold, limit=limit
        )
        
        analytics = []
        for candidate in candidates:
            analytics.append(CandidateAnalytics(
                candidate_id=candidate.id,
                name=candidate.name,
                applications_count=0,
                views_received=0,
                last_activity=candidate.updated_at.isoformat(),
                visibility_score=0.0
            ))
        
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidates with zero visibility: {str(e)}"
        )

@router.get("/skill-gap-analysis")
async def get_skill_gap_analysis(
    db: AsyncSession = Depends(get_db_session),
    top_n: int = Query(10, ge=1, le=50, description="Top N skills to analyze")
):
    """Get skill demand vs availability analysis"""
    try:
        # This would require complex aggregation queries
        # For now, return mock data structure
        skill_gaps = [
            SkillGapAnalysis(
                skill="Python",
                demand_count=15,
                supply_count=8,
                gap=7,
                avg_salary_demand=120000,
                avg_salary_supply=95000
            ),
            SkillGapAnalysis(
                skill="React",
                demand_count=12,
                supply_count=10,
                gap=2,
                avg_salary_demand=110000,
                avg_salary_supply=105000
            ),
            SkillGapAnalysis(
                skill="Data Science",
                demand_count=8,
                supply_count=3,
                gap=5,
                avg_salary_demand=130000,
                avg_salary_supply=115000
            )
        ]
        
        return skill_gaps[:top_n]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve skill gap analysis: {str(e)}"
        )

@router.get("/application-stats")
async def get_application_statistics(
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(30, ge=1, le=365, description="Days to analyze")
):
    """Get application statistics"""
    try:
        # Get basic stats
        total_applications = await application_crud.count(db)
        recent_applications = await application_crud.count_recent(
            db, days_back=days_back
        )
        
        # Get status distribution
        status_distribution = await application_crud.get_status_distribution(db)
        
        return {
            "total_applications": total_applications,
            "recent_applications": recent_applications,
            "days_analyzed": days_back,
            "status_distribution": status_distribution
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve application statistics: {str(e)}"
        )

@router.get("/job-performance")
async def get_job_performance_metrics(
    db: AsyncSession = Depends(get_db_session),
    days_back: int = Query(30, ge=1, le=365, description="Days to analyze")
):
    """Get job performance metrics"""
    try:
        # Get job performance data
        performance_data = await job_crud.get_performance_metrics(
            db, days_back=days_back
        )
        
        return performance_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job performance metrics: {str(e)}"
        ) 