"""Add company_id to jobs table

Revision ID: add_company_id_jobs
Revises: add_recruiter_id_jobs
Create Date: 2025-01-17 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_company_id_jobs'
down_revision = 'add_recruiter_id_jobs'
depends_on = None

def upgrade():
    """Add company_id column and index to jobs table"""
    try:
        op.add_column('jobs', sa.Column('company_id', sa.Integer(), nullable=True))
    except Exception:
        pass  # Column might already exist
    
    try:
        op.create_foreign_key(
            'fk_jobs_company_id', 
            'jobs', 
            'companies', 
            ['company_id'], 
            ['id'], 
            ondelete='CASCADE'
        )
    except Exception:
        pass  # Constraint might already exist
    
    try:
        op.create_index('idx_job_company_id', 'jobs', ['company_id'])
    except Exception:
        pass  # Index might already exist

def downgrade():
    """Remove company_id column and related constraints"""
    try:
        op.drop_index('idx_job_company_id', table_name='jobs')
    except Exception:
        pass
    
    try:
        op.drop_constraint('fk_jobs_company_id', 'jobs', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.drop_column('jobs', 'company_id')
    except Exception:
        pass
