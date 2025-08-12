"""merge performance indexes and role field

Revision ID: a9f01ac9d72a
Revises: performance_indexes_001, add_role_field
Create Date: 2025-08-04 14:57:57.705119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9f01ac9d72a'
down_revision: Union[str, Sequence[str], None] = ('performance_indexes_001', 'add_role_field')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
