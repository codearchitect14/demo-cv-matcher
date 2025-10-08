"""merge heads

Revision ID: c51e6bd41eec
Revises: add_total_experience_years, add_company_id_jobs
Create Date: 2025-09-24 16:11:44.089485

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c51e6bd41eec'
down_revision: Union[str, Sequence[str], None] = ('add_total_experience_years', 'add_company_id_jobs')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
