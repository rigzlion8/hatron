"""Inventory module API Router."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user, get_db
from backend.core.schemas import PaginatedResponse
from backend.modules.auth.models import User
from backend.modules.inventory.schemas import (
    WarehouseCreate, WarehouseResponse,
    StockLocationCreate, StockLocationResponse,
    StockQuantResponse,
    StockPickingCreate, StockPickingResponse, StockPickingListResponse,
    StockMoveUpdate, StockMoveResponse
)
from backend.modules.inventory.service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ─── Warehouses & Locations ───

@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = InventoryService(db)
    return await service.create_warehouse(current_user.tenant_id, data)

@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = InventoryService(db)
    return await service.list_warehouses(current_user.tenant_id)


@router.post("/locations", response_model=StockLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    data: StockLocationCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = InventoryService(db)
    return await service.create_location(current_user.tenant_id, data)

@router.get("/locations", response_model=list[StockLocationResponse])
async def list_locations(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = InventoryService(db)
    return await service.list_locations(current_user.tenant_id)

@router.get("/quants", response_model=list[StockQuantResponse])
async def list_quants(
    location_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = InventoryService(db)
    return await service.list_quants(current_user.tenant_id, location_id)

# ─── Pickings & Transfers ───

@router.post("/pickings", response_model=StockPickingResponse, status_code=status.HTTP_201_CREATED)
async def create_picking(
    data: StockPickingCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = InventoryService(db)
    return await service.create_picking(current_user.tenant_id, current_user.id, data)

@router.get("/pickings", response_model=PaginatedResponse[StockPickingListResponse])
async def list_pickings(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    pick_type: Optional[str] = None,
    pick_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InventoryService(db)
    return await service.list_pickings(
        current_user.tenant_id, page=page, per_page=per_page, 
        pick_type=pick_type, status=pick_status
    )

@router.get("/pickings/{picking_id}", response_model=StockPickingResponse)
async def get_picking(
    picking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InventoryService(db)
    return await service.get_picking(picking_id, current_user.tenant_id)

@router.patch("/moves/{move_id}", response_model=StockMoveResponse)
async def update_move_done_quantity(
    move_id: uuid.UUID,
    data: StockMoveUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InventoryService(db)
    return await service.update_move_quantity(move_id, current_user.tenant_id, float(data.quantity_done))

@router.post("/pickings/{picking_id}/validate", response_model=StockPickingResponse)
async def validate_picking(
    picking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Marks moves as done and performs double-entry quant adjustments."""
    service = InventoryService(db)
    return await service.validate_picking(picking_id, current_user.tenant_id)
