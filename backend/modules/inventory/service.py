"""Inventory Service & Event Handlers."""

import math
import uuid
import datetime
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.events import event_bus
from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.schemas import PaginatedResponse, PaginationMeta
from backend.modules.inventory.models import StockPicking
from backend.modules.inventory.repository import InventoryRepository
from backend.modules.inventory.schemas import (
    WarehouseCreate, WarehouseResponse,
    StockLocationCreate, StockLocationResponse,
    StockQuantResponse,
    StockMoveUpdate, StockMoveResponse,
    StockPickingCreate, StockPickingResponse, StockPickingListResponse
)


class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = InventoryRepository(db)


    # ─── Warehouses & Locations ───

    async def create_warehouse(self, tenant_id: uuid.UUID, data: WarehouseCreate) -> WarehouseResponse:
        w_data = data.model_dump()
        w = await self.repo.create_warehouse(tenant_id, **w_data)
        
        # Auto-create the main internal stock location for this warehouse
        await self.repo.create_location(
            tenant_id=tenant_id,
            name=f"{w.code} Stock",
            warehouse_id=w.id,
            type="internal"
        )
        
        return WarehouseResponse.model_validate(w)

    async def list_warehouses(self, tenant_id: uuid.UUID) -> list[WarehouseResponse]:
        warehouses = await self.repo.list_warehouses(tenant_id)
        return [WarehouseResponse.model_validate(w) for w in warehouses]

    async def create_location(self, tenant_id: uuid.UUID, data: StockLocationCreate) -> StockLocationResponse:
        loc = await self.repo.create_location(tenant_id, **data.model_dump())
        return StockLocationResponse.model_validate(loc)

    async def list_locations(self, tenant_id: uuid.UUID) -> list[StockLocationResponse]:
        locs = await self.repo.list_locations(tenant_id)
        return [StockLocationResponse.model_validate(l) for l in locs]

    async def list_quants(self, tenant_id: uuid.UUID, location_id: Optional[uuid.UUID] = None) -> list[StockQuantResponse]:
        quants = await self.repo.list_quants(tenant_id, location_id)
        return [StockQuantResponse.model_validate(q) for q in quants]


    # ─── Pickings & Moves ───

    async def create_picking(self, tenant_id: uuid.UUID, created_by: uuid.UUID, data: StockPickingCreate) -> StockPickingResponse:
        pick_data = data.model_dump(exclude={"lines"})
        lines_data = data.model_dump()["lines"]
        
        picking = await self.repo.create_picking(tenant_id, created_by, lines_data, **pick_data)
        picking = await self.repo.get_picking(picking.id, tenant_id)
        return StockPickingResponse.model_validate(picking)

    async def list_pickings(
        self, tenant_id: uuid.UUID, page: int = 1, per_page: int = 20, 
        pick_type: Optional[str] = None, status: Optional[str] = None
    ) -> PaginatedResponse[StockPickingListResponse]:
        offset = (page - 1) * per_page
        pickings = await self.repo.list_pickings(tenant_id, offset, limit=per_page, pick_type=pick_type, status=status)
        total = await self.repo.count_pickings(tenant_id, pick_type, status)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        
        return PaginatedResponse(
            data=[StockPickingListResponse.model_validate(p) for p in pickings],
            meta=PaginationMeta(
                total=total, page=page, per_page=per_page, total_pages=total_pages,
                has_next=page < total_pages, has_prev=page > 1
            )
        )

    async def get_picking(self, picking_id: uuid.UUID, tenant_id: uuid.UUID) -> StockPickingResponse:
        picking = await self.repo.get_picking(picking_id, tenant_id)
        if not picking:
            raise NotFoundError("StockPicking", picking_id)
        return StockPickingResponse.model_validate(picking)

    async def update_move_quantity(self, move_id: uuid.UUID, tenant_id: uuid.UUID, done_qty: float) -> StockMoveResponse:
        move = await self.repo.get_move(move_id, tenant_id)
        if not move:
            raise NotFoundError("StockMove", move_id)
            
        move = await self.repo.update_move(move, quantity_done=done_qty)
        return StockMoveResponse.model_validate(move)

    async def validate_picking(self, picking_id: uuid.UUID, tenant_id: uuid.UUID) -> StockPickingResponse:
        """Confirm a shipment. This is the core double-entry inventory engine."""
        picking = await self.repo.get_picking(picking_id, tenant_id)
        if not picking:
            raise NotFoundError("StockPicking", picking_id)
            
        if picking.status == "done":
            raise ValidationError("Picking is already done")
            
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Process every move
        for move in picking.moves:
            qty_to_process = move.quantity_done
            if qty_to_process <= 0:
                continue # Skip processing empty lines
                
            # Double entry stock movement
            # 1. Decrease source location
            src_quant = await self.repo.get_quant(move.product_id, move.location_id, tenant_id)
            await self.repo.update_quant(src_quant, -qty_to_process)
            
            # 2. Increase destination location
            dest_quant = await self.repo.get_quant(move.product_id, move.location_dest_id, tenant_id)
            await self.repo.update_quant(dest_quant, qty_to_process)
            
            # Mark move as done
            move = await self.repo.update_move(move, status="done", date_done=now)
            
        # Update Picking
        picking = await self.repo.update_picking(picking, status="done", date_done=now)
        
        return StockPickingResponse.model_validate(picking)


