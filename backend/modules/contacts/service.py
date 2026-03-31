"""Contacts module service — business logic for contact management."""

import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.schemas import PaginatedResponse, PaginationMeta
from backend.modules.contacts.models import Contact
from backend.modules.contacts.repository import ContactRepository
from backend.modules.contacts.schemas import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)


class ContactService:
    """Business logic for contact and address management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ContactRepository(db)

    async def create_contact(
        self, tenant_id: uuid.UUID, data: ContactCreate, created_by: uuid.UUID = None
    ) -> Contact:
        """Create a new contact with optional inline addresses.

        Validates parent company exists if parent_id is provided.
        """
        # Validate parent_id if provided
        if data.parent_id:
            parent = await self.repo.get_by_id(data.parent_id, tenant_id)
            if not parent:
                raise NotFoundError("Parent contact", data.parent_id)
            if parent.type != "company":
                raise ValidationError("Parent contact must be a company")

        contact_data = data.model_dump(exclude_none=True)
        contact_data["created_by"] = created_by

        contact = await self.repo.create(tenant_id=tenant_id, **contact_data)
        return await self.repo.get_by_id(contact.id, tenant_id)

    async def get_contact(
        self, contact_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> ContactResponse:
        """Get a single contact by ID."""
        contact = await self.repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)
        return ContactResponse.model_validate(contact)

    async def list_contacts(
        self,
        tenant_id: uuid.UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        search: str = None,
        contact_type: str = None,
        is_customer: bool = None,
        is_vendor: bool = None,
        tags: list[str] = None,
    ) -> PaginatedResponse[ContactListResponse]:
        """List contacts with filtering and pagination."""
        offset = (page - 1) * per_page

        contacts = await self.repo.list(
            tenant_id,
            search=search,
            contact_type=contact_type,
            is_customer=is_customer,
            is_vendor=is_vendor,
            tags=tags,
            offset=offset,
            limit=per_page,
        )

        total = await self.repo.count(
            tenant_id,
            search=search,
            contact_type=contact_type,
            is_customer=is_customer,
            is_vendor=is_vendor,
        )

        total_pages = math.ceil(total / per_page) if total > 0 else 0
        data = [ContactListResponse.model_validate(c) for c in contacts]

        return PaginatedResponse(
            data=data,
            meta=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        )

    async def update_contact(
        self,
        contact_id: uuid.UUID,
        tenant_id: uuid.UUID,
        data: ContactUpdate,
    ) -> ContactResponse:
        """Update a contact's fields."""
        contact = await self.repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)

        update_data = data.model_dump(exclude_unset=True)

        # Validate parent_id if being changed
        if "parent_id" in update_data and update_data["parent_id"]:
            parent = await self.repo.get_by_id(update_data["parent_id"], tenant_id)
            if not parent:
                raise NotFoundError("Parent contact", update_data["parent_id"])
            if parent.type != "company":
                raise ValidationError("Parent contact must be a company")

        contact = await self.repo.update(contact, **update_data)
        return ContactResponse.model_validate(contact)

    async def delete_contact(
        self, contact_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> None:
        """Soft-delete a contact."""
        contact = await self.repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)
        await self.repo.soft_delete(contact)

    # ─── Address Operations ───

    async def add_address(
        self,
        contact_id: uuid.UUID,
        tenant_id: uuid.UUID,
        data: AddressCreate,
    ) -> AddressResponse:
        """Add an address to a contact."""
        contact = await self.repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)

        address = await self.repo.add_address(
            contact_id=contact_id, **data.model_dump()
        )
        return AddressResponse.model_validate(address)

    async def update_address(
        self,
        contact_id: uuid.UUID,
        address_id: uuid.UUID,
        tenant_id: uuid.UUID,
        data: AddressUpdate,
    ) -> AddressResponse:
        """Update a contact's address."""
        contact = await self.repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)

        address = await self.repo.get_address(address_id, contact_id)
        if not address:
            raise NotFoundError("Address", address_id)

        update_data = data.model_dump(exclude_unset=True)
        address = await self.repo.update_address(address, **update_data)
        return AddressResponse.model_validate(address)

    async def delete_address(
        self,
        contact_id: uuid.UUID,
        address_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> None:
        """Delete a contact's address."""
        contact = await self.repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)

        address = await self.repo.get_address(address_id, contact_id)
        if not address:
            raise NotFoundError("Address", address_id)

        await self.repo.delete_address(address)
