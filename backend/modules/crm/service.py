"""CRM Service."""

import math
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.schemas import PaginatedResponse, PaginationMeta
from backend.modules.crm.models import CrmLead, CrmPipeline, CrmActivity
from backend.modules.crm.repository import CrmRepository
from backend.modules.crm.schemas import (
    CrmPipelineCreate,
    CrmPipelineResponse,
    CrmLeadCreate,
    CrmLeadUpdate,
    CrmLeadStateUpdate,
    CrmLeadResponse,
    CrmLeadListResponse,
    CrmActivityCreate,
    CrmActivityResponse
)


class CrmService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CrmRepository(db)

    # ─── Pipelines ───
    async def create_pipeline(self, tenant_id: uuid.UUID, data: CrmPipelineCreate) -> CrmPipelineResponse:
        p_data = data.model_dump()
        pipeline = await self.repo.create_pipeline(tenant_id, **p_data)
        # Refetch to eager load stages
        pipeline = await self.repo.get_pipeline(pipeline.id, tenant_id)
        return CrmPipelineResponse.model_validate(pipeline)

    async def list_pipelines(self, tenant_id: uuid.UUID) -> list[CrmPipelineResponse]:
        pipelines = await self.repo.list_pipelines(tenant_id)
        return [CrmPipelineResponse.model_validate(p) for p in pipelines]

    # ─── Leads ───
    async def create_lead(self, tenant_id: uuid.UUID, created_by: uuid.UUID, data: CrmLeadCreate) -> CrmLeadResponse:
        lead_data = data.model_dump()
        lead = await self.repo.create_lead(tenant_id, created_by, **lead_data)
        lead = await self.repo.get_lead(lead.id, tenant_id)
        return CrmLeadResponse.model_validate(lead)

    async def get_lead(self, lead_id: uuid.UUID, tenant_id: uuid.UUID) -> CrmLeadResponse:
        lead = await self.repo.get_lead(lead_id, tenant_id)
        if not lead:
            raise NotFoundError("Lead", lead_id)
        return CrmLeadResponse.model_validate(lead)

    async def list_leads(
        self, tenant_id: uuid.UUID, page: int = 1, per_page: int = 20, 
        stage_id: Optional[uuid.UUID] = None, assigned_to: Optional[uuid.UUID] = None, 
        status: Optional[str] = None, search: Optional[str] = None
    ) -> PaginatedResponse[CrmLeadListResponse]:
        offset = (page - 1) * per_page
        leads = await self.repo.list_leads(
            tenant_id, offset=offset, limit=per_page, stage_id=stage_id, 
            assigned_to=assigned_to, status=status, search=search
        )
        total = await self.repo.count_leads(tenant_id, stage_id, assigned_to, status, search)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        
        return PaginatedResponse(
            data=[CrmLeadListResponse.model_validate(l) for l in leads],
            meta=PaginationMeta(
                total=total, page=page, per_page=per_page, total_pages=total_pages,
                has_next=page < total_pages, has_prev=page > 1
            )
        )

    async def update_lead(self, lead_id: uuid.UUID, tenant_id: uuid.UUID, data: CrmLeadUpdate) -> CrmLeadResponse:
        lead = await self.repo.get_lead(lead_id, tenant_id)
        if not lead:
            raise NotFoundError("Lead", lead_id)
        update_data = data.model_dump(exclude_unset=True)
        lead = await self.repo.update_lead(lead, **update_data)
        lead = await self.repo.get_lead(lead.id, tenant_id)
        return CrmLeadResponse.model_validate(lead)

    async def update_lead_state(self, lead_id: uuid.UUID, tenant_id: uuid.UUID, data: CrmLeadStateUpdate) -> CrmLeadResponse:
        lead = await self.repo.get_lead(lead_id, tenant_id)
        if not lead:
            raise NotFoundError("Lead", lead_id)
        update_data = data.model_dump(exclude_unset=True)
        # Move stages or change won/lost status
        lead = await self.repo.update_lead(lead, **update_data)
        lead = await self.repo.get_lead(lead.id, tenant_id)
        return CrmLeadResponse.model_validate(lead)

    # ─── Activities ───
    async def create_activity(self, lead_id: uuid.UUID, tenant_id: uuid.UUID, data: CrmActivityCreate) -> CrmActivityResponse:
        lead = await self.repo.get_lead(lead_id, tenant_id)
        if not lead:
            raise NotFoundError("Lead", lead_id)
        
        activity = await self.repo.create_activity(tenant_id=tenant_id, lead_id=lead_id, **data.model_dump())
        return CrmActivityResponse.model_validate(activity)

    async def mark_activity_done(self, activity_id: uuid.UUID, tenant_id: uuid.UUID, done: bool) -> CrmActivityResponse:
        activity = await self.repo.update_activity(activity_id, tenant_id, done)
        if not activity:
            raise NotFoundError("Activity", activity_id)
        return CrmActivityResponse.model_validate(activity)
