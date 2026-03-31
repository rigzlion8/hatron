"""make sales_orders contact_id nullable for POS walk-ins

Revision ID: cf2885b0aaf2
Revises: 12ac554e60f1
Create Date: 2026-03-31 10:41:50.027168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cf2885b0aaf2'
down_revision: Union[str, Sequence[str], None] = '12ac554e60f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('sales_orders', 'contact_id',
               existing_type=sa.UUID(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('sales_orders', 'contact_id',
               existing_type=sa.UUID(),
               nullable=False)
