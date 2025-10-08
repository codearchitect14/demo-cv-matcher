"""Add role field to candidates table

Revision ID: add_role_field
Revises: 9fb63d4fdb6e
Create Date: 2025-01-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_role_field'
down_revision = '9fb63d4fdb6e'
branch_labels = None
depends_on = None

def upgrade():
    # Add role column to candidates table
    op.add_column('candidates', sa.Column('role', sa.String(20), nullable=False, server_default='user'))
    
    # Create index on role column
    op.create_index('idx_candidate_role', 'candidates', ['role'])

def downgrade():
    # Drop index
    op.drop_index('idx_candidate_role', table_name='candidates')
    
    # Drop role column
    op.drop_column('candidates', 'role') 