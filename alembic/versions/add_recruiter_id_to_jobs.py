"""Add recruiter_id to jobs table

Revision ID: add_recruiter_id_jobs
Revises: 
Create Date: 2025-01-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_recruiter_id_jobs'
down_revision = 'fix_enum_uppercase'
depends_on = None

def upgrade():
    """Add recruiter_id column and index to jobs table (if not exists)"""
    # Since column already exists, just add constraints
    try:
        op.create_foreign_key(
            'fk_jobs_recruiter_id', 
            'jobs', 
            'recruiters', 
            ['recruiter_id'], 
            ['id'], 
            ondelete='CASCADE'
        )
    except Exception:
        pass
    
    try:
        op.create_index('idx_job_recruiter', 'jobs', ['recruiter_id'])
    except Exception:
        pass

def downgrade():
    """Remove recruiter_id column and related constraints"""
    # Drop index
    op.drop_index('idx_job_recruiter', table_name='jobs')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_jobs_recruiter_id', 'jobs', type_='foreignkey')
    
    # Drop column
    op.drop_column('jobs', 'recruiter_id')
