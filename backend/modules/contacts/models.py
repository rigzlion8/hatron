"""Contacts module database models — Contact and Address entities."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Contact(Base):
    """Unified contact entity — represents both individuals and companies.

    Contacts are the foundation shared across CRM, Sales, Invoicing,
    Purchase, and other modules. The `is_customer` and `is_vendor`
    flags determine their role in business processes.
    """

    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="individual"
    )  # 'individual' or 'company'
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Hierarchical: individuals can belong to a company
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True
    )

    # Business classification
    is_customer: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    is_vendor: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # Tags for flexible categorization
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )

    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft delete and audit
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    addresses: Mapped[list["Address"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan", lazy="selectin"
    )
    parent: Mapped["Contact | None"] = relationship(
        remote_side="Contact.id", lazy="selectin"
    )

    def __repr__(self):
        return f"<Contact {self.name} ({self.type})>"


class Address(Base):
    """Physical address linked to a contact.

    A contact can have multiple addresses with different types
    (invoice, delivery, etc.).
    """

    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(20), default="default"
    )  # 'default', 'invoice', 'delivery', 'other'
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    street2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(
        String(2), nullable=True
    )  # ISO 3166-1 alpha-2
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # Relationships
    contact: Mapped["Contact"] = relationship(back_populates="addresses")

    def __repr__(self):
        return f"<Address {self.city}, {self.country} ({self.type})>"
