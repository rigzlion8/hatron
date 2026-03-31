"""Inventory Models."""

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


class Warehouse(Base):
    """A physical location handling inventory operations."""
    __tablename__ = "inventory_warehouses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. WH
    address_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    
    locations: Mapped[list["StockLocation"]] = relationship(
        back_populates="warehouse", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self):
        return f"<Warehouse {self.code} - {self.name}>"


class StockLocation(Base):
    """Granular locations (Shelf, Vendor Location, Customer Location, Inventory Loss)."""
    __tablename__ = "inventory_locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_warehouses.id", ondelete="CASCADE"), nullable=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="internal") # internal, vendor, customer, loss, transit
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    warehouse: Mapped["Warehouse | None"] = relationship(back_populates="locations")
    
    # Internal relationship
    children: Mapped[list["StockLocation"]] = relationship(back_populates="parent", lazy="selectin")
    parent: Mapped["StockLocation | None"] = relationship(back_populates="children", remote_side=[id])

    def __repr__(self):
        return f"<StockLocation {self.name} ({self.type})>"


class StockQuant(Base):
    """Current physical quantity of a product at a specific location."""
    __tablename__ = "inventory_quants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True, nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), index=True, nullable=False)
    
    quantity: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<StockQuant Prod:{self.product_id} Loc:{self.location_id} Qty:{self.quantity}>"


class StockPicking(Base):
    """A grouping of stock moves (e.g. Delivery Order or Receipt)."""
    __tablename__ = "inventory_pickings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    picking_number: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. WH/OUT/0001
    
    type: Mapped[str] = mapped_column(String(20), nullable=False) # incoming, outgoing, internal
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False) # Default Source
    location_dest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False) # Default Dest
    
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft, waiting, ready, done, cancelled
    
    origin: Mapped[str | None] = mapped_column(String(100), nullable=True) # e.g. SO-0001
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)

    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_done: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    moves: Mapped[list["StockMove"]] = relationship(
        back_populates="picking", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self):
        return f"<StockPicking {self.picking_number} ({self.status})>"


class StockMove(Base):
    """The individual movement of a product quantity from Source Location to Destination Location."""
    __tablename__ = "inventory_moves"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    picking_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_pickings.id", ondelete="CASCADE"), nullable=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False) # Description
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False)
    location_dest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False)
    
    quantity: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0) # Demand
    quantity_done: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0) # Actual Done
    
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft, waiting, available, done, cancelled

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date_done: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    picking: Mapped["StockPicking | None"] = relationship(back_populates="moves")

    def __repr__(self):
        return f"<StockMove {self.product_id} Qty:{self.quantity}>"
