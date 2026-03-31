"""add image_url to products

Revision ID: b90cf5f42cbd
Revises: b09ddf082b28
Create Date: 2026-03-31 06:44:56.859309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b90cf5f42cbd'
down_revision: Union[str, Sequence[str], None] = 'b09ddf082b28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('products', sa.Column('image_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('products', 'image_url')
