"""Add password reset columns only

Revision ID: 5ca46a68bba7
Revises: 6ee43cdb7264
Create Date: 2025-10-01 16:29:23.378728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ca46a68bba7'
down_revision: Union[str, Sequence[str], None] = '6ee43cdb7264'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
