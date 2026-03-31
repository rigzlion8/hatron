"""POS (Point of Sale) API Router."""

import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_db, get_current_user
from backend.modules.auth.models import User
from backend.modules.pos.models import POSSession, POSOrder, POSOrderLine
from backend.modules.pos.schemas import (
    POSSessionCreate,
    POSSessionResponse,
    POSOrderCreate,
    POSOrderResponse,
    POSSetupRequest,
    POSProductResponse,
    MpesaSTKPushRequest,
    MpesaSTKPushResponse,
    MpesaStatusRequest,
    PaystackInitRequest,
    PaystackInitResponse,
    PaystackVerifyResponse
)
from backend.modules.pos.seeds import seed_pos_demo_data
from backend.modules.sales.models import Product, ProductCategory, SalesOrder, SalesOrderLine
from backend.modules.inventory.models import StockQuant, StockMove, StockPicking
from sqlalchemy import select, delete

logger = logging.getLogger("erp.pos")

router = APIRouter(prefix="/pos", tags=["Point of Sale"])


@router.post("/setup")
async def setup_pos(
    data: POSSetupRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Initial POS configuration — optional demo data seeding or cleaning."""
    if data.mode == "demo":
        await seed_pos_demo_data(db, user.tenant_id)
        return {"status": "success", "message": "Demo data populated."}
    elif data.mode == "clean":
        from backend.modules.invoicing.models import InvoiceLine, Invoice, Payment
        from backend.modules.purchase.models import PurchaseOrder, PurchaseOrderLine
        from backend.modules.crm.models import CrmLead, CrmActivity, CrmStage, CrmPipeline
        from backend.modules.contacts.models import Contact

        # Delete in FK dependency order (children first)

        # CRM
        await db.execute(delete(CrmActivity).where(CrmActivity.tenant_id == user.tenant_id))
        await db.execute(delete(CrmLead).where(CrmLead.tenant_id == user.tenant_id))
        # Stages have no tenant_id; delete via pipeline
        from sqlalchemy import select as sel
        pipeline_ids = (await db.execute(
            sel(CrmPipeline.id).where(CrmPipeline.tenant_id == user.tenant_id)
        )).scalars().all()
        if pipeline_ids:
            await db.execute(delete(CrmStage).where(CrmStage.pipeline_id.in_(pipeline_ids)))
        await db.execute(delete(CrmPipeline).where(CrmPipeline.tenant_id == user.tenant_id))

        # Invoicing (payments -> invoice lines -> invoices)
        await db.execute(delete(Payment).where(Payment.tenant_id == user.tenant_id))
        await db.execute(delete(InvoiceLine).where(InvoiceLine.tenant_id == user.tenant_id))
        await db.execute(delete(Invoice).where(Invoice.tenant_id == user.tenant_id))

        # Purchase (lines -> orders)
        await db.execute(delete(PurchaseOrderLine).where(PurchaseOrderLine.tenant_id == user.tenant_id))
        await db.execute(delete(PurchaseOrder).where(PurchaseOrder.tenant_id == user.tenant_id))

        # POS
        await db.execute(delete(POSOrderLine).where(POSOrderLine.tenant_id == user.tenant_id))
        await db.execute(delete(POSOrder).where(POSOrder.tenant_id == user.tenant_id))
        await db.execute(delete(POSSession).where(POSSession.tenant_id == user.tenant_id))

        # Sales (orders -> lines to avoid FK issues)
        await db.execute(delete(SalesOrder).where(SalesOrder.tenant_id == user.tenant_id))
        await db.execute(delete(SalesOrderLine).where(SalesOrderLine.tenant_id == user.tenant_id))

        # Stock
        await db.execute(delete(StockMove).where(StockMove.tenant_id == user.tenant_id))
        await db.execute(delete(StockPicking).where(StockPicking.tenant_id == user.tenant_id))
        await db.execute(delete(StockQuant).where(StockQuant.tenant_id == user.tenant_id))

        # Catalog (delete products AFTER sales_order_lines are cleared)
        await db.execute(delete(Product).where(Product.tenant_id == user.tenant_id))
        await db.execute(delete(ProductCategory).where(ProductCategory.tenant_id == user.tenant_id))

        # Contacts
        await db.execute(delete(Contact).where(Contact.tenant_id == user.tenant_id))

        await db.commit()
        return {"status": "success", "message": "Database cleaned and ready for new inventory."}
    return {"status": "success", "message": "No action taken."}


@router.get("/products", response_model=List[POSProductResponse])
async def list_pos_products(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get all products available for the POS terminal."""
    # Joint select to get category names
    stmt = (
        select(Product, ProductCategory.name.label("category_name"))
        .outerjoin(ProductCategory, Product.category_id == ProductCategory.id)
        .where(Product.tenant_id == user.tenant_id, Product.is_active == True)
    )
    result = await db.execute(stmt)
    
    products = []
    for row in result:
        p, cat_name = row
        products.append(POSProductResponse(
            id=p.id,
            name=p.name,
            price=float(p.price),
            sku=p.sku,
            image_url=p.image_url,
            category_name=cat_name
        ))
    return products


@router.post("/sessions", response_model=POSSessionResponse)
async def open_session(
    data: POSSessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Open a new POS register session."""
    session = POSSession(
        tenant_id=user.tenant_id,
        user_id=user.id,
        name=data.name,
        opening_balance=data.opening_balance,
        status="open"
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=List[POSSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all POS sessions for the current tenant."""
    stmt = select(POSSession).where(POSSession.tenant_id == user.tenant_id).order_by(POSSession.start_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/orders", response_model=POSOrderResponse)
async def create_order(
    data: POSOrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Create the POS Order first
    order = POSOrder(
        tenant_id=user.tenant_id,
        session_id=data.session_id,
        order_reference=data.order_reference,
        contact_id=data.contact_id,
        amount_total=data.amount_total,
        amount_tax=data.amount_tax,
        amount_paid=data.amount_paid,
        amount_return=data.amount_return,
        payment_method=data.payment_method,
    )
    db.add(order)
    await db.flush()

    # --- Unified Sales Module Sync ---
    # Create a shadow SalesOrder so this retail sale appears in Sales reporting
    sales_order = SalesOrder(
        tenant_id=user.tenant_id,
        order_number=f"SO-{order.order_reference}",
        contact_id=order.contact_id,  # None for walk-in customers (allowed now)
        status="confirmed",  # POS sales are always confirmed
        amount_untaxed=float(order.amount_total) - float(order.amount_tax),
        amount_tax=float(order.amount_tax),
        amount_total=float(order.amount_total),
        customer_reference=f"POS Terminal: {order.order_reference}",
        created_by=user.id
    )
    db.add(sales_order)
    await db.flush()

    for line_data in data.lines:
        line = POSOrderLine(
            tenant_id=user.tenant_id,
            order_id=order.id,
            product_id=line_data.product_id,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            price_subtotal=line_data.price_subtotal
        )
        db.add(line)
        
        so_line = SalesOrderLine(
            tenant_id=user.tenant_id,
            order_id=sales_order.id,
            product_id=line_data.product_id,
            description="POS Item",
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            price_subtotal=line_data.price_subtotal,
            price_total=line_data.price_subtotal
        )
        db.add(so_line)
    
    await db.commit()
    await db.refresh(order)
    return order


# ─── Payment Endpoints ───

@router.post("/payments/mpesa/initiate", response_model=MpesaSTKPushResponse)
async def initiate_mpesa_payment(
    data: MpesaSTKPushRequest,
    user: User = Depends(get_current_user)
):
    """Initiate an M-Pesa STK Push to the customer's phone."""
    from backend.modules.pos.payment_service import mpesa_service

    try:
        result = await mpesa_service.initiate_stk_push(
            phone_number=data.phone_number,
            amount=data.amount,
            order_reference=data.order_reference,
            description=f"POS Payment - {data.order_reference}"
        )

        # Check if the API returned success
        response_code = result.get("ResponseCode", "")
        if response_code == "0":
            return MpesaSTKPushResponse(
                success=True,
                checkout_request_id=result.get("CheckoutRequestID"),
                merchant_request_id=result.get("MerchantRequestID"),
                response_description=result.get("ResponseDescription")
            )
        else:
            return MpesaSTKPushResponse(
                success=False,
                error=result.get("ResponseDescription", "STK Push failed")
            )
    except Exception as e:
        logger.error(f"M-Pesa STK Push error: {e}")
        return MpesaSTKPushResponse(
            success=False,
            error=str(e)
        )


@router.post("/payments/mpesa/status")
async def check_mpesa_status(
    data: MpesaStatusRequest,
    user: User = Depends(get_current_user)
):
    """Check the status of an M-Pesa STK Push payment."""
    from backend.modules.pos.payment_service import mpesa_service

    try:
        result = await mpesa_service.query_stk_status(data.checkout_request_id)
        result_code = result.get("ResultCode")
        
        return {
            "success": result_code == "0" or result_code == 0,
            "result_code": result_code,
            "result_desc": result.get("ResultDesc", ""),
            "raw": result
        }
    except Exception as e:
        logger.error(f"M-Pesa status query error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/payments/mpesa/callback")
async def mpesa_callback(request: Request):
    """
    M-Pesa callback webhook — receives payment confirmation from Safaricom.
    This endpoint is called by M-Pesa servers, no auth required.
    """
    from backend.modules.pos.payment_service import MpesaService

    try:
        data = await request.json()
        logger.info(f"M-Pesa callback received: {data}")
        parsed = MpesaService.parse_callback(data)
        logger.info(f"M-Pesa parsed callback: {parsed}")

        # TODO: Update order payment status in DB based on parsed result
        # For now, just log and acknowledge
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    except Exception as e:
        logger.error(f"M-Pesa callback error: {e}")
        return {"ResultCode": 1, "ResultDesc": str(e)}


@router.post("/payments/paystack/initiate", response_model=PaystackInitResponse)
async def initiate_paystack_payment(
    data: PaystackInitRequest,
    user: User = Depends(get_current_user)
):
    """Initialize a Paystack payment transaction."""
    from backend.modules.pos.payment_service import paystack_service

    try:
        result = await paystack_service.initialize_transaction(
            email=data.email,
            amount=data.amount,
            reference=data.reference,
            callback_url=data.callback_url,
            metadata={"user_id": str(user.id), "tenant_id": str(user.tenant_id)}
        )

        if result.get("status"):
            tx_data = result.get("data", {})
            return PaystackInitResponse(
                success=True,
                authorization_url=tx_data.get("authorization_url"),
                access_code=tx_data.get("access_code"),
                reference=tx_data.get("reference")
            )
        else:
            return PaystackInitResponse(
                success=False,
                error=result.get("message", "Paystack initialization failed")
            )
    except Exception as e:
        logger.error(f"Paystack init error: {e}")
        return PaystackInitResponse(success=False, error=str(e))


@router.get("/payments/paystack/verify/{reference}", response_model=PaystackVerifyResponse)
async def verify_paystack_payment(
    reference: str,
    user: User = Depends(get_current_user)
):
    """Verify a Paystack payment by its reference."""
    from backend.modules.pos.payment_service import paystack_service

    try:
        result = await paystack_service.verify_transaction(reference)

        if result.get("status"):
            tx_data = result.get("data", {})
            return PaystackVerifyResponse(
                success=True,
                status=tx_data.get("status"),
                amount=tx_data.get("amount", 0) / 100,  # Convert from kobo
                currency=tx_data.get("currency"),
                reference=tx_data.get("reference")
            )
        else:
            return PaystackVerifyResponse(
                success=False,
                error=result.get("message", "Verification failed")
            )
    except Exception as e:
        logger.error(f"Paystack verify error: {e}")
        return PaystackVerifyResponse(success=False, error=str(e))
