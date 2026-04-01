"""merge_heads

Revision ID: 2026033121
Revises: 2026033120, cf2885b0aaf2
Create Date: 2026-03-31 20:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2026033121'
down_revision: Union[str, Sequence[str], None] = ('2026033120', 'cf2885b0aaf2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - merge point, no schema changes."""
    pass


def downgrade() -> None:
    """Downgrade schema - merge point, no schema changes."""
    pass
