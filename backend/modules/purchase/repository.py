"""Purchase Repository."""

import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.purchase.models import PurchaseOrder, PurchaseOrderLine

class PurchaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_order_number(self, tenant_id: uuid.UUID) -> str:
        stmt = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        return f"PO-{count + 1:05d}"
        
    async def create_order(self, tenant_id: uuid.UUID, created_by: uuid.UUID, lines: list[dict], **kwargs) -> PurchaseOrder:
        order_num = await self.generate_order_number(tenant_id)
        order = PurchaseOrder(tenant_id=tenant_id, created_by=created_by, order_number=order_num, **kwargs)
        self.db.add(order)
        await self.db.flush()
        
        for line_data in lines:
            line = PurchaseOrderLine(tenant_id=tenant_id, order_id=order.id, **line_data)
            self.db.add(line)
        await self.db.flush()
        return order
        
    async def get_order(self, order_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[PurchaseOrder]:
        stmt = select(PurchaseOrder).options(selectinload(PurchaseOrder.lines)).where(
            PurchaseOrder.id == order_id, PurchaseOrder.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_orders(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20, 
        vendor_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> list[PurchaseOrder]:
        stmt = select(PurchaseOrder).where(PurchaseOrder.tenant_id == tenant_id)
        if vendor_id:
            stmt = stmt.where(PurchaseOrder.vendor_id == vendor_id)
        if status:
            stmt = stmt.where(PurchaseOrder.status == status)
            
        stmt = stmt.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
        
    async def count_orders(
        self, tenant_id: uuid.UUID, vendor_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> int:
        stmt = select(func.count(PurchaseOrder.id)).where(PurchaseOrder.tenant_id == tenant_id)
        if vendor_id:
            stmt = stmt.where(PurchaseOrder.vendor_id == vendor_id)
        if status:
            stmt = stmt.where(PurchaseOrder.status == status)
            
        result = await self.db.execute(stmt)
        return result.scalar() or 0
        
    async def update_order(self, order: PurchaseOrder, lines: Optional[list[dict]] = None, **kwargs) -> PurchaseOrder:
        for k, v in kwargs.items():
            if hasattr(order, k) and v is not None:
                setattr(order, k, v)
                
        if lines is not None:
            from sqlalchemy import delete
            await self.db.execute(delete(PurchaseOrderLine).where(PurchaseOrderLine.order_id == order.id))
            
            for line_data in lines:
                line = PurchaseOrderLine(tenant_id=order.tenant_id, order_id=order.id, **line_data)
                self.db.add(line)
                
        await self.db.flush()
        return order
