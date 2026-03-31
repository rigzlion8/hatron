"""System Settings schemas."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict


class SystemSettingsBase(BaseModel):
    """Common fields for SystemSettings."""
    brand_name: str = "Hatron"
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    footer_text: Optional[str] = None
    header_custom_html: Optional[str] = None
    payment_settings: Optional[Dict[str, Any]] = None


class SystemSettingsUpdate(SystemSettingsBase):
    """Schema to update settings (all fields optional)."""
    brand_name: Optional[str] = "Hatron"


class SystemSettingsResponse(SystemSettingsBase):
    """Schema returned by the API."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
