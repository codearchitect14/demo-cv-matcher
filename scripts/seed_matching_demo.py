import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure project root is on sys.path when running from scripts/
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config.database import get_db_session
from db.crud import job, candidate, skill, job_skill, candidate_skill


async def ensure_skill(db: AsyncSession, name: str):
    db_skill = await skill.get_by_name(db, name)
    if not db_skill:
        db_skill = await skill.create(db, obj_in={
            'name': name,
            'category': 'tech',
            'description': f'{name} skill'
        })
    return db_skill


async def run():
    async for db in get_db_session():
        # 1) Create demo job
        demo_job = await job.create(db, obj_in={
            'title': 'Senior Python Developer',
            'company': 'DemoCorp',
            'location': 'Remote',
            'salary_min': 80000,
            'salary_max': 120000,
            'domain': 'Software',
            'total_years_required': 3,
            'job_description': 'Build backend services with Python and SQL.'
        })

        # 2) Ensure skills and attach to job
        py = await ensure_skill(db, 'Python')
        sql = await ensure_skill(db, 'SQL')

        await job_skill.create(db, obj_in={
            'job_id': demo_job.id,
            'skill_id': py.id,
            'min_years_experience': 2,
            'priority': 'required',
            'description': 'Core language'
        })

        await job_skill.create(db, obj_in={
            'job_id': demo_job.id,
            'skill_id': sql.id,
            'min_years_experience': 1,
            'priority': 'preferred',
            'description': 'Database querying'
        })

        # 3) Create demo candidate with matching skills
        demo_cand = await candidate.create(db, obj_in={
            'name': 'Test Candidate',
            'email': 'test.candidate@example.com',
            'location': 'Remote',
            'domain': 'Software',
            'expected_salary_min': 70000,
            'expected_salary_max': 110000,
            'summary': 'Backend engineer with Python and SQL experience',
            'role': 'user',
            'consent_given': True
        })

        await candidate_skill.create(db, obj_in={
            'candidate_id': demo_cand.id,
            'skill_id': py.id,
            'years_experience': 3,
            'proficiency_level': 'advanced'
        })

        await candidate_skill.create(db, obj_in={
            'candidate_id': demo_cand.id,
            'skill_id': sql.id,
            'years_experience': 2,
            'proficiency_level': 'intermediate'
        })

        print('\nSeed complete:')
        print(f"  Job id: {demo_job.id} - Senior Python Developer")
        print(f"  Candidate id: {demo_cand.id} - Test Candidate")
        return


if __name__ == '__main__':
    asyncio.run(run())


