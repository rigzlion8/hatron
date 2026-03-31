"""Purchase API Router."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user, get_db
from backend.core.schemas import PaginatedResponse
from backend.modules.auth.models import User
from backend.modules.purchase.schemas import (
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderStateUpdate,
    PurchaseOrderResponse, PurchaseOrderListResponse
)
from backend.modules.purchase.service import PurchaseService

router = APIRouter(prefix="/purchase", tags=["Purchase"])

@router.post("/orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: PurchaseOrderCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = PurchaseService(db)
    return await service.create_order(current_user.tenant_id, current_user.id, data)

@router.get("/orders", response_model=PaginatedResponse[PurchaseOrderListResponse])
async def list_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    vendor_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = PurchaseService(db)
    return await service.list_orders(
        current_user.tenant_id, page=page, per_page=per_page, 
        vendor_id=vendor_id, status=status
    )

@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = PurchaseService(db)
    return await service.get_order(order_id, current_user.tenant_id)

@router.patch("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def update_order(
    order_id: uuid.UUID,
    data: PurchaseOrderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = PurchaseService(db)
    return await service.update_order(order_id, current_user.tenant_id, data)

@router.post("/orders/{order_id}/confirm", response_model=PurchaseOrderResponse)
async def confirm_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = PurchaseService(db)
    return await service.confirm_order(order_id, current_user.tenant_id)
