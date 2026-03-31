"""Purchase models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    String,
    Text,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class PurchaseOrder(Base):
    """A Request for Quotation or confirmed Purchase Order."""
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. PO-00001
    
    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft, sent, confirmed, done, cancelled
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    receipt_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    amount_untaxed: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_tax: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_total: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    
    vendor_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self):
        return f"<PurchaseOrder {self.order_number} ({self.status})>"


class PurchaseOrderLine(Base):
    """Items being purchased."""
    __tablename__ = "purchase_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(15, 2), default=1.0)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0) # Usually standard cost, but vendor can override
    
    tax_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    price_subtotal: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    price_tax: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    price_total: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)

    order: Mapped["PurchaseOrder"] = relationship(back_populates="lines")

    def __repr__(self):
        return f"<PurchaseOrderLine {self.product_id} x{self.quantity}>"
