"""CRM API Router."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_user, get_db
from backend.core.schemas import PaginatedResponse
from backend.modules.auth.models import User
from backend.modules.crm.schemas import (
    CrmPipelineCreate,
    CrmPipelineResponse,
    CrmLeadCreate,
    CrmLeadUpdate,
    CrmLeadStateUpdate,
    CrmLeadResponse,
    CrmLeadListResponse,
    CrmActivityCreate,
    CrmActivityResponse,
    CrmActivityUpdate
)
from backend.modules.crm.service import CrmService

router = APIRouter(prefix="/crm", tags=["CRM"])


# ─── Pipelines ───

@router.post("/pipelines", response_model=CrmPipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    data: CrmPipelineCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = CrmService(db)
    return await service.create_pipeline(current_user.tenant_id, data)

@router.get("/pipelines", response_model=list[CrmPipelineResponse])
async def list_pipelines(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = CrmService(db)
    return await service.list_pipelines(current_user.tenant_id)


# ─── Leads ───

@router.post("/leads", response_model=CrmLeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    data: CrmLeadCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    service = CrmService(db)
    return await service.create_lead(current_user.tenant_id, current_user.id, data)

@router.get("/leads", response_model=PaginatedResponse[CrmLeadListResponse])
async def list_leads(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    stage_id: Optional[uuid.UUID] = None,
    assigned_to: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CrmService(db)
    return await service.list_leads(
        current_user.tenant_id, page=page, per_page=per_page, 
        stage_id=stage_id, assigned_to=assigned_to, status=status, search=search
    )

@router.get("/leads/{lead_id}", response_model=CrmLeadResponse)
async def get_lead(
    lead_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CrmService(db)
    return await service.get_lead(lead_id, current_user.tenant_id)

@router.patch("/leads/{lead_id}", response_model=CrmLeadResponse)
async def update_lead(
    lead_id: uuid.UUID,
    data: CrmLeadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CrmService(db)
    return await service.update_lead(lead_id, current_user.tenant_id, data)

@router.patch("/leads/{lead_id}/move", response_model=CrmLeadResponse)
async def move_lead_stage(
    lead_id: uuid.UUID,
    data: CrmLeadStateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CrmService(db)
    return await service.update_lead_state(lead_id, current_user.tenant_id, data)


# ─── Activities ───

@router.post("/leads/{lead_id}/activities", response_model=CrmActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    lead_id: uuid.UUID,
    data: CrmActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CrmService(db)
    return await service.create_activity(lead_id, current_user.tenant_id, data)

@router.patch("/activities/{activity_id}", response_model=CrmActivityResponse)
async def mark_activity_status(
    activity_id: uuid.UUID,
    data: CrmActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CrmService(db)
    return await service.mark_activity_done(activity_id, current_user.tenant_id, data.done)
