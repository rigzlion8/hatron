"""Sales Pydantic Schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.core.schemas import OrmBase


# ─── Products ───

class ProductCategoryCreate(BaseModel):
    name: str = Field(..., max_length=255)
    parent_id: Optional[uuid.UUID] = None
    description: Optional[str] = None

class ProductCategoryResponse(OrmBase):
    id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID] = None
    description: Optional[str] = None

class ProductCreate(BaseModel):
    name: str = Field(..., max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    type: str = Field(default="storable", pattern="^(storable|consumable|service)$")
    category_id: Optional[uuid.UUID] = None
    price: Decimal = Field(default=Decimal(0), ge=0)
    cost: Decimal = Field(default=Decimal(0), ge=0)
    description_sales: Optional[str] = None
    attributes: Optional[dict] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, pattern="^(storable|consumable|service)$")
    category_id: Optional[uuid.UUID] = None
    price: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    description_sales: Optional[str] = None
    attributes: Optional[dict] = None
    is_active: Optional[bool] = None

class ProductResponse(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    sku: Optional[str] = None
    type: str
    category_id: Optional[uuid.UUID] = None
    price: Decimal
    cost: Decimal
    description_sales: Optional[str] = None
    attributes: Optional[dict] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategoryResponse] = None


# ─── Sales Orders ───

class SalesOrderLineCreate(BaseModel):
    product_id: uuid.UUID
    description: Optional[str] = None
    quantity: Decimal = Field(default=Decimal("1.0"), gt=0)
    unit_price: Optional[Decimal] = None # Will pull from product if None
    discount: Decimal = Field(default=Decimal(0), ge=0, le=100)
    tax_id: Optional[uuid.UUID] = None

class SalesOrderLineResponse(OrmBase):
    id: uuid.UUID
    product_id: uuid.UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    tax_id: Optional[uuid.UUID] = None
    price_subtotal: Decimal
    price_tax: Decimal
    price_total: Decimal

class SalesOrderCreate(BaseModel):
    contact_id: uuid.UUID
    lead_id: Optional[uuid.UUID] = None
    salesperson_id: Optional[uuid.UUID] = None
    validity_date: Optional[datetime] = None
    customer_reference: Optional[str] = None
    notes: Optional[str] = None
    lines: List[SalesOrderLineCreate] = Field(default_factory=list)

class SalesOrderUpdate(BaseModel):
    contact_id: Optional[uuid.UUID] = None
    validity_date: Optional[datetime] = None
    customer_reference: Optional[str] = None
    notes: Optional[str] = None
    # Completely replacing lines on update simplifies complex edits
    lines: Optional[List[SalesOrderLineCreate]] = None

class SalesOrderStateUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|sent|confirmed|cancelled)$")

class SalesOrderResponse(OrmBase):
    id: uuid.UUID
    order_number: str
    contact_id: Optional[uuid.UUID] = None
    lead_id: Optional[uuid.UUID] = None
    salesperson_id: Optional[uuid.UUID] = None
    status: str
    order_date: datetime
    validity_date: Optional[datetime] = None
    amount_untaxed: Decimal
    amount_tax: Decimal
    amount_total: Decimal
    customer_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    lines: List[SalesOrderLineResponse] = []

class SalesOrderListResponse(OrmBase):
    id: uuid.UUID
    order_number: str
    contact_id: Optional[uuid.UUID] = None
    salesperson_id: Optional[uuid.UUID] = None
    status: str
    order_date: datetime
    amount_total: Decimal
