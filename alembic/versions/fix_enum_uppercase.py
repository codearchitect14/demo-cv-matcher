"""fix_enum_uppercase

Revision ID: fix_enum_uppercase
Revises: ac1659092046
Create Date: 2025-08-27 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_enum_uppercase'
down_revision: Union[str, Sequence[str], None] = 'ac1659092046'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Update application status enum values to uppercase."""
    # Update existing enum values to uppercase
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'applied' TO 'APPLIED'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'rejected' TO 'REJECTED'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'reviewed' TO 'REVIEWED'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'interview_scheduled' TO 'INTERVIEW_SCHEDULED'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'hired' TO 'HIRED'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'pending' TO 'PENDING'")


def downgrade() -> None:
    """Downgrade schema - Revert enum values back to lowercase."""
    # Revert enum values back to lowercase
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'APPLIED' TO 'applied'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'REJECTED' TO 'rejected'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'REVIEWED' TO 'reviewed'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'INTERVIEW_SCHEDULED' TO 'interview_scheduled'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'HIRED' TO 'hired'")
    op.execute("ALTER TYPE applicationstatusenum RENAME VALUE 'PENDING' TO 'pending'")
