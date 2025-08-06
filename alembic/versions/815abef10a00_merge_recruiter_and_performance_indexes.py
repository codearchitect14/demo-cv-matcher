"""merge recruiter and performance indexes

Revision ID: 815abef10a00
Revises: a9f01ac9d72a, add_recruiter_table_001
Create Date: 2025-08-04 20:22:54.078407

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '815abef10a00'
down_revision: Union[str, Sequence[str], None] = ('a9f01ac9d72a', 'add_recruiter_table_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
