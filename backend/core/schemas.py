"""Shared Pydantic schemas for API responses, pagination, and errors."""

import uuid
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class OrmBase(BaseModel):
    """Base schema that enables ORM mode for SQLAlchemy model serialization."""

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    """Pagination metadata returned with list responses."""

    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response."""

    data: List[T]
    meta: PaginationMeta


class ErrorDetail(BaseModel):
    """Individual field-level error detail."""

    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None


class MessageResponse(BaseModel):
    """Simple success message response."""

    message: str


class IDResponse(BaseModel):
    """Response with just an ID (for create operations)."""

    id: uuid.UUID
    message: str = "Created successfully"


class TimestampMixin(OrmBase):
    """Mixin providing created/updated timestamps."""

    created_at: datetime
    updated_at: datetime
