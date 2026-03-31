"""CRM Pydantic Schemas."""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.core.schemas import OrmBase


class CrmStageCreate(BaseModel):
    name: str = Field(..., max_length=255)
    sequence: int = 0
    fold: bool = False
    probability: Decimal = Field(default=Decimal(0), ge=0, le=100)

class CrmStageResponse(OrmBase):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    name: str
    sequence: int
    fold: bool
    probability: Decimal

class CrmPipelineCreate(BaseModel):
    name: str = Field(..., max_length=255)
    is_default: bool = False
    stages: Optional[List[CrmStageCreate]] = None

class CrmPipelineResponse(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    is_default: bool
    stages: List[CrmStageResponse] = []


class CrmActivityCreate(BaseModel):
    type: str = Field(..., max_length=50) # call, email, meeting, task
    summary: Optional[str] = Field(None, max_length=255)
    note: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[uuid.UUID] = None

class CrmActivityUpdate(BaseModel):
    done: bool

class CrmActivityResponse(OrmBase):
    id: uuid.UUID
    lead_id: uuid.UUID
    type: str
    summary: Optional[str] = None
    note: Optional[str] = None
    due_date: Optional[datetime] = None
    done: bool
    assigned_to: Optional[uuid.UUID] = None
    created_at: datetime


class CrmLeadCreate(BaseModel):
    name: str = Field(..., max_length=255)
    contact_id: Optional[uuid.UUID] = None
    stage_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    source: Optional[str] = Field(None, max_length=100)
    expected_revenue: Decimal = Field(default=Decimal(0), ge=0)
    probability: Decimal = Field(default=Decimal(0), ge=0, le=100)
    expected_close: Optional[date] = None
    priority: int = Field(default=0, ge=0, le=3)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class CrmLeadUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    contact_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    source: Optional[str] = Field(None, max_length=100)
    expected_revenue: Optional[Decimal] = Field(None, ge=0)
    probability: Optional[Decimal] = Field(None, ge=0, le=100)
    expected_close: Optional[date] = None
    priority: Optional[int] = Field(None, ge=0, le=3)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class CrmLeadStateUpdate(BaseModel):
    """Specific schema for moving stages or marking won/lost"""
    stage_id: Optional[uuid.UUID] = None
    status: Optional[str] = Field(None, pattern="^(open|won|lost)$")
    lost_reason: Optional[str] = None

class CrmLeadResponse(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    contact_id: Optional[uuid.UUID] = None
    stage_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    source: Optional[str] = None
    expected_revenue: Decimal
    probability: Decimal
    expected_close: Optional[date] = None
    priority: int
    status: str
    lost_reason: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    stage: Optional[CrmStageResponse] = None
    activities: List[CrmActivityResponse] = []

class CrmLeadListResponse(OrmBase):
    id: uuid.UUID
    name: str
    contact_id: Optional[uuid.UUID] = None
    stage_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    expected_revenue: Decimal
    probability: Decimal
    expected_close: Optional[date] = None
    priority: int
    status: str
    created_at: datetime
    stage: Optional[CrmStageResponse] = None
