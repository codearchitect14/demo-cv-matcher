"""Add password reset columns to candidates

Revision ID: manual_password_reset
Revises: c51e6bd41eec
Create Date: 2025-10-01 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'manual_password_reset'
down_revision: Union[str, Sequence[str], None] = 'c51e6bd41eec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password reset columns to candidates table."""
    # Add reset_token column
    op.add_column('candidates', sa.Column('reset_token', sa.String(500), nullable=True))
    
    # Add reset_token_expires column
    op.add_column('candidates', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))
    
    # Create indexes for performance
    op.create_index('idx_candidates_reset_token', 'candidates', ['reset_token'], unique=False, postgresql_where=sa.text('reset_token IS NOT NULL'))
    op.create_index('idx_candidates_reset_token_expires', 'candidates', ['reset_token_expires'], unique=False, postgresql_where=sa.text('reset_token_expires IS NOT NULL'))


def downgrade() -> None:
    """Remove password reset columns from candidates table."""
    # Drop indexes first
    op.drop_index('idx_candidates_reset_token_expires', table_name='candidates')
    op.drop_index('idx_candidates_reset_token', table_name='candidates')
    
    # Drop columns
    op.drop_column('candidates', 'reset_token_expires')
    op.drop_column('candidates', 'reset_token')
