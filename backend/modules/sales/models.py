"""Sales module Models — Products, Categories, Orders."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Numeric,
    Integer,
    ForeignKey,
    String,
    Text,
    func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.modules.contacts.models import Contact


class ProductCategory(Base):
    """Hierarchical grouping of products."""
    __tablename__ = "product_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Internal relationship
    subcategories: Mapped[list["ProductCategory"]] = relationship(back_populates="parent", lazy="selectin")
    parent: Mapped["ProductCategory | None"] = relationship(back_populates="subcategories", remote_side=[id])

    def __repr__(self):
        return f"<ProductCategory {self.name}>"


class Product(Base):
    """Items and services being sold."""
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    type: Mapped[str] = mapped_column(String(50), default="storable") # storable, consumable, service
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    
    price: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    cost: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description_sales: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category: Mapped["ProductCategory | None"] = relationship(lazy="selectin")

    def __repr__(self):
        return f"<Product {self.name}>"


class SalesOrder(Base):
    """A sales quotation or confirmed order."""
    __tablename__ = "sales_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm_leads.id"), nullable=True)
    salesperson_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft, sent, confirmed, cancelled
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    validity_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    amount_untaxed: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_tax: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    amount_total: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    
    customer_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lines: Mapped[list["SalesOrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )
    contact: Mapped["Contact | None"] = relationship(lazy="selectin")

    def __repr__(self):
        return f"<SalesOrder {self.order_number} ({self.status})>"


class SalesOrderLine(Base):
    """A specific line item on a SalesOrder."""
    __tablename__ = "sales_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False)
    
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(15, 2), default=1.0)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    discount: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0) # Percentage
    
    tax_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True) # Will link to invoice module later playfully via ID
    
    price_subtotal: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    price_tax: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    price_total: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)

    order: Mapped["SalesOrder"] = relationship(back_populates="lines")

    def __repr__(self):
        return f"<SalesOrderLine {self.product_id} x{self.quantity}>"
