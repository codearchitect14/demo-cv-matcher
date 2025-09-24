"""Add total_experience_years to candidates table

Revision ID: add_total_experience_years
Revises: a9f01ac9d72a
Create Date: 2025-01-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_total_experience_years'
down_revision = 'a9f01ac9d72a'
branch_labels = None
depends_on = None

def upgrade():
    # Add total_experience_years column to candidates table
    op.add_column('candidates', sa.Column('total_experience_years', sa.Integer(), nullable=True))
    
    # Create index on total_experience_years column
    op.create_index('idx_candidate_total_experience', 'candidates', ['total_experience_years'])

def downgrade():
    # Drop index
    op.drop_index('idx_candidate_total_experience', table_name='candidates')
    
    # Drop total_experience_years column
    op.drop_column('candidates', 'total_experience_years')
