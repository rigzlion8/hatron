"""Invoicing Pydantic Schemas."""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.core.schemas import OrmBase

class TaxRuleCreate(BaseModel):
    name: str = Field(..., max_length=255)
    rate: Decimal = Field(..., ge=0, le=100)
    is_active: bool = True

class TaxRuleResponse(OrmBase):
    id: uuid.UUID
    name: str
    rate: Decimal
    is_active: bool


class InvoiceLineCreate(BaseModel):
    product_id: Optional[uuid.UUID] = None
    description: str
    quantity: Decimal = Field(default=Decimal("1.0"), gt=0)
    unit_price: Decimal = Field(default=Decimal(0), ge=0)
    discount: Decimal = Field(default=Decimal(0), ge=0, le=100)
    tax_id: Optional[uuid.UUID] = None

class InvoiceLineResponse(OrmBase):
    id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    tax_id: Optional[uuid.UUID] = None
    price_subtotal: Decimal
    price_tax: Decimal
    price_total: Decimal


class InvoiceCreate(BaseModel):
    contact_id: uuid.UUID
    sales_order_id: Optional[uuid.UUID] = None
    type: str = Field(default="out_invoice", pattern="^(out_invoice|out_refund)$")
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    lines: List[InvoiceLineCreate] = Field(default_factory=list)

class InvoiceUpdate(BaseModel):
    due_date: Optional[date] = None
    notes: Optional[str] = None
    lines: Optional[List[InvoiceLineCreate]] = None

class InvoiceStateUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|open|paid|cancelled)$")


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., max_length=50)
    payment_date: Optional[date] = None
    reference: Optional[str] = None

class PaymentResponse(OrmBase):
    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: Decimal
    payment_method: str
    payment_date: date
    reference: Optional[str] = None
    created_at: datetime


class InvoiceResponse(OrmBase):
    id: uuid.UUID
    invoice_number: str
    contact_id: uuid.UUID
    sales_order_id: Optional[uuid.UUID] = None
    status: str
    type: str
    invoice_date: date
    due_date: Optional[date] = None
    amount_untaxed: Decimal
    amount_tax: Decimal
    amount_total: Decimal
    amount_residual: Decimal
    notes: Optional[str] = None
    created_at: datetime
    lines: List[InvoiceLineResponse] = []
    payments: List[PaymentResponse] = []

class InvoiceListResponse(OrmBase):
    id: uuid.UUID
    invoice_number: str
    contact_id: uuid.UUID
    status: str
    type: str
    invoice_date: date
    due_date: Optional[date] = None
    amount_total: Decimal
    amount_residual: Decimal
