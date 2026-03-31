"""Purchase Service."""

import math
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.events import event_bus
from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.schemas import PaginatedResponse, PaginationMeta
from backend.modules.purchase.models import PurchaseOrder
from backend.modules.purchase.repository import PurchaseRepository
from backend.modules.purchase.schemas import (
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderStateUpdate,
    PurchaseOrderResponse, PurchaseOrderListResponse
)
# Intentionally avoiding cross importing models directly for logic separation where possible
from backend.modules.sales.repository import SalesRepository # To fetch product costs


class PurchaseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PurchaseRepository(db)
        self.sales_repo = SalesRepository(db)

    async def _calculate_order_totals(self, tenant_id: uuid.UUID, lines_data: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
        untaxed = Decimal('0.0')
        tax = Decimal('0.0')
        
        for line in lines_data:
            product = await self.sales_repo.get_product(line["product_id"], tenant_id)
            if not product:
                raise ValidationError(f"Invalid product_id: {line['product_id']}")
                
            unit_price = line.get("unit_price")
            if unit_price is None:
                unit_price = product.cost # Purchases evaluate standard cost
            else:
                unit_price = Decimal(str(unit_price))
                
            qty = Decimal(str(line["quantity"]))
            
            subtotal = qty * unit_price
            
            line["unit_price"] = unit_price
            line["description"] = line.get("description") or product.name
            line["price_subtotal"] = subtotal
            line["price_tax"] = Decimal('0.0')
            line["price_total"] = subtotal
            
            untaxed += subtotal
            
        return untaxed, tax, untaxed + tax

    async def create_order(self, tenant_id: uuid.UUID, created_by: uuid.UUID, data: PurchaseOrderCreate) -> PurchaseOrderResponse:
        order_data = data.model_dump(exclude={"lines"})
        lines_data = data.model_dump()["lines"]
        
        untaxed, tax, total = await self._calculate_order_totals(tenant_id, lines_data)
        
        order_data["amount_untaxed"] = untaxed
        order_data["amount_tax"] = tax
        order_data["amount_total"] = total
        
        order = await self.repo.create_order(tenant_id, created_by, lines_data, **order_data)
        order = await self.repo.get_order(order.id, tenant_id)
        return PurchaseOrderResponse.model_validate(order)

    async def get_order(self, order_id: uuid.UUID, tenant_id: uuid.UUID) -> PurchaseOrderResponse:
        order = await self.repo.get_order(order_id, tenant_id)
        if not order:
            raise NotFoundError("PurchaseOrder", order_id)
        return PurchaseOrderResponse.model_validate(order)

    async def list_orders(
        self, tenant_id: uuid.UUID, page: int = 1, per_page: int = 20, 
        vendor_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> PaginatedResponse[PurchaseOrderListResponse]:
        offset = (page - 1) * per_page
        orders = await self.repo.list_orders(tenant_id, offset, limit=per_page, vendor_id=vendor_id, status=status)
        total = await self.repo.count_orders(tenant_id, vendor_id, status)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        
        return PaginatedResponse(
            data=[PurchaseOrderListResponse.model_validate(o) for o in orders],
            meta=PaginationMeta(
                total=total, page=page, per_page=per_page, total_pages=total_pages,
                has_next=page < total_pages, has_prev=page > 1
            )
        )

    async def update_order(self, order_id: uuid.UUID, tenant_id: uuid.UUID, data: PurchaseOrderUpdate) -> PurchaseOrderResponse:
        order = await self.repo.get_order(order_id, tenant_id)
        if not order:
            raise NotFoundError("PurchaseOrder", order_id)
        if order.status != "draft":
            raise ValidationError("Cannot update a confirmed or sent order")
            
        update_data = data.model_dump(exclude_unset=True, exclude={"lines"})
        lines_data = data.model_dump(exclude_unset=True).get("lines")
        
        if lines_data is not None:
            untaxed, tax, total = await self._calculate_order_totals(tenant_id, lines_data)
            update_data["amount_untaxed"] = untaxed
            update_data["amount_tax"] = tax
            update_data["amount_total"] = total
            
        order = await self.repo.update_order(order, lines=lines_data, **update_data)
        order = await self.repo.get_order(order.id, tenant_id)
        return PurchaseOrderResponse.model_validate(order)

    async def confirm_order(self, order_id: uuid.UUID, tenant_id: uuid.UUID) -> PurchaseOrderResponse:
        order = await self.repo.get_order(order_id, tenant_id)
        if not order:
            raise NotFoundError("PurchaseOrder", order_id)
            
        if order.status not in ("draft", "sent"):
            raise ValidationError(f"Cannot confirm order in {order.status} state")
            
        order = await self.repo.update_order(order, status="confirmed")
        order = await self.repo.get_order(order.id, tenant_id)
        
        # PUBLISH EVENT FOR INVENTORY AND INVOICING MODULES TO LISTEN TO!
        await event_bus.publish("purchase.order.confirmed", {
            "order_id": str(order.id),
            "tenant_id": str(tenant_id)
        })
        
        return PurchaseOrderResponse.model_validate(order)
