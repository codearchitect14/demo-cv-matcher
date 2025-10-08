# # File: db/utils.py
# from typing import List, Dict, Any, Optional
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from sqlalchemy import and_, or_, func


# async def check_skill_requirements(
#     db: AsyncSession, 
#     candidate_id: int, 
#     job_id: int
# ) -> Dict[str, Any]:
#     """Check if candidate meets job skill requirements"""
#     from models.job import JobMandatorySkill
#     from models.candidate import CandidateExperience
    
#     # Get job requirements
#     job_skills_result = await db.execute(
#         select(JobMandatorySkill).where(JobMandatorySkill.job_id == job_id)
#     )
#     job_skills = job_skills_result.scalars().all()
    
#     # Get candidate skills
#     candidate_skills_result = await db.execute(
#         select(CandidateExperience).where(CandidateExperience.candidate_id == candidate_id)
#     )
#     candidate_skills = candidate_skills_result.scalars().all()
    
#     # Create skill mapping
#     candidate_skill_map = {skill.skill.lower(): skill.years for skill in candidate_skills}
    
#     requirements_met = []
#     requirements_missing = []
    
#     for job_skill in job_skills:
#         candidate_years = candidate_skill_map.get(job_skill.skill.lower(), 0)
#         requirement = {
#             "skill": job_skill.skill,
#             "required_years": job_skill.min_experience,
#             "candidate_years": candidate_years,
#             "meets_requirement": candidate_years >= job_skill.min_experience
#         }
        
#         if requirement["meets_requirement"]:
#             requirements_met.append(requirement)
#         else:
#             requirements_missing.append(requirement)
    
#     return {
#         "meets_all_requirements": len(requirements_missing) == 0,
#         "requirements_met": requirements_met,
#         "requirements_missing": requirements_missing,
#         "total_requirements": len(job_skills),
#         "met_count": len(requirements_met)
#     }


# async def get_database_stats(db: AsyncSession) -> Dict[str, int]:
#     """Get database statistics"""
#     from models.candidate import Candidate
#     from models.job import Job
#     from models.application import Application
#     from models.interaction import InteractionLog
    
#     # Count records in each table
#     candidates_count = await db.scalar(select(func.count(Candidate.id)))
#     jobs_count = await db.scalar(select(func.count(Job.id)))
#     applications_count = await db.scalar(select(func.count(Application.id)))
#     interactions_count = await db.scalar(select(func.count(InteractionLog.id)))
    
#     return {
#         "candidates": candidates_count,
#         "jobs": jobs_count,
#         "applications": applications_count,
#         "interactions": interactions_count
#     }


# Today's date: 25/07/2025
from typing import Dict, Any
from models.candidate import CandidateExperience
from models.job import JobMandatorySkill
from sqlalchemy import func

def format_skill_name(skill: str) -> str:
    """Format skill name to lowercase and strip whitespace"""
    return skill.lower().strip()

def calculate_match_percentage(matched: int, total: int) -> float:
    """Calculate percentage match between matched and total skills"""
    if total == 0:
        return 0.0
    return round((matched / total) * 100, 2)

async def get_database_stats(db) -> Dict[str, int]:
    """Get database statistics (moved to db/crud/stats.py in real implementation)"""
    from models.candidate import Candidate
    from models.job import Job
    from models.application import Application
    from models.interaction import InteractionLog
    
    candidates_count = await db.scalar(func.count(Candidate.id))
    jobs_count = await db.scalar(func.count(Job.id))
    applications_count = await db.scalar(func.count(Application.id))
    interactions_count = await db.scalar(func.count(InteractionLog.id))
    
    return {
        "candidates": candidates_count,
        "jobs": jobs_count,
        "applications": applications_count,
        "interactions": interactions_count
    }