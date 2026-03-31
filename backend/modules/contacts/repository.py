"""Contacts module repository — database queries for contacts and addresses."""

import uuid
from typing import Optional

from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.modules.contacts.models import Address, Contact


class ContactRepository:
    """Data access layer for contacts and addresses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Contact Operations ───

    async def create(self, tenant_id: uuid.UUID, **kwargs) -> Contact:
        """Create a new contact."""
        addresses_data = kwargs.pop("addresses", None)
        contact = Contact(tenant_id=tenant_id, **kwargs)
        self.db.add(contact)
        await self.db.flush()

        if addresses_data:
            for addr_data in addresses_data:
                if isinstance(addr_data, dict):
                    address = Address(contact_id=contact.id, **addr_data)
                else:
                    address = Address(
                        contact_id=contact.id, **addr_data.model_dump()
                    )
                self.db.add(address)
            await self.db.flush()

        return contact

    async def get_by_id(
        self, contact_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Optional[Contact]:
        """Get a contact by ID within a tenant (excludes soft-deleted)."""
        stmt = (
            select(Contact)
            .options(selectinload(Contact.addresses))
            .where(
                Contact.id == contact_id,
                Contact.tenant_id == tenant_id,
                Contact.is_deleted == False,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        tenant_id: uuid.UUID,
        *,
        search: Optional[str] = None,
        contact_type: Optional[str] = None,
        is_customer: Optional[bool] = None,
        is_vendor: Optional[bool] = None,
        tags: Optional[list[str]] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Contact]:
        """List contacts with filtering and pagination."""
        stmt = (
            select(Contact)
            .where(Contact.tenant_id == tenant_id, Contact.is_deleted == False)
            .order_by(Contact.name)
        )

        # Apply filters
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Contact.name.ilike(pattern),
                    Contact.email.ilike(pattern),
                    Contact.phone.ilike(pattern),
                )
            )
        if contact_type:
            stmt = stmt.where(Contact.type == contact_type)
        if is_customer is not None:
            stmt = stmt.where(Contact.is_customer == is_customer)
        if is_vendor is not None:
            stmt = stmt.where(Contact.is_vendor == is_vendor)
        if tags:
            stmt = stmt.where(Contact.tags.overlap(tags))

        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        tenant_id: uuid.UUID,
        *,
        search: Optional[str] = None,
        contact_type: Optional[str] = None,
        is_customer: Optional[bool] = None,
        is_vendor: Optional[bool] = None,
    ) -> int:
        """Count contacts matching filters."""
        stmt = select(func.count(Contact.id)).where(
            Contact.tenant_id == tenant_id, Contact.is_deleted == False
        )
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Contact.name.ilike(pattern),
                    Contact.email.ilike(pattern),
                    Contact.phone.ilike(pattern),
                )
            )
        if contact_type:
            stmt = stmt.where(Contact.type == contact_type)
        if is_customer is not None:
            stmt = stmt.where(Contact.is_customer == is_customer)
        if is_vendor is not None:
            stmt = stmt.where(Contact.is_vendor == is_vendor)

        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def update(self, contact: Contact, **kwargs) -> Contact:
        """Update contact fields."""
        for key, value in kwargs.items():
            if hasattr(contact, key) and value is not None:
                setattr(contact, key, value)
        await self.db.flush()
        return contact

    async def soft_delete(self, contact: Contact) -> None:
        """Soft-delete a contact."""
        contact.is_deleted = True
        await self.db.flush()

    # ─── Address Operations ───

    async def add_address(
        self, contact_id: uuid.UUID, **kwargs
    ) -> Address:
        """Add an address to a contact."""
        address = Address(contact_id=contact_id, **kwargs)
        self.db.add(address)
        await self.db.flush()
        return address

    async def get_address(
        self, address_id: uuid.UUID, contact_id: uuid.UUID
    ) -> Optional[Address]:
        """Get a specific address."""
        stmt = select(Address).where(
            Address.id == address_id, Address.contact_id == contact_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_address(self, address: Address, **kwargs) -> Address:
        """Update address fields."""
        for key, value in kwargs.items():
            if hasattr(address, key) and value is not None:
                setattr(address, key, value)
        await self.db.flush()
        return address

    async def delete_address(self, address: Address) -> None:
        """Hard-delete an address."""
        await self.db.delete(address)
        await self.db.flush()
