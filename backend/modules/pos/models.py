"""POS (Point of Sale) module models — Sessions and Orders."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base
from backend.core.models import BaseModel


class POSSession(Base):
    """A POS register session (shift)."""
    __tablename__ = "pos_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "Main Cashier - Shift A"
    
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    stop_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="open") # open, closed, closing_control
    
    opening_balance: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    closing_balance: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Relationships
    orders: Mapped[List["POSOrder"]] = relationship(back_populates="session", lazy="selectin")

    def __repr__(self):
        return f"<POSSession {self.name} ({self.status})>"


class POSOrder(Base):
    """A retail transaction made at a POS terminal."""
    __tablename__ = "pos_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pos_sessions.id"), nullable=False)
    
    order_reference: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. POS/2026/0001
    
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    
    amount_total: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_tax: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_paid: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_return: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    
    payment_method: Mapped[str] = mapped_column(String(50), default="cash") # cash, card, bank_transfer
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session: Mapped["POSSession"] = relationship(back_populates="orders")
    lines: Mapped[List["POSOrderLine"]] = relationship(back_populates="order", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<POSOrder {self.order_reference} Total: {self.amount_total}>"


class POSOrderLine(Base):
    """Line item for a POS transaction."""
    __tablename__ = "pos_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pos_orders.id", ondelete="CASCADE"), nullable=False)
    
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(15, 2), default=1.0)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    price_subtotal: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    
    order: Mapped["POSOrder"] = relationship(back_populates="lines")

    def __repr__(self):
        return f"<POSOrderLine Product: {self.product_id} x{self.quantity}>"
