"""Add performance indexes

Revision ID: performance_indexes_001
Revises: 9fb63d4fdb6e
Create Date: 2024-01-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'performance_indexes_001'
down_revision = '9fb63d4fdb6e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create indexes for candidates table
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates (email)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_location ON candidates (location)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_domain ON candidates (domain)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_salary_range ON candidates (expected_salary_min, expected_salary_max)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON candidates (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_role ON candidates (role)")
    
    # Composite indexes for candidates
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_location_domain ON candidates (location, domain)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_domain_salary ON candidates (domain, expected_salary_min, expected_salary_max)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_role_created ON candidates (role, created_at)")
    
    # Create indexes for jobs table
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs (company)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs (location)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_domain ON jobs (domain)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_salary_range ON jobs (salary_min, salary_max)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs (created_at)")
    
    # Composite indexes for jobs
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_location_domain ON jobs (location, domain)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company_location ON jobs (company, location)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_domain_salary ON jobs (domain, salary_min, salary_max)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_domain_years ON jobs (domain, total_years_required)")
    
    # Create indexes for applications table
    op.execute("CREATE INDEX IF NOT EXISTS idx_applications_candidate_id ON applications (candidate_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications (job_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications (status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications (created_at)")
    
    # Composite indexes for applications
    op.execute("CREATE INDEX IF NOT EXISTS idx_applications_candidate_status ON applications (candidate_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_applications_job_status ON applications (job_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_applications_status_created ON applications (status, created_at)")
    
    # Create indexes for interaction_log table
    op.execute("CREATE INDEX IF NOT EXISTS idx_interaction_log_user_id ON interaction_log (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_interaction_log_job_id ON interaction_log (job_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_interaction_log_type ON interaction_log (interaction_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_interaction_log_timestamp ON interaction_log (timestamp)")
    
    # Composite indexes for interaction analytics
    op.execute("CREATE INDEX IF NOT EXISTS idx_interaction_log_user_type ON interaction_log (user_id, interaction_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_interaction_log_job_type ON interaction_log (job_id, interaction_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_interaction_log_type_timestamp ON interaction_log (interaction_type, timestamp)")
    
    # Create indexes for candidate_experience table
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidate_experience_candidate_id ON candidate_experience (candidate_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidate_experience_skill ON candidate_experience (skill)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidate_experience_years ON candidate_experience (years)")
    
    # Composite indexes for experience queries
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidate_experience_candidate_skill ON candidate_experience (candidate_id, skill)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidate_experience_skill_years ON candidate_experience (skill, years)")
    
    # Create indexes for job_mandatory_skills table
    op.execute("CREATE INDEX IF NOT EXISTS idx_job_mandatory_skills_job_id ON job_mandatory_skills (job_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_job_mandatory_skills_skill ON job_mandatory_skills (skill)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_job_mandatory_skills_min_experience ON job_mandatory_skills (min_experience)")
    
    # Composite indexes for job skills queries
    op.execute("CREATE INDEX IF NOT EXISTS idx_job_mandatory_skills_job_skill ON job_mandatory_skills (job_id, skill)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_job_mandatory_skills_skill_experience ON job_mandatory_skills (skill, min_experience)")
    
    # Partial indexes for active records (only if deleted_at column exists)
    try:
        op.execute('CREATE INDEX IF NOT EXISTS idx_candidates_active ON candidates (id) WHERE deleted_at IS NULL')
    except:
        pass  # Skip if deleted_at column doesn't exist
    
    try:
        op.execute('CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs (id) WHERE deleted_at IS NULL')
    except:
        pass  # Skip if deleted_at column doesn't exist
    
    try:
        op.execute('CREATE INDEX IF NOT EXISTS idx_applications_active ON applications (id) WHERE deleted_at IS NULL')
    except:
        pass  # Skip if deleted_at column doesn't exist
    
    # Text search indexes for full-text search
    op.execute('CREATE INDEX IF NOT EXISTS idx_candidates_name_gin ON candidates USING gin(to_tsvector(\'english\', name))')
    op.execute('CREATE INDEX IF NOT EXISTS idx_candidates_summary_gin ON candidates USING gin(to_tsvector(\'english\', summary))')
    op.execute('CREATE INDEX IF NOT EXISTS idx_jobs_title_gin ON jobs USING gin(to_tsvector(\'english\', title))')
    op.execute('CREATE INDEX IF NOT EXISTS idx_jobs_description_gin ON jobs USING gin(to_tsvector(\'english\', job_description))')


def downgrade() -> None:
    # Drop text search indexes
    op.execute('DROP INDEX IF EXISTS idx_candidates_name_gin')
    op.execute('DROP INDEX IF EXISTS idx_candidates_summary_gin')
    op.execute('DROP INDEX IF EXISTS idx_jobs_title_gin')
    op.execute('DROP INDEX IF EXISTS idx_jobs_description_gin')
    
    # Drop partial indexes
    op.execute('DROP INDEX IF EXISTS idx_candidates_active')
    op.execute('DROP INDEX IF EXISTS idx_jobs_active')
    op.execute('DROP INDEX IF EXISTS idx_applications_active')
    
    # Drop composite indexes
    op.drop_index('idx_candidates_location_domain', table_name='candidates')
    op.drop_index('idx_candidates_domain_salary', table_name='candidates')
    op.drop_index('idx_candidates_role_created', table_name='candidates')
    op.drop_index('idx_jobs_location_domain', table_name='jobs')
    op.drop_index('idx_jobs_company_location', table_name='jobs')
    op.drop_index('idx_jobs_domain_salary', table_name='jobs')
    op.drop_index('idx_jobs_domain_years', table_name='jobs')
    op.drop_index('idx_applications_candidate_status', table_name='applications')
    op.drop_index('idx_applications_job_status', table_name='applications')
    op.drop_index('idx_applications_status_created', table_name='applications')
    op.drop_index('idx_interaction_log_user_type', table_name='interaction_log')
    op.drop_index('idx_interaction_log_job_type', table_name='interaction_log')
    op.drop_index('idx_interaction_log_type_timestamp', table_name='interaction_log')
    op.drop_index('idx_candidate_experience_candidate_skill', table_name='candidate_experience')
    op.drop_index('idx_candidate_experience_skill_years', table_name='candidate_experience')
    op.drop_index('idx_job_mandatory_skills_job_skill', table_name='job_mandatory_skills')
    op.drop_index('idx_job_mandatory_skills_skill_experience', table_name='job_mandatory_skills')
    
    # Drop single column indexes
    op.drop_index('idx_candidates_email', table_name='candidates')
    op.drop_index('idx_candidates_location', table_name='candidates')
    op.drop_index('idx_candidates_domain', table_name='candidates')
    op.drop_index('idx_candidates_salary_range', table_name='candidates')
    op.drop_index('idx_candidates_created_at', table_name='candidates')
    op.drop_index('idx_candidates_role', table_name='candidates')
    op.drop_index('idx_jobs_company', table_name='jobs')
    op.drop_index('idx_jobs_location', table_name='jobs')
    op.drop_index('idx_jobs_domain', table_name='jobs')
    op.drop_index('idx_jobs_salary_range', table_name='jobs')
    op.drop_index('idx_jobs_created_at', table_name='jobs')
    op.drop_index('idx_applications_candidate_id', table_name='applications')
    op.drop_index('idx_applications_job_id', table_name='applications')
    op.drop_index('idx_applications_status', table_name='applications')
    op.drop_index('idx_applications_created_at', table_name='applications')
    op.drop_index('idx_interaction_log_user_id', table_name='interaction_log')
    op.drop_index('idx_interaction_log_job_id', table_name='interaction_log')
    op.drop_index('idx_interaction_log_type', table_name='interaction_log')
    op.drop_index('idx_interaction_log_timestamp', table_name='interaction_log')
    op.drop_index('idx_candidate_experience_candidate_id', table_name='candidate_experience')
    op.drop_index('idx_candidate_experience_skill', table_name='candidate_experience')
    op.drop_index('idx_candidate_experience_years', table_name='candidate_experience')
    op.drop_index('idx_job_mandatory_skills_job_id', table_name='job_mandatory_skills')
    op.drop_index('idx_job_mandatory_skills_skill', table_name='job_mandatory_skills')
    op.drop_index('idx_job_mandatory_skills_min_experience', table_name='job_mandatory_skills') 