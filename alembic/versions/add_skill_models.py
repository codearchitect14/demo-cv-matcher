"""add skill models

Revision ID: add_skill_models_001
Revises: fix_enum_values_001
Create Date: 2025-01-04 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_skill_models_001'
down_revision = 'fix_enum_values_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create skills table
    op.create_table('skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('aliases', sa.Text(), nullable=True),
        sa.Column('parent_skill_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for skills table
    op.create_index('idx_skill_name', 'skills', ['name'])
    op.create_index('idx_skill_category', 'skills', ['category'])
    op.create_index('idx_skill_is_active', 'skills', ['is_active'])
    
    # Create job_skills table
    op.create_table('job_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('min_years_experience', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='required'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for job_skills table
    op.create_index('idx_job_skill_job_id', 'job_skills', ['job_id'])
    op.create_index('idx_job_skill_skill_id', 'job_skills', ['skill_id'])
    op.create_index('idx_job_skill_min_years', 'job_skills', ['min_years_experience'])
    op.create_index('idx_job_skill_priority', 'job_skills', ['priority'])
    
    # Create foreign keys for job_skills
    op.create_foreign_key('fk_job_skill_job', 'job_skills', 'jobs', ['job_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_job_skill_skill', 'job_skills', 'skills', ['skill_id'], ['id'], ondelete='CASCADE')
    
    # Create candidate_skills table
    op.create_table('candidate_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('years_experience', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('proficiency_level', sa.String(length=20), nullable=False, server_default='beginner'),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('experience_description', sa.Text(), nullable=True),
        sa.Column('projects_worked', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for candidate_skills table
    op.create_index('idx_candidate_skill_candidate_id', 'candidate_skills', ['candidate_id'])
    op.create_index('idx_candidate_skill_skill_id', 'candidate_skills', ['skill_id'])
    op.create_index('idx_candidate_skill_years_experience', 'candidate_skills', ['years_experience'])
    op.create_index('idx_candidate_skill_last_used', 'candidate_skills', ['last_used'])
    
    # Create foreign keys for candidate_skills
    op.create_foreign_key('fk_candidate_skill_candidate', 'candidate_skills', 'candidates', ['candidate_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_candidate_skill_skill', 'candidate_skills', 'skills', ['skill_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop foreign keys
    op.drop_constraint('fk_candidate_skill_skill', 'candidate_skills', type_='foreignkey')
    op.drop_constraint('fk_candidate_skill_candidate', 'candidate_skills', type_='foreignkey')
    op.drop_constraint('fk_job_skill_skill', 'job_skills', type_='foreignkey')
    op.drop_constraint('fk_job_skill_job', 'job_skills', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_candidate_skill_last_used', table_name='candidate_skills')
    op.drop_index('idx_candidate_skill_years_experience', table_name='candidate_skills')
    op.drop_index('idx_candidate_skill_skill_id', table_name='candidate_skills')
    op.drop_index('idx_candidate_skill_candidate_id', table_name='candidate_skills')
    op.drop_index('idx_job_skill_priority', table_name='job_skills')
    op.drop_index('idx_job_skill_min_years', table_name='job_skills')
    op.drop_index('idx_job_skill_skill_id', table_name='job_skills')
    op.drop_index('idx_job_skill_job_id', table_name='job_skills')
    op.drop_index('idx_skill_is_active', table_name='skills')
    op.drop_index('idx_skill_category', table_name='skills')
    op.drop_index('idx_skill_name', table_name='skills')
    
    # Drop tables
    op.drop_table('candidate_skills')
    op.drop_table('job_skills')
    op.drop_table('skills') 