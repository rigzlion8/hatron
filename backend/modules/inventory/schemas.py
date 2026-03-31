"""Inventory Schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.core.schemas import OrmBase


# ─── Warehouse & Locations ───

class WarehouseCreate(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    address_id: Optional[uuid.UUID] = None
    is_active: bool = True

class WarehouseResponse(OrmBase):
    id: uuid.UUID
    name: str
    code: str
    is_active: bool


class StockLocationCreate(BaseModel):
    name: str = Field(..., max_length=255)
    warehouse_id: Optional[uuid.UUID] = None
    type: str = Field(default="internal", pattern="^(internal|vendor|customer|loss|transit)$")
    parent_id: Optional[uuid.UUID] = None

class StockLocationResponse(OrmBase):
    id: uuid.UUID
    name: str
    type: str
    warehouse_id: Optional[uuid.UUID] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: bool


class StockQuantResponse(OrmBase):
    id: uuid.UUID
    product_id: uuid.UUID
    location_id: uuid.UUID
    quantity: Decimal
    updated_at: datetime


# ─── Movements ───

class StockMoveCreate(BaseModel):
    name: str
    product_id: uuid.UUID
    location_id: uuid.UUID
    location_dest_id: uuid.UUID
    quantity: Decimal = Field(default=Decimal(0), ge=0)
    quantity_done: Decimal = Field(default=Decimal(0), ge=0)

class StockMoveUpdate(BaseModel):
    quantity_done: Decimal = Field(default=Decimal(0), ge=0)

class StockMoveResponse(OrmBase):
    id: uuid.UUID
    picking_id: Optional[uuid.UUID] = None
    name: str
    product_id: uuid.UUID
    location_id: uuid.UUID
    location_dest_id: uuid.UUID
    quantity: Decimal
    quantity_done: Decimal
    status: str
    created_at: datetime
    date_done: Optional[datetime] = None


class StockPickingCreate(BaseModel):
    type: str = Field(..., pattern="^(incoming|outgoing|internal)$")
    location_id: uuid.UUID
    location_dest_id: uuid.UUID
    origin: Optional[str] = None
    contact_id: Optional[uuid.UUID] = None
    scheduled_date: Optional[datetime] = None
    lines: List[StockMoveCreate] = Field(default_factory=list)

class StockPickingResponse(OrmBase):
    id: uuid.UUID
    picking_number: str
    type: str
    location_id: uuid.UUID
    location_dest_id: uuid.UUID
    status: str
    origin: Optional[str] = None
    contact_id: Optional[uuid.UUID] = None
    scheduled_date: Optional[datetime] = None
    date_done: Optional[datetime] = None
    created_at: datetime
    moves: List[StockMoveResponse] = []

class StockPickingListResponse(OrmBase):
    id: uuid.UUID
    picking_number: str
    type: str
    location_id: uuid.UUID
    location_dest_id: uuid.UUID
    status: str
    origin: Optional[str] = None
    created_at: datetime
