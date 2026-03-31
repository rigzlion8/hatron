"""Contacts module Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from backend.core.schemas import OrmBase


# ─── Address Schemas ───


class AddressCreate(BaseModel):
    """Create a new address."""

    type: str = Field("default", pattern="^(default|invoice|delivery|other)$")
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = Field(None, max_length=2, description="ISO 3166-1 alpha-2")
    is_primary: bool = False


class AddressUpdate(BaseModel):
    """Update an address."""

    type: Optional[str] = Field(None, pattern="^(default|invoice|delivery|other)$")
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = Field(None, max_length=2)
    is_primary: Optional[bool] = None


class AddressResponse(OrmBase):
    """Address in API responses."""

    id: uuid.UUID
    type: str
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    is_primary: bool


# ─── Contact Schemas ───


class ContactCreate(BaseModel):
    """Create a new contact."""

    type: str = Field("individual", pattern="^(individual|company)$")
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_customer: bool = False
    is_vendor: bool = False
    tags: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    addresses: Optional[List[AddressCreate]] = None


class ContactUpdate(BaseModel):
    """Update a contact (all fields optional for PATCH)."""

    type: Optional[str] = Field(None, pattern="^(individual|company)$")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_customer: Optional[bool] = None
    is_vendor: Optional[bool] = None
    tags: Optional[List[str]] = None
    avatar_url: Optional[str] = None


class ContactResponse(OrmBase):
    """Full contact detail response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    type: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_customer: bool
    is_vendor: bool
    tags: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    addresses: List[AddressResponse] = []
    created_at: datetime
    updated_at: datetime


class ContactListResponse(OrmBase):
    """Abbreviated contact for list views."""

    id: uuid.UUID
    type: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_customer: bool
    is_vendor: bool
    tags: Optional[List[str]] = None
    created_at: datetime
