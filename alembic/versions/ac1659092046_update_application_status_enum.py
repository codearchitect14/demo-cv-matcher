"""update_application_status_enum

Revision ID: ac1659092046
Revises: add_skill_models_001
Create Date: 2025-08-26 13:05:47.991522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac1659092046'
down_revision: Union[str, Sequence[str], None] = 'add_skill_models_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Update the enum values to match the frontend expectations
    # We need to handle the enum conversion properly in PostgreSQL
    
    # First, create a new enum type with the updated values
    op.execute("""
        CREATE TYPE application_status_enum_new AS ENUM (
            'applied', 'rejected', 'reviewed', 'interview_scheduled', 'hired', 'pending'
        )
    """)
    
    # Convert existing values to the new enum type using text conversion
    op.execute("""
        ALTER TABLE applications 
        ALTER COLUMN status TYPE application_status_enum_new 
        USING CASE 
            WHEN status::text = 'accepted' THEN 'hired'::application_status_enum_new
            WHEN status::text = 'applied' THEN 'applied'::application_status_enum_new
            WHEN status::text = 'rejected' THEN 'rejected'::application_status_enum_new
            WHEN status::text = 'pending' THEN 'pending'::application_status_enum_new
            ELSE 'applied'::application_status_enum_new
        END
    """)
    
    # Drop the old enum type (using the correct name from SQLAlchemy)
    op.execute("DROP TYPE applicationstatusenum")
    
    # Rename the new enum type to the original name
    op.execute("ALTER TYPE application_status_enum_new RENAME TO applicationstatusenum")


def downgrade() -> None:
    """Downgrade schema."""
    # Revert back to the original enum values
    op.execute("""
        CREATE TYPE application_status_enum_old AS ENUM (
            'applied', 'rejected', 'accepted', 'pending'
        )
    """)
    
    # Convert 'hired' back to 'accepted' if needed
    op.execute("""
        UPDATE applications 
        SET status = 'accepted'::application_status_enum_old 
        WHERE status = 'hired'
    """)
    
    # Convert 'reviewed' and 'interview_scheduled' to 'accepted'
    op.execute("""
        UPDATE applications 
        SET status = 'accepted'::application_status_enum_old 
        WHERE status IN ('reviewed', 'interview_scheduled')
    """)
    
    # Convert existing values to the old enum type
    op.execute("""
        ALTER TABLE applications 
        ALTER COLUMN status TYPE application_status_enum_old 
        USING status::text::application_status_enum_old
    """)
    
    # Drop the new enum type
    op.execute("DROP TYPE applicationstatusenum")
    
    # Rename the old enum type to the original name
    op.execute("ALTER TYPE application_status_enum_old RENAME TO applicationstatusenum")
