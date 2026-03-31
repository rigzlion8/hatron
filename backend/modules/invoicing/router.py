"""Invoicing API Router."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user, get_db
from backend.core.schemas import PaginatedResponse
from backend.modules.auth.models import User
from backend.modules.invoicing.schemas import (
    TaxRuleCreate, TaxRuleResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceStateUpdate,
    InvoiceResponse, InvoiceListResponse,
    PaymentCreate, PaymentResponse
)
from backend.modules.invoicing.service import InvoicingService

router = APIRouter(prefix="/invoicing", tags=["Invoicing"])

# ─── Taxes ───

@router.post("/taxes", response_model=TaxRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_tax(
    data: TaxRuleCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = InvoicingService(db)
    return await service.create_tax_rule(current_user.tenant_id, data)

@router.get("/taxes", response_model=list[TaxRuleResponse])
async def list_taxes(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = InvoicingService(db)
    return await service.list_tax_rules(current_user.tenant_id)


# ─── Invoices ───

@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = InvoicingService(db)
    return await service.create_invoice(current_user.tenant_id, current_user.id, data)

@router.get("/invoices", response_model=PaginatedResponse[InvoiceListResponse])
async def list_invoices(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    contact_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InvoicingService(db)
    return await service.list_invoices(
        current_user.tenant_id, page=page, per_page=per_page, 
        contact_id=contact_id, status=status
    )

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InvoicingService(db)
    return await service.get_invoice(invoice_id, current_user.tenant_id)

@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InvoicingService(db)
    return await service.update_invoice(invoice_id, current_user.tenant_id, data)

@router.patch("/invoices/{invoice_id}/state", response_model=InvoiceResponse)
async def update_invoice_state(
    invoice_id: uuid.UUID,
    data: InvoiceStateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InvoicingService(db)
    return await service.update_state(invoice_id, current_user.tenant_id, data.status)


# ─── Payments ───

@router.post("/invoices/{invoice_id}/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    invoice_id: uuid.UUID,
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InvoicingService(db)
    return await service.create_payment(invoice_id, current_user.tenant_id, data)