# ─── Event Subscriptions ───

async def generate_delivery_from_sales_order(data: dict):
    """Event handler for sales.order.confirmed -> Creates outgoing Delivery Order."""
    from backend.core.database import async_session_factory
    from backend.modules.sales.repository import SalesRepository
    
    order_id = uuid.UUID(data["order_id"])
    tenant_id = uuid.UUID(data["tenant_id"])
    
    async with async_session_factory() as db:
        try:
            sales_repo = SalesRepository(db)
            inv_repo = InventoryRepository(db)
            
            order = await sales_repo.get_order(order_id, tenant_id)
            if not order:
                return
                
            # Need source and dest locations
            cust_loc = await inv_repo.get_location_by_type(tenant_id, "customer")
            stock_loc = await inv_repo.get_location_by_type(tenant_id, "internal") # Grab first internal
            
            if not cust_loc or not stock_loc:
                logging.getLogger("erp.events").error(
                    f"Failed to generate delivery for SO {order_id}: Source (internal) or Destination (customer) location not found."
                )
                return
                
            inv_service = InventoryService(db)
            
            lines = []
            for line in order.lines:
                lines.append({
                    "name": line.description,
                    "product_id": line.product_id,
                    "location_id": stock_loc.id,
                    "location_dest_id": cust_loc.id,
                    "quantity": line.quantity,
                    "quantity_done": 0.0 # user has to manually validate it
                })
                
            pick_data = StockPickingCreate(
                type="outgoing",
                location_id=stock_loc.id,
                location_dest_id=cust_loc.id,
                origin=order.order_number,
                contact_id=order.contact_id,
                lines=lines
            )
            
            await inv_service.create_picking(
                tenant_id=tenant_id,
                created_by=order.created_by,
                data=pick_data
            )
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logging.getLogger("erp.events").error(f"Failed to generate delivery for SO {order_id}: {e}")

async def generate_receipt_from_purchase_order(data: dict):
    """Event handler for purchase.order.confirmed -> Creates incoming Receipt."""
    from backend.core.database import async_session_factory
    from backend.modules.purchase.repository import PurchaseRepository
    
    order_id = uuid.UUID(data["order_id"])
    tenant_id = uuid.UUID(data["tenant_id"])
    
    async with async_session_factory() as db:
        try:
            purchase_repo = PurchaseRepository(db)
            inv_repo = InventoryRepository(db)
            
            order = await purchase_repo.get_order(order_id, tenant_id)
            if not order:
                return
                
            vendor_loc = await inv_repo.get_location_by_type(tenant_id, "vendor")
            stock_loc = await inv_repo.get_location_by_type(tenant_id, "internal")
            
            if not vendor_loc or not stock_loc:
                logging.getLogger("erp.events").error(
                    f"Failed to generate receipt for PO {order_id}: Source (vendor) or Destination (internal) location not found."
                )
                return
                
            inv_service = InventoryService(db)
            
            lines = []
            for line in order.lines:
                lines.append({
                    "name": line.description,
                    "product_id": line.product_id,
                    "location_id": vendor_loc.id,
                    "location_dest_id": stock_loc.id,
                    "quantity": line.quantity,
                    "quantity_done": 0.0
                })
                
            pick_data = StockPickingCreate(
                type="incoming",
                location_id=vendor_loc.id,
                location_dest_id=stock_loc.id,
                origin=order.order_number,
                contact_id=order.vendor_id,
                lines=lines
            )
            
            await inv_service.create_picking(
                tenant_id=tenant_id,
                created_by=order.created_by,
                data=pick_data
            )
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logging.getLogger("erp.events").error(f"Failed to generate receipt for PO {order_id}: {e}")

# Register listeners
event_bus.subscribe("sales.order.confirmed", generate_delivery_from_sales_order)
event_bus.subscribe("purchase.order.confirmed", generate_receipt_from_purchase_order)

