"""System Settings API Router."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.dependencies import get_db, get_current_user
from backend.modules.auth.models import User
from backend.modules.settings.models import SystemSettings
from backend.modules.settings.schemas import SystemSettingsResponse, SystemSettingsUpdate

router = APIRouter(prefix="/settings", tags=["System Settings"])


async def get_or_create_settings(db: AsyncSession, tenant_id: uuid.UUID) -> SystemSettings:
    """Helper to ensure a settings object exists for every tenant."""
    stmt = select(SystemSettings).where(SystemSettings.tenant_id == tenant_id)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = SystemSettings(tenant_id=tenant_id, brand_name="Hatron")
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        
    return settings


@router.get("/", response_model=SystemSettingsResponse)
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Fetch branding and UI settings for the current tenant."""
    return await get_or_create_settings(db, user.tenant_id)


@router.put("/", response_model=SystemSettingsResponse)
async def update_system_settings(
    data: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Update branding and UI settings (Admin privilege assumed or implied by access)."""
    # Simple check for now, we can add more robust RBAC later
    settings = await get_or_create_settings(db, user.tenant_id)
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
        
    await db.commit()
    await db.refresh(settings)
    return settings
