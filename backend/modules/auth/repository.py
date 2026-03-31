"""Auth module repository — database queries for users, roles, tenants."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.models import TenantModel
from backend.modules.auth.models import Role, RolePermission, User, user_roles


class AuthRepository:
    """Data access layer for authentication-related entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Tenant Operations ───

    async def create_tenant(self, name: str, slug: str) -> TenantModel:
        """Create a new tenant (company/organization)."""
        tenant = TenantModel(name=name, slug=slug)
        self.db.add(tenant)
        await self.db.flush()
        return tenant

    async def get_tenant_by_slug(self, slug: str) -> Optional[TenantModel]:
        """Find a tenant by its URL slug."""
        stmt = select(TenantModel).where(TenantModel.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tenant_by_id(self, tenant_id: uuid.UUID) -> Optional[TenantModel]:
        """Find a tenant by ID."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ─── User Operations ───

    async def create_user(
        self,
        tenant_id: uuid.UUID,
        email: str,
        password_hash: str,
        full_name: str,
        is_superuser: bool = False,
    ) -> User:
        """Create a new user within a tenant."""
        user = User(
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_superuser=is_superuser,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_user_by_email(
        self, email: str, tenant_id: uuid.UUID
    ) -> Optional[User]:
        """Find a user by email within a specific tenant."""
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.email == email, User.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Find a user by ID."""
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users_by_tenant(
        self,
        tenant_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> list[User]:
        """List all users for a tenant with pagination."""
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.tenant_id == tenant_id)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_users_by_tenant(self, tenant_id: uuid.UUID) -> int:
        """Count total users in a tenant."""
        stmt = select(func.count(User.id)).where(User.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def update_last_login(self, user: User) -> None:
        """Update the user's last login timestamp."""
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(user)

    async def update_user(
        self, user: User, **kwargs
    ) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.db.flush()
        return user

    # ─── Role Operations ───

    async def create_role(
        self,
        tenant_id: uuid.UUID,
        name: str,
        description: str = "",
        permissions: list[str] | None = None,
        is_system: bool = False,
    ) -> Role:
        """Create a role with optional permissions."""
        role = Role(
            tenant_id=tenant_id,
            name=name,
            description=description,
            is_system=is_system,
        )
        self.db.add(role)
        await self.db.flush()

        if permissions:
            for perm in permissions:
                role_perm = RolePermission(role_id=role.id, permission=perm)
                self.db.add(role_perm)
            await self.db.flush()

        return role

    async def get_role_by_name(
        self, name: str, tenant_id: uuid.UUID
    ) -> Optional[Role]:
        """Find a role by name within a tenant."""
        stmt = select(Role).where(
            Role.name == name, Role.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def assign_role_to_user(
        self, user_id: uuid.UUID, role_id: uuid.UUID
    ) -> None:
        """Add a role to a user via direct insert (avoids lazy-load)."""
        from sqlalchemy import insert

        stmt = insert(user_roles).values(user_id=user_id, role_id=role_id)
        await self.db.execute(stmt)
        await self.db.flush()

