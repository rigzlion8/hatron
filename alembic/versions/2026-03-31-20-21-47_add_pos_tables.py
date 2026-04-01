"""add_pos_tables

Revision ID: 2026033120
Revises: b90cf5f42cbd
Create Date: 2026-03-31 20:21:47

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2026033120'
down_revision: Union[str, Sequence[str], None] = 'b90cf5f42cbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create POS Sessions table
    op.create_table('pos_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('stop_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('opening_balance', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('closing_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pos_sessions_tenant_id'), 'pos_sessions', ['tenant_id'], unique=False)

    # Create POS Orders table
    op.create_table('pos_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_reference', sa.String(length=50), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount_total', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('amount_tax', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('amount_paid', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('amount_return', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['pos_sessions.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pos_orders_tenant_id'), 'pos_orders', ['tenant_id'], unique=False)

    # Create POS Order Lines table
    op.create_table('pos_order_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('price_subtotal', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['pos_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pos_order_lines_tenant_id'), 'pos_order_lines', ['tenant_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_pos_order_lines_tenant_id'), table_name='pos_order_lines')
    op.drop_table('pos_order_lines')
    op.drop_index(op.f('ix_pos_orders_tenant_id'), table_name='pos_orders')
    op.drop_table('pos_orders')
    op.drop_index(op.f('ix_pos_sessions_tenant_id'), table_name='pos_sessions')
    op.drop_table('pos_sessions')
