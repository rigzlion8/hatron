"""CRM Repository."""

import uuid
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.crm.models import CrmPipeline, CrmStage, CrmLead, CrmActivity


class CrmRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Pipeline/Stages ───
    async def create_pipeline(self, tenant_id: uuid.UUID, **kwargs) -> CrmPipeline:
        stages_data = kwargs.pop("stages", None)
        pipeline = CrmPipeline(tenant_id=tenant_id, **kwargs)
        self.db.add(pipeline)
        await self.db.flush()

        if stages_data:
            for s in stages_data:
                stage = CrmStage(pipeline_id=pipeline.id, **s)
                self.db.add(stage)
            await self.db.flush()
        return pipeline

    async def get_pipeline(self, pipeline_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[CrmPipeline]:
        stmt = select(CrmPipeline).where(
            CrmPipeline.id == pipeline_id, CrmPipeline.tenant_id == tenant_id
        ).options(selectinload(CrmPipeline.stages))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def list_pipelines(self, tenant_id: uuid.UUID) -> list[CrmPipeline]:
        stmt = select(CrmPipeline).where(CrmPipeline.tenant_id == tenant_id).options(selectinload(CrmPipeline.stages))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ─── Leads ───
    async def create_lead(self, tenant_id: uuid.UUID, created_by: uuid.UUID, **kwargs) -> CrmLead:
        lead = CrmLead(tenant_id=tenant_id, created_by=created_by, **kwargs)
        self.db.add(lead)
        await self.db.flush()
        return lead
        
    async def get_lead(self, lead_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[CrmLead]:
        stmt = select(CrmLead).options(
            selectinload(CrmLead.stage), selectinload(CrmLead.activities)
        ).where(
            CrmLead.id == lead_id, CrmLead.tenant_id == tenant_id, CrmLead.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_leads(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20, 
        stage_id: Optional[uuid.UUID] = None, assigned_to: Optional[uuid.UUID] = None, 
        status: Optional[str] = None, search: Optional[str] = None
    ) -> list[CrmLead]:
        stmt = select(CrmLead).options(selectinload(CrmLead.stage)).where(
            CrmLead.tenant_id == tenant_id, CrmLead.is_deleted == False
        )
        
        if stage_id:
            stmt = stmt.where(CrmLead.stage_id == stage_id)
        if assigned_to:
            stmt = stmt.where(CrmLead.assigned_to == assigned_to)
        if status:
            stmt = stmt.where(CrmLead.status == status)
        if search:
            stmt = stmt.where(CrmLead.name.ilike(f"%{search}%"))

        stmt = stmt.order_by(CrmLead.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
        
    async def count_leads(self, tenant_id: uuid.UUID, stage_id: Optional[uuid.UUID] = None, assigned_to: Optional[uuid.UUID] = None, status: Optional[str] = None, search: Optional[str] = None) -> int:
        stmt = select(func.count(CrmLead.id)).where(CrmLead.tenant_id == tenant_id, CrmLead.is_deleted == False)
        if stage_id:
            stmt = stmt.where(CrmLead.stage_id == stage_id)
        if assigned_to:
            stmt = stmt.where(CrmLead.assigned_to == assigned_to)
        if status:
            stmt = stmt.where(CrmLead.status == status)
        if search:
            stmt = stmt.where(CrmLead.name.ilike(f"%{search}%"))
        result = await self.db.execute(stmt)
        return result.scalar() or 0
        
    async def update_lead(self, lead: CrmLead, **kwargs) -> CrmLead:
        for k, v in kwargs.items():
            if hasattr(lead, k) and v is not None:
                setattr(lead, k, v)
        await self.db.flush()
        return lead
        
    # ─── Activities ───
    async def create_activity(self, tenant_id: uuid.UUID, **kwargs) -> CrmActivity:
        activity = CrmActivity(tenant_id=tenant_id, **kwargs)
        self.db.add(activity)
        await self.db.flush()
        return activity
        
    async def update_activity(self, activity_id: uuid.UUID, tenant_id: uuid.UUID, done: bool) -> Optional[CrmActivity]:
        stmt = select(CrmActivity).where(CrmActivity.id == activity_id, CrmActivity.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        activity = result.scalar_one_or_none()
        if activity:
            activity.done = done
            await self.db.flush()
        return activity
