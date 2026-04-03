"""Sales module API Router."""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.settings import settings

from backend.core.dependencies import get_current_user, get_db
from backend.core.schemas import PaginatedResponse
from backend.modules.auth.models import User
from backend.modules.sales.schemas import (
    ProductCategoryCreate, ProductCategoryResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    SalesOrderCreate, SalesOrderUpdate, SalesOrderStateUpdate,
    SalesOrderResponse, SalesOrderListResponse
)
from backend.modules.sales.service import SalesService

# Two routers to keep endpoints clean: Products and Sales

products_router = APIRouter(prefix="/products", tags=["Products"])
sales_router = APIRouter(prefix="/sales", tags=["Sales"])

# ─── Products & Categories ───

@products_router.post("/categories", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: ProductCategoryCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.create_category(current_user.tenant_id, data)

@products_router.get("/categories", response_model=list[ProductCategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.list_categories(current_user.tenant_id)

@products_router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.create_product(current_user.tenant_id, data)

@products_router.get("", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.list_products(
        current_user.tenant_id, page=page, per_page=per_page, 
        category_id=category_id, search=search
    )

@products_router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.get_product(product_id, current_user.tenant_id)

@products_router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.update_product(product_id, current_user.tenant_id, data)


@products_router.post("/{product_id}/upload-image", response_model=dict)
async def upload_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload product image and return the file path."""
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    tenant_id = current_user.tenant_id
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"product_{product_id}_{uuid.uuid4()}{file_ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, str(tenant_id), filename)
    
    # Create tenant directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Save file
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Return a path that can be passed through Next.js proxy
    relative_path = f"/api/v1/uploads/{tenant_id}/{filename}"
    
    return {
        "url": relative_path,
        "filename": filename
    }


# ─── Sales Orders ───

@sales_router.post("/orders", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: SalesOrderCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.create_order(current_user.tenant_id, current_user.id, data)

@sales_router.get("/orders", response_model=PaginatedResponse[SalesOrderListResponse])
async def list_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    contact_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.list_orders(
        current_user.tenant_id, page=page, per_page=per_page, 
        contact_id=contact_id, status=status
    )

@sales_router.get("/orders/{order_id}", response_model=SalesOrderResponse)
async def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.get_order(order_id, current_user.tenant_id)

@sales_router.patch("/orders/{order_id}", response_model=SalesOrderResponse)
async def update_order(
    order_id: uuid.UUID,
    data: SalesOrderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.update_order(order_id, current_user.tenant_id, data)

@sales_router.post("/orders/{order_id}/confirm", response_model=SalesOrderResponse)
async def confirm_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SalesService(db)
    return await service.confirm_order(order_id, current_user.tenant_id)
