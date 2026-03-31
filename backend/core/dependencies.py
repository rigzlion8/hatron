"""FastAPI dependencies — shared across all modules.

These are injected into route handlers via Depends().
"""

import uuid
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.database import async_session_factory
from backend.core.security import decode_token

# HTTP Bearer token extraction
security_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    Commits on success, rolls back on exception. The session is
    scoped to a single request lifecycle.

    Usage in routes:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Extract and validate the current user from the JWT token.

    Returns the User ORM object with roles eagerly loaded.
    Raises 401 if token is invalid or user not found.
    """
    from backend.modules.auth.models import User

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    stmt = (
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_uuid, User.is_active == True)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user if a valid token is provided, otherwise None.

    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if credentials is None:
        return None

    from backend.modules.auth.models import User

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return None

    stmt = (
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_uuid, User.is_active == True)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
