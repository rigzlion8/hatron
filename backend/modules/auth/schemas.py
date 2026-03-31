"""Auth module Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.core.schemas import OrmBase


# ─── Request Schemas ───


class RegisterRequest(BaseModel):
    """New user registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    tenant_name: Optional[str] = Field(
        None,
        description="If provided, creates a new tenant. Otherwise, must provide tenant_id.",
    )
    tenant_id: Optional[uuid.UUID] = Field(
        None, description="Existing tenant to join."
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """User login request."""

    email: str = Field(..., description="Email or Username")
    password: str
    tenant_slug: Optional[str] = Field(
        None, description="Tenant slug for multi-tenant login."
    )


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class UpdateProfileRequest(BaseModel):
    """Update user profile."""

    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ─── Response Schemas ───


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RoleResponse(OrmBase):
    """Role summary in user responses."""

    id: uuid.UUID
    name: str
    description: Optional[str] = None


class UserResponse(OrmBase):
    """User detail response."""

    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    is_active: bool
    is_superuser: bool
    roles: List[RoleResponse] = []
    tenant_id: uuid.UUID
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserListResponse(OrmBase):
    """Abbreviated user info for list endpoints."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    roles: List[RoleResponse] = []
    created_at: datetime
