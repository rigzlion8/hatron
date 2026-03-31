"""POS (Point of Sale) Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from backend.core.schemas import OrmBase


# ─── Setup Schemas ───

class POSSetupRequest(BaseModel):
    """Initial setup for POS (Demo vs. Clean)."""
    mode: str = Field(..., description="demo or clean")


# ─── Session Schemas ───

class POSSessionCreate(BaseModel):
    """Request to open a new POS session."""
    name: str = Field(..., min_length=1, max_length=100)
    opening_balance: float = 0.0


class POSSessionResponse(OrmBase):
    """Response representing a POS session."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    start_at: datetime
    stop_at: Optional[datetime] = None
    status: str
    opening_balance: float
    closing_balance: Optional[float] = None


# ─── Order Schemas ───

class POSOrderLineCreate(BaseModel):
    """Line item for order creation."""
    product_id: uuid.UUID
    quantity: float
    unit_price: float
    price_subtotal: float


class POSOrderCreate(BaseModel):
    """Request to sync a POS order."""
    session_id: uuid.UUID
    order_reference: str
    contact_id: Optional[uuid.UUID] = None
    amount_total: float
    amount_tax: float
    amount_paid: float
    amount_return: float
    payment_method: str = "cash"
    lines: List[POSOrderLineCreate]


class POSOrderResponse(OrmBase):
    """Response representing a POS order."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    session_id: uuid.UUID
    order_reference: str
    amount_total: float
    created_at: datetime
    payment_method: str


class POSProductResponse(OrmBase):
    """Subset of Product data for POS display."""
    id: uuid.UUID
    name: str
    price: float
    sku: Optional[str] = None
    image_url: Optional[str] = None
    category_name: Optional[str] = None


# ─── Payment Schemas ───

class MpesaSTKPushRequest(BaseModel):
    """Request to initiate M-Pesa STK Push."""
    phone_number: str = Field(..., description="Phone number in 254XXXXXXXXX format")
    amount: float = Field(..., gt=0)
    order_reference: str = Field(..., min_length=1)


class MpesaSTKPushResponse(BaseModel):
    """Response from M-Pesa STK Push initiation."""
    success: bool
    checkout_request_id: Optional[str] = None
    merchant_request_id: Optional[str] = None
    response_description: Optional[str] = None
    error: Optional[str] = None


class MpesaStatusRequest(BaseModel):
    """Request to check M-Pesa payment status."""
    checkout_request_id: str


class PaystackInitRequest(BaseModel):
    """Request to initialize Paystack payment."""
    email: str = Field(..., description="Customer email for Paystack")
    amount: float = Field(..., gt=0)
    reference: str = Field(..., min_length=1)
    callback_url: Optional[str] = None


class PaystackInitResponse(BaseModel):
    """Response from Paystack initialization."""
    success: bool
    authorization_url: Optional[str] = None
    access_code: Optional[str] = None
    reference: Optional[str] = None
    error: Optional[str] = None


class PaystackVerifyResponse(BaseModel):
    """Response from Paystack verification."""
    success: bool
    status: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    reference: Optional[str] = None
    error: Optional[str] = None
