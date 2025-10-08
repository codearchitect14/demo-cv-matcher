"""add recruiter table

Revision ID: add_recruiter_table_001
Revises: add_role_field
Create Date: 2025-01-04 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_recruiter_table_001'
down_revision = 'add_role_field'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types with IF NOT EXISTS
    op.execute("DO $$ BEGIN CREATE TYPE companysize AS ENUM ('1-10', '11-50', '51-200', '201-500', '501-1000', '1000+'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE domain AS ENUM ('IT', 'Healthcare', 'Finance', 'Education', 'Manufacturing', 'Retail', 'Consulting', 'Media', 'Real Estate', 'Transportation', 'Energy', 'Telecommunications', 'Other'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create recruiters table
    op.create_table('recruiters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=50), nullable=False),
        sa.Column('company_size', sa.String(length=20), nullable=False),
        sa.Column('company_description', sa.Text(), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='recruiter'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for recruiters table
    op.create_index('idx_recruiter_email', 'recruiters', ['email'])
    op.create_index('idx_recruiter_domain', 'recruiters', ['domain'])
    op.create_index('idx_recruiter_company_size', 'recruiters', ['company_size'])
    op.create_index('idx_recruiter_role', 'recruiters', ['role'])
    op.create_index('idx_recruiter_is_active', 'recruiters', ['is_active'])
    op.create_index('idx_recruiter_domain_company_size', 'recruiters', ['domain', 'company_size'])
    
    # Add recruiter_id column to jobs table
    op.add_column('jobs', sa.Column('recruiter_id', sa.Integer(), nullable=True))
    op.create_index('idx_job_recruiter', 'jobs', ['recruiter_id'])
    op.create_foreign_key('fk_job_recruiter', 'jobs', 'recruiters', ['recruiter_id'], ['id'], ondelete='CASCADE')
    
    # Add recruiter_id column to applications table
    op.add_column('applications', sa.Column('recruiter_id', sa.Integer(), nullable=True))
    op.create_index('idx_application_recruiter', 'applications', ['recruiter_id'])
    op.create_foreign_key('fk_application_recruiter', 'applications', 'recruiters', ['recruiter_id'], ['id'], ondelete='CASCADE')
    
    # Update interaction_log table to support both candidates and recruiters
    op.add_column('interaction_log', sa.Column('user_type', sa.String(length=20), nullable=False, server_default='candidate'))
    op.create_index('idx_interaction_log_user_type', 'interaction_log', ['user_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_interaction_log_user_type', table_name='interaction_log')
    op.drop_index('idx_application_recruiter', table_name='applications')
    op.drop_index('idx_job_recruiter', table_name='jobs')
    op.drop_index('idx_recruiter_domain_company_size', table_name='recruiters')
    op.drop_index('idx_recruiter_is_active', table_name='recruiters')
    op.drop_index('idx_recruiter_role', table_name='recruiters')
    op.drop_index('idx_recruiter_company_size', table_name='recruiters')
    op.drop_index('idx_recruiter_domain', table_name='recruiters')
    op.drop_index('idx_recruiter_email', table_name='recruiters')
    
    # Drop foreign keys
    op.drop_constraint('fk_application_recruiter', 'applications', type_='foreignkey')
    op.drop_constraint('fk_job_recruiter', 'jobs', type_='foreignkey')
    
    # Drop columns
    op.drop_column('interaction_log', 'user_type')
    op.drop_column('applications', 'recruiter_id')
    op.drop_column('jobs', 'recruiter_id')
    
    # Drop recruiters table
    op.drop_table('recruiters')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS domain')
    op.execute('DROP TYPE IF EXISTS companysize') 