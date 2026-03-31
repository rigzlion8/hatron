"""Sales Repository."""

import uuid
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.sales.models import (
    ProductCategory, Product, SalesOrder, SalesOrderLine
)


class SalesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Products & Categories ───
    async def create_category(self, tenant_id: uuid.UUID, **kwargs) -> ProductCategory:
        cat = ProductCategory(tenant_id=tenant_id, **kwargs)
        self.db.add(cat)
        await self.db.flush()
        return cat
        
    async def get_category(self, category_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[ProductCategory]:
        stmt = select(ProductCategory).where(
            ProductCategory.id == category_id, ProductCategory.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_categories(self, tenant_id: uuid.UUID) -> list[ProductCategory]:
        stmt = select(ProductCategory).where(ProductCategory.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_product(self, tenant_id: uuid.UUID, **kwargs) -> Product:
        product = Product(tenant_id=tenant_id, **kwargs)
        self.db.add(product)
        await self.db.flush()
        return product

    async def get_product(self, product_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Product]:
        stmt = select(Product).options(selectinload(Product.category)).where(
            Product.id == product_id, Product.tenant_id == tenant_id, Product.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def list_products(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20, 
        category_id: Optional[uuid.UUID] = None, search: Optional[str] = None
    ) -> list[Product]:
        stmt = select(Product).options(selectinload(Product.category)).where(
            Product.tenant_id == tenant_id, Product.is_deleted == False
        )
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        if search:
            stmt = stmt.where(or_(Product.name.ilike(f"%{search}%"), Product.sku.ilike(f"%{search}%")))
            
        stmt = stmt.order_by(Product.name).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_products(
        self, tenant_id: uuid.UUID, category_id: Optional[uuid.UUID] = None, search: Optional[str] = None
    ) -> int:
        stmt = select(func.count(Product.id)).where(Product.tenant_id == tenant_id, Product.is_deleted == False)
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        if search:
            stmt = stmt.where(or_(Product.name.ilike(f"%{search}%"), Product.sku.ilike(f"%{search}%")))
            
        result = await self.db.execute(stmt)
        return result.scalar() or 0
        
    async def update_product(self, product: Product, **kwargs) -> Product:
        for k, v in kwargs.items():
            if hasattr(product, k) and v is not None:
                setattr(product, k, v)
        await self.db.flush()
        return product


    # ─── Sales Orders ───
    async def generate_order_number(self, tenant_id: uuid.UUID) -> str:
        stmt = select(func.count(SalesOrder.id)).where(SalesOrder.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        return f"SO-{count + 1:05d}"
        
    async def create_order(self, tenant_id: uuid.UUID, created_by: uuid.UUID, lines: list[dict], **kwargs) -> SalesOrder:
        order_num = await self.generate_order_number(tenant_id)
        order = SalesOrder(tenant_id=tenant_id, created_by=created_by, order_number=order_num, **kwargs)
        self.db.add(order)
        await self.db.flush()
        
        for line_data in lines:
            line = SalesOrderLine(tenant_id=tenant_id, order_id=order.id, **line_data)
            self.db.add(line)
        await self.db.flush()
        return order
        
    async def get_order(self, order_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[SalesOrder]:
        stmt = select(SalesOrder).options(selectinload(SalesOrder.lines)).where(
            SalesOrder.id == order_id, SalesOrder.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_orders(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20, 
        contact_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> list[SalesOrder]:
        stmt = select(SalesOrder).where(SalesOrder.tenant_id == tenant_id)
        if contact_id:
            stmt = stmt.where(SalesOrder.contact_id == contact_id)
        if status:
            stmt = stmt.where(SalesOrder.status == status)
            
        stmt = stmt.order_by(SalesOrder.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
        
    async def count_orders(
        self, tenant_id: uuid.UUID, contact_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> int:
        stmt = select(func.count(SalesOrder.id)).where(SalesOrder.tenant_id == tenant_id)
        if contact_id:
            stmt = stmt.where(SalesOrder.contact_id == contact_id)
        if status:
            stmt = stmt.where(SalesOrder.status == status)
            
        result = await self.db.execute(stmt)
        return result.scalar() or 0
        
    async def update_order(self, order: SalesOrder, lines: Optional[list[dict]] = None, **kwargs) -> SalesOrder:
        for k, v in kwargs.items():
            if hasattr(order, k) and v is not None:
                setattr(order, k, v)
                
        # If lines provided, clear and replace
        if lines is not None:
            # Delete orphan lines handled via cascade if we remove them from the collection
            # But the simplest is direct deletion for Asyncpg:
            from sqlalchemy import delete
            await self.db.execute(delete(SalesOrderLine).where(SalesOrderLine.order_id == order.id))
            
            for line_data in lines:
                line = SalesOrderLine(tenant_id=order.tenant_id, order_id=order.id, **line_data)
                self.db.add(line)
                
        await self.db.flush()
        return order
