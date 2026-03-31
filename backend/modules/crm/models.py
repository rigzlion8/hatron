"""CRM module database models — Pipelines, Stages, Leads, Activities."""

import uuid
from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    DateTime,
    Numeric,
    Integer,
    ForeignKey,
    String,
    Text,
    func,
    Date
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class CrmPipeline(Base):
    """A sales pipeline grouping multiple stages."""
    __tablename__ = "crm_pipelines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    
    stages: Mapped[list["CrmStage"]] = relationship(
        back_populates="pipeline", cascade="all, delete-orphan", lazy="selectin",
        order_by="CrmStage.sequence"
    )

    def __repr__(self):
        return f"<CrmPipeline {self.name}>"


class CrmStage(Base):
    """Stages within a CRM Pipeline."""
    __tablename__ = "crm_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_pipelines.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fold: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    probability: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)

    pipeline: Mapped["CrmPipeline"] = relationship(back_populates="stages")

    def __repr__(self):
        return f"<CrmStage {self.name}>"


class CrmLead(Base):
    """An opportunity or lead in the CRM."""
    __tablename__ = "crm_leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True
    )
    stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_stages.id"), nullable=True
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_revenue: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    probability: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    expected_close: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0) # 0 to 3
    status: Mapped[str] = mapped_column(String(20), default="open") # open, won, lost
    lost_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True, default=list)

    # Soft delete & audit
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    activities: Mapped[list["CrmActivity"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan", lazy="selectin",
        order_by="CrmActivity.created_at.desc()"
    )
    
    stage: Mapped["CrmStage | None"] = relationship(lazy="selectin")

    def __repr__(self):
        return f"<CrmLead {self.name} ({self.status})>"


class CrmActivity(Base):
    """An activity logged against a lead."""
    __tablename__ = "crm_activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_leads.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False) # call, email, meeting, note
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped["CrmLead"] = relationship(back_populates="activities")

    def __repr__(self):
        return f"<CrmActivity {self.type}>"
