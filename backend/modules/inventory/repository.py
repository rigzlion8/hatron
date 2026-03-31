"""Inventory Repository."""

import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.inventory.models import (
    Warehouse, StockLocation, StockQuant, StockPicking, StockMove
)


class InventoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Warehouses & Locations ───
    async def create_warehouse(self, tenant_id: uuid.UUID, **kwargs) -> Warehouse:
        warehouse = Warehouse(tenant_id=tenant_id, **kwargs)
        self.db.add(warehouse)
        await self.db.flush()
        return warehouse

    async def get_warehouse(self, warehouse_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Warehouse]:
        stmt = select(Warehouse).where(
            Warehouse.id == warehouse_id, Warehouse.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_warehouses(self, tenant_id: uuid.UUID) -> list[Warehouse]:
        stmt = select(Warehouse).where(Warehouse.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_location(self, tenant_id: uuid.UUID, **kwargs) -> StockLocation:
        loc = StockLocation(tenant_id=tenant_id, **kwargs)
        self.db.add(loc)
        await self.db.flush()
        return loc

    async def get_location_by_type(self, tenant_id: uuid.UUID, loc_type: str) -> Optional[StockLocation]:
        stmt = select(StockLocation).where(
            StockLocation.tenant_id == tenant_id, StockLocation.type == loc_type
        ).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_locations(self, tenant_id: uuid.UUID) -> list[StockLocation]:
        stmt = select(StockLocation).where(StockLocation.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    # ─── Quants ───
    async def get_quant(self, product_id: uuid.UUID, location_id: uuid.UUID, tenant_id: uuid.UUID) -> StockQuant:
        """Get quant, or create empty if doesn't exist."""
        stmt = select(StockQuant).where(
            StockQuant.product_id == product_id,
            StockQuant.location_id == location_id,
            StockQuant.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        quant = result.scalar_one_or_none()
        
        if not quant:
            quant = StockQuant(
                tenant_id=tenant_id, product_id=product_id, location_id=location_id, quantity=0.0
            )
            self.db.add(quant)
            await self.db.flush()
            
        return quant

    async def update_quant(self, quant: StockQuant, delta: float) -> StockQuant:
        """Add delta to quant."""
        quant.quantity = float(quant.quantity) + delta
        await self.db.flush()
        return quant

    async def list_quants(self, tenant_id: uuid.UUID, location_id: Optional[uuid.UUID] = None) -> list[StockQuant]:
        """List all stock quants for a tenant, optionally filtered by location."""
        stmt = select(StockQuant).where(StockQuant.tenant_id == tenant_id)
        if location_id:
            stmt = stmt.where(StockQuant.location_id == location_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    # ─── Pickings ───
    async def generate_picking_number(self, tenant_id: uuid.UUID, pick_type: str) -> str:
        stmt = select(func.count(StockPicking.id)).where(
            StockPicking.tenant_id == tenant_id, StockPicking.type == pick_type
        )
        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        prefix = "IN" if pick_type == "incoming" else "OUT" if pick_type == "outgoing" else "INT"
        return f"{prefix}-{count + 1:05d}"

    async def create_picking(self, tenant_id: uuid.UUID, created_by: uuid.UUID, lines: list[dict], **kwargs) -> StockPicking:
        pick_num = await self.generate_picking_number(tenant_id, kwargs.get("type", "internal"))
        picking = StockPicking(tenant_id=tenant_id, created_by=created_by, picking_number=pick_num, **kwargs)
        self.db.add(picking)
        await self.db.flush()
        
        for line_data in lines:
            move = StockMove(tenant_id=tenant_id, picking_id=picking.id, **line_data)
            self.db.add(move)
        await self.db.flush()
        return picking

    async def get_picking(self, picking_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[StockPicking]:
        stmt = select(StockPicking).options(selectinload(StockPicking.moves)).where(
            StockPicking.id == picking_id, StockPicking.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pickings(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20, 
        pick_type: Optional[str] = None, status: Optional[str] = None
    ) -> list[StockPicking]:
        stmt = select(StockPicking).where(StockPicking.tenant_id == tenant_id)
        if pick_type:
            stmt = stmt.where(StockPicking.type == pick_type)
        if status:
            stmt = stmt.where(StockPicking.status == status)
            
        stmt = stmt.order_by(StockPicking.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_pickings(self, tenant_id: uuid.UUID, pick_type: Optional[str] = None, status: Optional[str] = None) -> int:
        stmt = select(func.count(StockPicking.id)).where(StockPicking.tenant_id == tenant_id)
        if pick_type:
            stmt = stmt.where(StockPicking.type == pick_type)
        if status:
            stmt = stmt.where(StockPicking.status == status)
            
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_move(self, move_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[StockMove]:
        stmt = select(StockMove).where(StockMove.id == move_id, StockMove.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_move(self, move: StockMove, **kwargs) -> StockMove:
        for k, v in kwargs.items():
            if hasattr(move, k) and v is not None:
                setattr(move, k, v)
        await self.db.flush()
        return move

    async def update_picking(self, picking: StockPicking, **kwargs) -> StockPicking:
        for k, v in kwargs.items():
            if hasattr(picking, k) and v is not None:
                setattr(picking, k, v)
        await self.db.flush()
        return picking
