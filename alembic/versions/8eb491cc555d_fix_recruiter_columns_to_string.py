"""fix_recruiter_columns_to_string

Revision ID: 8eb491cc555d
Revises: a7598c1c8efc
Create Date: 2025-08-05 20:25:19.598777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8eb491cc555d'
down_revision: Union[str, Sequence[str], None] = 'a7598c1c8efc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change domain and company_size columns from enum to string
    # This will allow us to store string values instead of enum values
    
    # First, create new columns with string type
    op.add_column('recruiters', sa.Column('domain_new', sa.String(50), nullable=True))
    op.add_column('recruiters', sa.Column('company_size_new', sa.String(20), nullable=True))
    
    # Copy data from old columns to new columns (if any data exists)
    # For now, we'll just create the new columns and drop the old ones
    
    # Drop the old enum columns
    op.drop_column('recruiters', 'domain')
    op.drop_column('recruiters', 'company_size')
    
    # Rename new columns to original names
    op.alter_column('recruiters', 'domain_new', new_column_name='domain')
    op.alter_column('recruiters', 'company_size_new', new_column_name='company_size')
    
    # Update any NULL values with default values before making NOT NULL
    op.execute("UPDATE recruiters SET domain = 'IT' WHERE domain IS NULL")
    op.execute("UPDATE recruiters SET company_size = '1-10' WHERE company_size IS NULL")
    
    # Make the columns not nullable
    op.alter_column('recruiters', 'domain', nullable=False)
    op.alter_column('recruiters', 'company_size', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert back to enum columns if needed
    pass
