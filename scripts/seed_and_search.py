import asyncio
import os
import sys
from typing import Tuple
import uuid

# Ensure project root is on sys.path when running from scripts/
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db_session
from db.crud import job as job_crud_module
from db.crud import job_skill as job_skill_crud
from db.crud import candidate as candidate_crud_module
from db.crud import candidate_skill as candidate_skill_crud
from db.crud import skill as skill_crud
from services.enhanced_recommendation_service import EnhancedRecommendationService


async def ensure_skill(db: AsyncSession, name: str) -> int:
    """Ensure a `skills` row exists; return its id."""
    db_skill = await skill_crud.get_by_name(db, name)
    if not db_skill:
        db_skill = await skill_crud.create(db, obj_in={
            'name': name,
            'category': 'programming',
            'description': f'{name} skill'
        })
    return db_skill.id


async def seed_job_with_skills(db: AsyncSession, title: str, company: str, location: str) -> Tuple[int, int, int]:
    """Create a job and attach Python + SQL requirements. Returns (job_id, py_id, sql_id)."""
    # Create job
    job = await job_crud_module.create(db, obj_in={
        'title': title,
        'company': company,
        'location': location,
        'salary_min': 80000,
        'salary_max': 120000,
        'domain': 'Software',
        'total_years_required': 3,
        'job_description': 'Build backend services with Python and SQL.'
    })

    # Ensure skills
    py_id = await ensure_skill(db, 'Python')
    sql_id = await ensure_skill(db, 'SQL')

    # Attach job_skills (normalized)
    await job_skill_crud.create(db, obj_in={
        'job_id': job.id,
        'skill_id': py_id,
        'min_years_experience': 2,
        'priority': 'required',
        'description': 'Core language'
    })
    await job_skill_crud.create(db, obj_in={
        'job_id': job.id,
        'skill_id': sql_id,
        'min_years_experience': 1,
        'priority': 'preferred',
        'description': 'Database querying'
    })

    # Also attach string-based mandatory_skills as a fallback path
    await job_crud_module.add_mandatory_skill(db, job_id=job.id, skill_data={'skill': 'Python', 'min_experience': 2})
    await job_crud_module.add_mandatory_skill(db, job_id=job.id, skill_data={'skill': 'SQL', 'min_experience': 1})

    return job.id, py_id, sql_id


async def seed_candidate_with_skills(db: AsyncSession, name: str, email: str, location: str, py_id: int, sql_id: int) -> int:
    """Create a candidate and attach Python + SQL skills. Returns candidate_id."""
    # Always ensure uniqueness by appending a short UUID if needed
    local, at, domain = email.partition('@')
    unique_email = email
    existing = await candidate_crud_module.get_by_email(db, unique_email)
    if existing:
        unique_email = f"{local}+{uuid.uuid4().hex[:8]}@{domain}"

    cand = await candidate_crud_module.create(db, obj_in={
        'name': name,
        'email': unique_email,
        'location': location,
        'domain': 'Software',
        'expected_salary_min': 70000,
        'expected_salary_max': 110000,
        'summary': 'Backend engineer with Python and SQL experience',
        'role': 'user',
        'consent_given': True
    })

    # Add normalized candidate_skills
    await candidate_skill_crud.create(db, obj_in={
        'candidate_id': cand.id,
        'skill_id': py_id,
        'years_experience': 3,
        'proficiency_level': 'advanced'
    })
    await candidate_skill_crud.create(db, obj_in={
        'candidate_id': cand.id,
        'skill_id': sql_id,
        'years_experience': 2,
        'proficiency_level': 'intermediate'
    })

    # Also add string-based candidate_experience as fallback
    await candidate_crud_module.bulk_create_experiences(db, candidate_id=cand.id, experiences=[
        {'skill': 'Python', 'years': 3, 'description': 'Backend development'},
        {'skill': 'SQL', 'years': 2, 'description': 'Data querying'}
    ])

    return cand.id


async def run():
    async for db in get_db_session():
        # 1) Seed job + candidate
        job_id, py_id, sql_id = await seed_job_with_skills(db, title='DemoMatch Python Developer', company='DemoCorp', location='Remote')
        candidate_id = await seed_candidate_with_skills(db, name='Demo Candidate', email='demo.candidate@example.com', location='Remote', py_id=py_id, sql_id=sql_id)

        print(f"Seeded job_id={job_id}, candidate_id={candidate_id}, skills(py_id={py_id}, sql_id={sql_id})")

        # 2) Run recruiter->candidates recommendations
        svc = EnhancedRecommendationService()
        recs = await svc.get_recruiter_candidate_recommendations(db=db, job_id=job_id, limit=10, include_explanation=True)

        print(f"\nRecommendations for job {job_id} -> {len(recs)} candidate(s):")
        for r in recs:
            print(f"- candidate_id={r.candidate_id}, score={r.overall_match_score:.2f}")
            met = [sm.skill_name for sm in r.skill_matches if sm.meets_requirement]
            gaps = [sm.skill_name for sm in r.skill_matches if not sm.meets_requirement]
            print(f"  meets: {met} | gaps: {gaps}")

        return


if __name__ == '__main__':
    asyncio.run(run())


