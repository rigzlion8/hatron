"""Auth module service — business logic for authentication and user management."""

import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
)
from backend.core.permissions import DEFAULT_ROLES
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.modules.auth.models import User
from backend.modules.auth.repository import AuthRepository
from backend.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from backend.settings import settings


class AuthService:
    """Business logic for authentication, registration, and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuthRepository(db)

    async def register(self, data: RegisterRequest) -> tuple[User, TokenResponse]:
        """Register a new user and optionally create a new tenant.

        If tenant_name is provided, creates a new tenant and makes the
        user a superuser of that tenant. Otherwise, joins an existing tenant.

        Returns:
            Tuple of (created User, TokenResponse with JWT tokens).

        Raises:
            ValidationError: If neither tenant_name nor tenant_id is provided.
            AlreadyExistsError: If email is already taken in the tenant.
            NotFoundError: If tenant_id doesn't exist.
        """
        # Determine tenant
        if data.tenant_name:
            # Create new tenant
            slug = self._slugify(data.tenant_name)
            existing = await self.repo.get_tenant_by_slug(slug)
            if existing:
                raise AlreadyExistsError("Tenant", "name")
            tenant = await self.repo.create_tenant(
                name=data.tenant_name, slug=slug
            )
            is_superuser = True  # First user is admin
        elif data.tenant_id:
            tenant = await self.repo.get_tenant_by_id(data.tenant_id)
            if not tenant:
                raise NotFoundError("Tenant", data.tenant_id)
            is_superuser = False
        else:
            raise ValidationError(
                "Either tenant_name (new org) or tenant_id (join existing) is required"
            )

        # Check for duplicate email in tenant
        existing_user = await self.repo.get_user_by_email(data.email, tenant.id)
        if existing_user:
            raise AlreadyExistsError("User", "email")

        # Create user
        user = await self.repo.create_user(
            tenant_id=tenant.id,
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            is_superuser=is_superuser,
        )

        # Create default roles for new tenant
        if data.tenant_name:
            await self._create_default_roles(tenant.id)

        # Assign default role
        role_name = "admin" if is_superuser else "user"
        role = await self.repo.get_role_by_name(role_name, tenant.id)
        if role:
            await self.repo.assign_role_to_user(user.id, role.id)

        # Re-fetch user with roles eagerly loaded
        user = await self.repo.get_user_by_id(user.id)

        # Generate tokens
        tokens = self._create_tokens(user)

        return user, tokens

    async def login(self, data: LoginRequest) -> tuple[User, TokenResponse]:
        """Authenticate a user with email and password.

        Returns:
            Tuple of (authenticated User, TokenResponse with JWT tokens).

        Raises:
            AuthenticationError: If credentials are invalid.
            NotFoundError: If tenant not found (when using tenant_slug).
        """
        # Resolve tenant
        if data.tenant_slug:
            tenant = await self.repo.get_tenant_by_slug(data.tenant_slug)
            if not tenant:
                raise NotFoundError("Tenant", data.tenant_slug)
            tenant_id = tenant.id
        else:
            # For single-tenant or when tenant is implicit, find user across tenants
            # In production, you'd require tenant_slug or use subdomain
            # For MVP, we search by email and return the first match
            from sqlalchemy import select
            from backend.modules.auth.models import User as UserModel

            stmt = select(UserModel).where(UserModel.email == data.email)
            result = await self.db.execute(stmt)
            found_user = result.scalar_one_or_none()
            if not found_user:
                raise AuthenticationError("Invalid email or password")
            tenant_id = found_user.tenant_id

        user = await self.repo.get_user_by_email(data.email, tenant_id)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        if not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        # Update last login timestamp in background
        await self.repo.update_last_login(user)

        tokens = self._create_tokens(user)
        return user, tokens

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Generate new access token using a valid refresh token.

        Returns:
            New TokenResponse with fresh access and refresh tokens.

        Raises:
            AuthenticationError: If refresh token is invalid or expired.
        """
        payload = decode_token(refresh_token)
        if payload is None:
            raise AuthenticationError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        user = await self.repo.get_user_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        return self._create_tokens(user)

    async def get_profile(self, user_id: uuid.UUID) -> User:
        """Get the current user's profile."""
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def update_profile(
        self, user: User, full_name: str = None, avatar_url: str = None
    ) -> User:
        """Update user profile fields."""
        updates = {}
        if full_name is not None:
            updates["full_name"] = full_name
        if avatar_url is not None:
            updates["avatar_url"] = avatar_url
        if updates:
            user = await self.repo.update_user(user, **updates)
        return user

    async def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        """Change user password after verifying current password."""
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        await self.repo.update_user(
            user, password_hash=hash_password(new_password)
        )

    # ─── Private Helpers ───

    def _create_tokens(self, user: User, role_names: list[str] | None = None) -> TokenResponse:
        """Generate JWT access and refresh token pair for a user."""
        if role_names is None:
            # Roles should already be eagerly loaded at this point
            try:
                role_names = [r.name for r in user.roles] if user.roles else []
            except Exception:
                role_names = []
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=role_names,
        )
        refresh_token = create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def _create_default_roles(self, tenant_id: uuid.UUID) -> None:
        """Create the default system roles for a new tenant."""
        for role_name, permissions in DEFAULT_ROLES.items():
            perm_values = [p.value if hasattr(p, "value") else p for p in permissions]
            await self.repo.create_role(
                tenant_id=tenant_id,
                name=role_name,
                description=f"System {role_name} role",
                permissions=perm_values,
                is_system=True,
            )

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to URL-safe slug."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text
