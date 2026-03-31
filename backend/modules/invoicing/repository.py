"""Invoicing Repository."""

import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.invoicing.models import TaxRule, Invoice, InvoiceLine, Payment


class InvoicingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Taxes ───
    async def create_tax_rule(self, tenant_id: uuid.UUID, **kwargs) -> TaxRule:
        rule = TaxRule(tenant_id=tenant_id, **kwargs)
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def get_tax_rule(self, tax_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[TaxRule]:
        stmt = select(TaxRule).where(TaxRule.id == tax_id, TaxRule.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tax_rules(self, tenant_id: uuid.UUID) -> list[TaxRule]:
        stmt = select(TaxRule).where(TaxRule.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    # ─── Invoices ───
    async def generate_invoice_number(self, tenant_id: uuid.UUID) -> str:
        stmt = select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        return f"INV-{count + 1:05d}"
        
    async def create_invoice(self, tenant_id: uuid.UUID, created_by: uuid.UUID, lines: list[dict], **kwargs) -> Invoice:
        inv_num = await self.generate_invoice_number(tenant_id)
        invoice = Invoice(tenant_id=tenant_id, created_by=created_by, invoice_number=inv_num, **kwargs)
        self.db.add(invoice)
        await self.db.flush()
        
        for line_data in lines:
            line = InvoiceLine(tenant_id=tenant_id, invoice_id=invoice.id, **line_data)
            self.db.add(line)
        await self.db.flush()
        return invoice
        
    async def get_invoice(self, invoice_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Invoice]:
        stmt = select(Invoice).options(
            selectinload(Invoice.lines), selectinload(Invoice.payments)
        ).where(
            Invoice.id == invoice_id, Invoice.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_invoices(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 20, 
        contact_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.tenant_id == tenant_id)
        if contact_id:
            stmt = stmt.where(Invoice.contact_id == contact_id)
        if status:
            stmt = stmt.where(Invoice.status == status)
            
        stmt = stmt.order_by(Invoice.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
        
    async def count_invoices(
        self, tenant_id: uuid.UUID, contact_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> int:
        stmt = select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id)
        if contact_id:
            stmt = stmt.where(Invoice.contact_id == contact_id)
        if status:
            stmt = stmt.where(Invoice.status == status)
            
        result = await self.db.execute(stmt)
        return result.scalar() or 0
        
    async def update_invoice(self, invoice: Invoice, lines: Optional[list[dict]] = None, **kwargs) -> Invoice:
        for k, v in kwargs.items():
            if hasattr(invoice, k) and v is not None:
                setattr(invoice, k, v)
                
        # If lines provided, clear and replace
        if lines is not None:
            from sqlalchemy import delete
            await self.db.execute(delete(InvoiceLine).where(InvoiceLine.invoice_id == invoice.id))
            
            for line_data in lines:
                line = InvoiceLine(tenant_id=invoice.tenant_id, invoice_id=invoice.id, **line_data)
                self.db.add(line)
                
        await self.db.flush()
        return invoice


    # ─── Payments ───
    async def create_payment(self, tenant_id: uuid.UUID, invoice_id: uuid.UUID, **kwargs) -> Payment:
        payment = Payment(tenant_id=tenant_id, invoice_id=invoice_id, **kwargs)
        self.db.add(payment)
        await self.db.flush()
        return payment
