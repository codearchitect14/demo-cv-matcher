"""merge heads

Revision ID: a7598c1c8efc
Revises: 815abef10a00, fix_enum_values_001
Create Date: 2025-08-05 20:22:56.915133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7598c1c8efc'
down_revision: Union[str, Sequence[str], None] = ('815abef10a00', 'fix_enum_values_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
