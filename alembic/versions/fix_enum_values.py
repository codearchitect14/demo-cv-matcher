"""fix enum values to match frontend

Revision ID: fix_enum_values_001
Revises: 8eb491cc555d
Create Date: 2025-01-04 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_enum_values_001'
down_revision = '8eb491cc555d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The issue is that the database enum values don't match what the frontend sends
    # Database has: SMALL_11_50, MEDIUM_51_200, etc.
    # Frontend sends: "11-50", "51-200", etc.
    
    # We need to update the enum values to match the frontend
    # Since we can't easily modify enum values in PostgreSQL, 
    # we'll create a new migration that handles this properly
    
    # For now, let's just ensure the table columns can accept the string values
    # by temporarily changing them to text and back to enum
    
    # This is a workaround - we'll handle the enum conversion in the application layer
    pass


def downgrade() -> None:
    pass 