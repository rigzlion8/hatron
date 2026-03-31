"""Purchase Schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.core.schemas import OrmBase


class PurchaseOrderLineCreate(BaseModel):
    product_id: uuid.UUID
    description: Optional[str] = None
    quantity: Decimal = Field(default=Decimal("1.0"), gt=0)
    unit_price: Optional[Decimal] = None # Fallback to product.cost
    tax_id: Optional[uuid.UUID] = None

class PurchaseOrderLineResponse(OrmBase):
    id: uuid.UUID
    product_id: uuid.UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_id: Optional[uuid.UUID] = None
    price_subtotal: Decimal
    price_tax: Decimal
    price_total: Decimal

class PurchaseOrderCreate(BaseModel):
    vendor_id: uuid.UUID
    buyer_id: Optional[uuid.UUID] = None
    receipt_date: Optional[datetime] = None
    vendor_reference: Optional[str] = None
    notes: Optional[str] = None
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)

class PurchaseOrderUpdate(BaseModel):
    vendor_id: Optional[uuid.UUID] = None
    receipt_date: Optional[datetime] = None
    vendor_reference: Optional[str] = None
    notes: Optional[str] = None
    lines: Optional[List[PurchaseOrderLineCreate]] = None

class PurchaseOrderStateUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|sent|confirmed|cancelled|done)$")

class PurchaseOrderResponse(OrmBase):
    id: uuid.UUID
    order_number: str
    vendor_id: uuid.UUID
    buyer_id: Optional[uuid.UUID] = None
    status: str
    order_date: datetime
    receipt_date: Optional[datetime] = None
    amount_untaxed: Decimal
    amount_tax: Decimal
    amount_total: Decimal
    vendor_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    lines: List[PurchaseOrderLineResponse] = []

class PurchaseOrderListResponse(OrmBase):
    id: uuid.UUID
    order_number: str
    vendor_id: uuid.UUID
    buyer_id: Optional[uuid.UUID] = None
    status: str
    order_date: datetime
    amount_total: Decimal
