"""Invoicing Service."""

import math
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.events import event_bus
from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.schemas import PaginatedResponse, PaginationMeta
from backend.modules.invoicing.models import Invoice, TaxRule
from backend.modules.invoicing.repository import InvoicingRepository
from backend.modules.invoicing.schemas import (
    TaxRuleCreate, TaxRuleResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceStateUpdate,
    InvoiceResponse, InvoiceListResponse,
    PaymentCreate, PaymentResponse,
    InvoiceLineCreate
)
# We will need the Sales Order service repo or direct DB query to fetch order details for the event handler.
from backend.modules.sales.repository import SalesRepository


class InvoicingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = InvoicingRepository(db)

    # ─── Taxes ───

    async def create_tax_rule(self, tenant_id: uuid.UUID, data: TaxRuleCreate) -> TaxRuleResponse:
        rule = await self.repo.create_tax_rule(tenant_id, **data.model_dump())
        rule = await self.repo.get_tax_rule(rule.id, tenant_id)
        return TaxRuleResponse.model_validate(rule)

    async def list_tax_rules(self, tenant_id: uuid.UUID) -> list[TaxRuleResponse]:
        rules = await self.repo.list_tax_rules(tenant_id)
        return [TaxRuleResponse.model_validate(r) for r in rules]


    # ─── Invoices ───

    async def _calculate_invoice_totals(self, tenant_id: uuid.UUID, lines_data: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
        untaxed = Decimal('0.0')
        tax = Decimal('0.0')
        
        for line in lines_data:
            unit_price = Decimal(str(line["unit_price"]))
            qty = Decimal(str(line["quantity"]))
            discount_pct = Decimal(str(line["discount"]))
            
            subtotal = qty * unit_price * (Decimal('1.0') - discount_pct / Decimal('100.0'))
            
            line_tax = Decimal('0.0')
            if line.get("tax_id"):
                tax_rule = await self.repo.get_tax_rule(line["tax_id"], tenant_id)
                if tax_rule:
                    rate = Decimal(str(tax_rule.rate)) / Decimal('100.0')
                    line_tax = subtotal * rate
            
            line["unit_price"] = float(unit_price)
            line["price_subtotal"] = float(subtotal)
            line["price_tax"] = float(line_tax)
            line["price_total"] = float(subtotal + line_tax)
            
            untaxed += subtotal
            tax += line_tax
            
        return float(untaxed), float(tax), float(untaxed + tax)

    async def create_invoice(self, tenant_id: uuid.UUID, created_by: uuid.UUID, data: InvoiceCreate) -> InvoiceResponse:
        invoice_data = data.model_dump(exclude={"lines"})
        lines_data = data.model_dump()["lines"]
        
        untaxed, tax, total = await self._calculate_invoice_totals(tenant_id, lines_data)
        
        invoice_data["amount_untaxed"] = untaxed
        invoice_data["amount_tax"] = tax
        invoice_data["amount_total"] = total
        invoice_data["amount_residual"] = total # Initially nothing is paid
        
        invoice = await self.repo.create_invoice(tenant_id, created_by, lines_data, **invoice_data)
        invoice = await self.repo.get_invoice(invoice.id, tenant_id)
        return InvoiceResponse.model_validate(invoice)

    async def get_invoice(self, invoice_id: uuid.UUID, tenant_id: uuid.UUID) -> InvoiceResponse:
        invoice = await self.repo.get_invoice(invoice_id, tenant_id)
        if not invoice:
            raise NotFoundError("Invoice", invoice_id)
        return InvoiceResponse.model_validate(invoice)

    async def list_invoices(
        self, tenant_id: uuid.UUID, page: int = 1, per_page: int = 20, 
        contact_id: Optional[uuid.UUID] = None, status: Optional[str] = None
    ) -> PaginatedResponse[InvoiceListResponse]:
        offset = (page - 1) * per_page
        invoices = await self.repo.list_invoices(tenant_id, offset, limit=per_page, contact_id=contact_id, status=status)
        total = await self.repo.count_invoices(tenant_id, contact_id, status)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        
        return PaginatedResponse(
            data=[InvoiceListResponse.model_validate(i) for i in invoices],
            meta=PaginationMeta(
                total=total, page=page, per_page=per_page, total_pages=total_pages,
                has_next=page < total_pages, has_prev=page > 1
            )
        )

    async def update_invoice(self, invoice_id: uuid.UUID, tenant_id: uuid.UUID, data: InvoiceUpdate) -> InvoiceResponse:
        invoice = await self.repo.get_invoice(invoice_id, tenant_id)
        if not invoice:
            raise NotFoundError("Invoice", invoice_id)
        if invoice.status != "draft":
            raise ValidationError("Cannot update a posted/open invoice")
            
        update_data = data.model_dump(exclude_unset=True, exclude={"lines"})
        lines_data = data.model_dump(exclude_unset=True).get("lines")
        
        if lines_data is not None:
            untaxed, tax, total = await self._calculate_invoice_totals(tenant_id, lines_data)
            update_data["amount_untaxed"] = untaxed
            update_data["amount_tax"] = tax
            update_data["amount_total"] = total
            update_data["amount_residual"] = total
            
        invoice = await self.repo.update_invoice(invoice, lines=lines_data, **update_data)
        invoice = await self.repo.get_invoice(invoice.id, tenant_id)
        return InvoiceResponse.model_validate(invoice)

    async def update_state(self, invoice_id: uuid.UUID, tenant_id: uuid.UUID, status: str) -> InvoiceResponse:
        invoice = await self.repo.get_invoice(invoice_id, tenant_id)
        if not invoice:
            raise NotFoundError("Invoice", invoice_id)
            
        invoice = await self.repo.update_invoice(invoice, status=status)
        invoice = await self.repo.get_invoice(invoice.id, tenant_id)
        return InvoiceResponse.model_validate(invoice)

    async def create_invoice_from_order(self, order) -> InvoiceResponse | None:
        """Create an invoice from a confirmed sales order."""
        if not order or not order.lines:
            return None

        from backend.modules.invoicing.schemas import InvoiceCreate, InvoiceLineCreate

        line_items = []
        for line in order.lines:
            line_items.append(InvoiceLineCreate(
                product_id=line.product_id,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount=line.discount or 0,
                tax_id=getattr(line, 'tax_id', None),
            ))

        invoice_payload = InvoiceCreate(
            contact_id=order.contact_id,
            sales_order_id=order.id,
            type="out_invoice",
            invoice_date=None,
            due_date=None,
            notes=f"Generated from {order.order_number}",
            lines=line_items,
        )

        return await self.create_invoice(order.tenant_id, order.created_by, invoice_payload)

    # ─── Payments ───

    async def create_payment(self, invoice_id: uuid.UUID, tenant_id: uuid.UUID, data: PaymentCreate) -> PaymentResponse:
        invoice = await self.repo.get_invoice(invoice_id, tenant_id)
        if not invoice:
            raise NotFoundError("Invoice", invoice_id)
        
        if invoice.status not in ("open", "paid"):
            raise ValidationError(f"Cannot pay an invoice in {invoice.status} state")
            
        amt = Decimal(str(data.amount))
        residual = Decimal(str(invoice.amount_residual))
        
        if amt > residual:
            raise ValidationError(f"Payment amount ({amt}) exceeds residual amount ({residual})")
            
        payment = await self.repo.create_payment(tenant_id, invoice_id, **data.model_dump())
        
        new_residual = residual - amt
        new_status = "paid" if new_residual <= 0 else invoice.status
        
        await self.repo.update_invoice(invoice, amount_residual=float(new_residual), status=new_status)
        
        return PaymentResponse.model_validate(payment)


# ─── Event Subscriptions ───

async def generate_invoice_from_sales_order(data: dict):
    """Event handler for sales.order.confirmed."""
    # We need a new isolated DB session because event handlers run outside request lifecycle
    from backend.core.database import async_session_factory
    import uuid
    
    order_id = uuid.UUID(data["order_id"])
    tenant_id = uuid.UUID(data["tenant_id"])
    
    async with async_session_factory() as db:
        try:
            sales_repo = SalesRepository(db)
            order = await sales_repo.get_order(order_id, tenant_id)
            if not order:
                return
                
            inv_service = InvoicingService(db)
            
            lines = []
            for line in order.lines:
                lines.append({
                    "product_id": line.product_id,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "discount": line.discount,
                    "tax_id": line.tax_id,
                })
                
            from datetime import date
            
            invoice_data = InvoiceCreate(
                contact_id=order.contact_id,
                sales_order_id=order.id,
                type="out_invoice",
                invoice_date=date.today(),
                due_date=None,
                notes=f"Generated from {order.order_number}",
                lines=[InvoiceLineCreate(**l) for l in lines]
            )
            
            await inv_service.create_invoice(
                tenant_id=tenant_id,
                created_by=order.created_by, # type: ignore - generated internally
                data=invoice_data
            )
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            import logging
            logging.getLogger("erp.events").error(f"Failed to generate invoice for order {order_id}: {e}")


def generate_invoice_from_sales_order_sync(data: dict):
    """Synchronous event handler for sales.order.confirmed (for Celery workers)."""
    from backend.core.database import sync_session_factory
    import uuid
    
    order_id = uuid.UUID(data["order_id"])
    tenant_id = uuid.UUID(data["tenant_id"])
    
    with sync_session_factory() as db:
        try:
            # Get the sales order
            from backend.modules.sales.models import SalesOrder
            order = db.query(SalesOrder).filter(
                SalesOrder.id == order_id,
                SalesOrder.tenant_id == tenant_id
            ).first()
            
            if not order:
                return
                
            # Generate invoice number
            from backend.modules.invoicing.models import Invoice
            count = db.query(Invoice).filter(Invoice.tenant_id == tenant_id).count()
            invoice_number = f"INV-{count + 1:05d}"
            
            # Calculate totals
            amount_untaxed = 0.0
            amount_tax = 0.0
            amount_total = 0.0
            
            lines_data = []
            for line in order.lines:
                unit_price = float(line.unit_price)
                quantity = float(line.quantity)
                discount = float(line.discount or 0)
                
                subtotal = quantity * unit_price * (1.0 - discount / 100.0)
                amount_untaxed += subtotal
                
                # For now, skip tax calculation in sync version
                amount_tax += 0.0
                amount_total += subtotal
                
                lines_data.append({
                    "tenant_id": tenant_id,
                    "product_id": line.product_id,
                    "description": line.description,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount": discount,
                    "tax_id": line.tax_id,
                    "price_subtotal": subtotal,
                    "price_tax": 0.0,
                    "price_total": subtotal,
                })
            
            # Create invoice
            from datetime import date
            invoice = Invoice(
                tenant_id=tenant_id,
                invoice_number=invoice_number,
                contact_id=order.contact_id,
                sales_order_id=order.id,
                status="draft",
                type="out_invoice",
                invoice_date=date.today(),
                amount_untaxed=amount_untaxed,
                amount_tax=amount_tax,
                amount_total=amount_total,
                amount_residual=amount_total,
                notes=f"Generated from {order.order_number}",
                created_by=order.created_by,
            )
            
            db.add(invoice)
            db.flush()  # Get the invoice ID
            
            # Create invoice lines
            from backend.modules.invoicing.models import InvoiceLine
            for line_data in lines_data:
                line_data["invoice_id"] = invoice.id
                invoice_line = InvoiceLine(**line_data)
                db.add(invoice_line)
            
            db.commit()
            
            import logging
            logging.getLogger("erp.events").info(f"Successfully generated invoice {invoice_number} for order {order_id}")
            
        except Exception as e:
            db.rollback()
            import logging
            logging.getLogger("erp.events").error(f"Failed to generate invoice for order {order_id}: {e}")
            raise

async def generate_bill_from_purchase_order(data: dict):
    """Event handler for purchase.order.confirmed -> Creates Vendor Bill (in_invoice)."""
    from backend.core.database import async_session_factory
    from backend.modules.purchase.repository import PurchaseRepository
    
    order_id = uuid.UUID(data["order_id"])
    tenant_id = uuid.UUID(data["tenant_id"])
    
    async with async_session_factory() as db:
        try:
            purchase_repo = PurchaseRepository(db)
            order = await purchase_repo.get_order(order_id, tenant_id)
            if not order:
                return
                
            inv_service = InvoicingService(db)
            
            lines = []
            for line in order.lines:
                lines.append({
                    "product_id": line.product_id,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "discount": 0.0, # Purhcases defaults to 0 discount in basic schema
                    "tax_id": line.tax_id,
                })
                
            from datetime import date
            import uuid
            
            invoice_data = InvoiceCreate(
                contact_id=order.vendor_id,
                # Link back loosely to PO on notes or custom field. No hard constraint needed for phase 3, just document reference.
                type="in_invoice", # Representing Vendor Bill
                invoice_date=date.today(),
                due_date=None,
                notes=f"Generated from {order.order_number}",
                lines=[InvoiceLineCreate(**l) for l in lines]
            )
            
            await inv_service.create_invoice(
                tenant_id=tenant_id,
                created_by=order.created_by,
                data=invoice_data
            )
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            import logging
            logging.getLogger("erp.events").error(f"Failed to generate vendor bill for PO {order_id}: {e}")

# Register listeners
event_bus.subscribe("sales.order.confirmed", generate_invoice_from_sales_order)
event_bus.subscribe("purchase.order.confirmed", generate_bill_from_purchase_order)

