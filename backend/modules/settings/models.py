"""System Settings database models."""

import uuid
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class SystemSettings(Base):
    """Global or Tenant-specific branding and configuration."""
    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    
    # Branding
    brand_name: Mapped[str] = mapped_column(String(255), default="Hatron", server_default="Hatron")
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # UI Customization
    footer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    header_custom_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Extended Configuration
    payment_settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Audit
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    def __repr__(self):
        return f"<SystemSettings tenant={self.tenant_id} brand={self.brand_name}>"
