"""Invoicing Module Models."""

import uuid
from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    String,
    Text,
    func,
    Date
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class TaxRule(Base):
    """A tax rule definition."""
    __tablename__ = "tax_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False) # e.g. 20.00 for 20%
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    def __repr__(self):
        return f"<TaxRule {self.name} ({self.rate}%)>"


class Invoice(Base):
    """A financial document sent to a customer."""
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    sales_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_orders.id"), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft, open, paid, cancelled
    type: Mapped[str] = mapped_column(String(20), default="out_invoice") # out_invoice, out_refund
    
    invoice_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    amount_untaxed: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_tax: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_total: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_residual: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0) # Amount left to pay
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lines: Mapped[list["InvoiceLine"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", lazy="selectin"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice", lazy="selectin"
    )

    def __repr__(self):
        return f"<Invoice {self.invoice_number} ({self.status})>"


class InvoiceLine(Base):
    """A line item on an invoice."""
    __tablename__ = "invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(15, 2), default=1.0)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    discount: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    
    tax_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tax_rules.id"), nullable=True)
    
    price_subtotal: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    price_tax: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    price_total: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)

    invoice: Mapped["Invoice"] = relationship(back_populates="lines")
    
    def __repr__(self):
        return f"<InvoiceLine x{self.quantity}>"


class Payment(Base):
    """A payment applied to an invoice."""
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False)
    
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False) # bank, cash, credit_card
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.amount} -> {self.invoice_id}>"
