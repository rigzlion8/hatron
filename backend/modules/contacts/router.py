"""Contacts module API routes."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user, get_db
from backend.core.schemas import MessageResponse, PaginatedResponse
from backend.modules.auth.models import User
from backend.modules.contacts.schemas import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from backend.modules.contacts.service import ContactService

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get(
    "",
    response_model=PaginatedResponse[ContactListResponse],
    summary="List contacts",
    description="List all contacts with filtering, search, and pagination.",
)
async def list_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search name, email, phone"),
    type: Optional[str] = Query(None, description="Filter by type: individual or company"),
    is_customer: Optional[bool] = Query(None),
    is_vendor: Optional[bool] = Query(None),
    tags: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ContactService(db)
    return await service.list_contacts(
        tenant_id=current_user.tenant_id,
        page=page,
        per_page=per_page,
        search=search,
        contact_type=type,
        is_customer=is_customer,
        is_vendor=is_vendor,
        tags=tags,
    )


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a contact",
    description="Create a new contact (individual or company) with optional addresses.",
)
async def create_contact(
    data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ContactService(db)
    contact = await service.create_contact(
        tenant_id=current_user.tenant_id,
        data=data,
        created_by=current_user.id,
    )
    return ContactResponse.model_validate(contact)


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Get contact details",
)
async def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ContactService(db)
    return await service.get_contact(contact_id, current_user.tenant_id)


@router.patch(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Update a contact",
)
async def update_contact(
    contact_id: uuid.UUID,
    data: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ContactService(db)
    return await service.update_contact(
        contact_id, current_user.tenant_id, data
    )


@router.delete(
    "/{contact_id}",
    response_model=MessageResponse,
    summary="Delete a contact",
    description="Soft-deletes the contact (can be recovered).",
)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ContactService(db)
    await service.delete_contact(contact_id, current_user.tenant_id)
    return MessageResponse(message="Contact deleted successfully")


# ─── Address Sub-routes ───


@router.post(
    "/{contact_id}/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add address to contact",
)
async def add_address(
    contact_id: uuid.UUID,
    data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ContactService(db)
    return await service.add_address(
        contact_id, current_user.tenant_id, data
    )


@router.patch(
    "/{contact_id}/addresses/{address_id}",
    response_model=AddressResponse,
    summary="Update an address",
)
async def update_address(
    contact_id: uuid.UUID,
    address_id: uuid.UUID,
    data: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ContactService(db)
    return await service.update_address(
        contact_id, address_id, current_user.tenant_id, data
    )


@router.delete(
    "/{contact_id}/addresses/{address_id}",
    response_model=MessageResponse,
    summary="Delete an address",
)
async def delete_address(
    contact_id: uuid.UUID,
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ContactService(db)
    await service.delete_address(
        contact_id, address_id, current_user.tenant_id
    )
    return MessageResponse(message="Address deleted successfully")
