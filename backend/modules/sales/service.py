"""Sales Service."""

import logging
import math
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.events import event_bus
from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.schemas import PaginatedResponse, PaginationMeta
from backend.modules.sales.models import SalesOrder, Product, ProductCategory
from backend.modules.sales.repository import SalesRepository
from backend.modules.sales.schemas import (
    ProductCategoryCreate, ProductCategoryResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    SalesOrderCreate, SalesOrderUpdate, SalesOrderStateUpdate,
    SalesOrderResponse, SalesOrderListResponse
)


class SalesService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SalesRepository(db)


    # ─── Products ───

    async def create_category(self, tenant_id: uuid.UUID, data: ProductCategoryCreate) -> ProductCategoryResponse:
        c = await self.repo.create_category(tenant_id, **data.model_dump())
        c = await self.repo.get_category(c.id, tenant_id)
        return ProductCategoryResponse.model_validate(c)

    async def list_categories(self, tenant_id: uuid.UUID) -> list[ProductCategoryResponse]:
        categories = await self.repo.list_categories(tenant_id)
        return [ProductCategoryResponse.model_validate(c) for c in categories]

    async def create_product(self, tenant_id: uuid.UUID, data: ProductCreate) -> ProductResponse:
        product = await self.repo.create_product(tenant_id, **data.model_dump())
        product = await self.repo.get_product(product.id, tenant_id)
        return ProductResponse.model_validate(product)

    async def get_product(self, product_id: uuid.UUID, tenant_id: uuid.UUID) -> ProductResponse:
        product = await self.repo.get_product(product_id, tenant_id)
        if not product:
            raise NotFoundError("Product", product_id)
        return ProductResponse.model_validate(product)

    async def list_products(
        self, tenant_id: uuid.UUID, page: int = 1, per_page: int = 20, 
        category_id: Optional[uuid.UUID] = None, search: Optional[str] = None
    ) -> PaginatedResponse[ProductResponse]:
        offset = (page - 1) * per_page
        products = await self.repo.list_products(tenant_id, offset, limit=per_page, category_id=category_id, search=search)
        total = await self.repo.count_products(tenant_id, category_id, search)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        
        return PaginatedResponse(
            data=[ProductResponse.model_validate(p) for p in products],
            meta=PaginationMeta(
                total=total, page=page, per_page=per_page, total_pages=total_pages,
                has_next=page < total_pages, has_prev=page > 1
            )
        )

    async def update_product(self, product_id: uuid.UUID, tenant_id: uuid.UUID, data: ProductUpdate) -> ProductResponse:
        product = await self.repo.get_product(product_id, tenant_id)
        if not product:
            raise NotFoundError("Product", product_id)
        product = await self.repo.update_product(product, **data.model_dump(exclude_unset=True))
        product = await self.repo.get_product(product.id, tenant_id)
        return ProductResponse.model_validate(product)


    # ─── Sales Orders ───

    async def _calculate_order_totals(self, tenant_id: uuid.UUID, lines_data: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
        untaxed = Decimal('0.0')
        tax = Decimal('0.0') # Simple tax calculation for Phase 2 (assumes lines include calculated price_tax if applicable, or we inject tax service here. Let's do a basic flat 0 tax unless calculated externally).
        
        for line in lines_data:
            product = await self.repo.get_product(line["product_id"], tenant_id)
            if not product:
                raise ValidationError(f"Invalid product_id: {line['product_id']}")
                
            unit_price = line.get("unit_price")
            if unit_price is None:
                unit_price = product.price
            else:
                unit_price = Decimal(str(unit_price))
                
            qty = Decimal(str(line["quantity"]))
            discount_pct = Decimal(str(line["discount"]))
            
            # Subtotal = qty * unit_price * (1 - discount%)
            subtotal = qty * unit_price * (Decimal('1.0') - discount_pct / Decimal('100.0'))
            
            # Set computed fields
            line["unit_price"] = unit_price
            line["description"] = line.get("description") or product.name
            line["price_subtotal"] = subtotal
            line["price_tax"] = Decimal('0.0')
            line["price_total"] = subtotal
            
            untaxed += subtotal
            
        return untaxed, tax, untaxed + tax

    async def create_order(self, tenant_id: uuid.UUID, created_by: uuid.UUID, data: SalesOrderCreate) -> SalesOrderResponse:
        order_data = data.model_dump(exclude={"lines"})
        lines_data = data.model_dump()["lines"]
        
        # Calculate totals safely with Decimal
        untaxed, tax, total = await self._calculate_order_totals(tenant_id, lines_data)
        
        order_data["amount_untaxed"] = untaxed
        order_data["amount_tax"] = tax
        order_data["amount_total"] = total
        
        order = await self.repo.create_order(tenant_id, created_by, lines_data, **order_data)
        order = await self.repo.get_order(order.id, tenant_id)
        return SalesOrderResponse.model_validate(order)

    async def get_order(self, order_id: uuid.UUID, tenant_id: uuid.UUID) -> SalesOrderResponse:
        order = await self.repo.get_order(order_id, tenant_id)
        if not order:
            raise NotFoundError("SalesOrder", order_id)
        return SalesOrderResponse.model_validate(order)

    async def list_orders(
        self, tenant_id: uuid.UUID, page: int = 1, per_page: int = 20, 
        contact_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> PaginatedResponse[SalesOrderListResponse]:
        offset = (page - 1) * per_page
        orders = await self.repo.list_orders(tenant_id, offset, limit=per_page, contact_id=contact_id, status=status)
        total = await self.repo.count_orders(tenant_id, contact_id, status)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        
        return PaginatedResponse(
            data=[SalesOrderListResponse.model_validate(o) for o in orders],
            meta=PaginationMeta(
                total=total, page=page, per_page=per_page, total_pages=total_pages,
                has_next=page < total_pages, has_prev=page > 1
            )
        )

    async def update_order(self, order_id: uuid.UUID, tenant_id: uuid.UUID, data: SalesOrderUpdate) -> SalesOrderResponse:
        order = await self.repo.get_order(order_id, tenant_id)
        if not order:
            raise NotFoundError("SalesOrder", order_id)
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
        return SalesOrderResponse.model_validate(order)

    async def confirm_order(self, order_id: uuid.UUID, tenant_id: uuid.UUID) -> SalesOrderResponse:
        order = await self.repo.get_order(order_id, tenant_id)
        if not order:
            raise NotFoundError("SalesOrder", order_id)
            
        if order.status not in ("draft", "sent"):
            raise ValidationError(f"Cannot confirm order in {order.status} state")
            
        order = await self.repo.update_order(order, status="confirmed")
        order = await self.repo.get_order(order.id, tenant_id)

        # Try local invoice generation as immediate fallback (no Celery dependency).
        try:
            from backend.modules.invoicing.service import InvoicingService
            invoice_service = InvoicingService(self.db)
            await invoice_service.create_invoice_from_order(order)
        except Exception as e:
            # Keep existing event bus logic for asynchronous processing.
            # If local generation fails (e.g. missing dependency), let event bus try.
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed create invoice directly from order {order_id}: {e}")

        # Publish event for other system subscribers
        await event_bus.publish("sales.order.confirmed", {
            "order_id": str(order.id),
            "tenant_id": str(tenant_id)
        })

        return SalesOrderResponse.model_validate(order)
