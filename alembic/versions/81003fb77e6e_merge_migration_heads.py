"""Merge migration heads

Revision ID: 81003fb77e6e
Revises: 68528aa198fd, c9b2f8a4d5e6
Create Date: 2025-09-01 18:16:37.617263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81003fb77e6e'
down_revision: Union[str, None] = ('68528aa198fd', 'c9b2f8a4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
