"""add attributes

Revision ID: 12ac554e60f1
Revises: b90cf5f42cbd
Create Date: 2026-03-31 07:45:10.213780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '12ac554e60f1'
down_revision: Union[str, Sequence[str], None] = 'b90cf5f42cbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'attributes')
    # ### end Alembic commands ###
