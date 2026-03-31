"""Manufacturing Models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class BillOfMaterial(Base):
    """BOM: Defines components needed to build a finished good."""
    __tablename__ = "mrp_boms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_qty: Mapped[float] = mapped_column(Numeric(15, 2), default=1.0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    lines: Mapped[list["BillOfMaterialLine"]] = relationship(
        back_populates="bom", cascade="all, delete-orphan"
    )


class BillOfMaterialLine(Base):
    __tablename__ = "mrp_bom_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    
    bom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mrp_boms.id", ondelete="CASCADE"), nullable=False)
    component_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    product_qty: Mapped[float] = mapped_column(Numeric(15, 2), default=1.0)
    
    bom: Mapped["BillOfMaterial"] = relationship(back_populates="lines")


class ManufacturingOrder(Base):
    """Execution of a BOM."""
    __tablename__ = "mrp_production_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    
    name: Mapped[str] = mapped_column(String(50), nullable=False) # MO-0001
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    bom_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mrp_boms.id"), nullable=True)
    
    product_qty: Mapped[float] = mapped_column(Numeric(15, 2), default=1.0)
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft, confirmed, in_progress, done, cancelled
    
    date_planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date_planned_finished: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
