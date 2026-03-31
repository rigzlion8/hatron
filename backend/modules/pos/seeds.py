"""Seeding logic for demo data across all modules."""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from backend.modules.sales.models import Product, ProductCategory, SalesOrder, SalesOrderLine
from backend.modules.contacts.models import Contact
from backend.modules.inventory.models import Warehouse, StockLocation, StockQuant, StockPicking, StockMove
from backend.modules.invoicing.models import Invoice, InvoiceLine, Payment
from backend.modules.crm.models import CrmPipeline, CrmStage, CrmLead
from backend.modules.purchase.models import PurchaseOrder, PurchaseOrderLine


DEMO_PRODUCTS = [
    {"name": "Laptop Pro 14", "price": 189999.00, "cost": 145000.00, "category": "Electronics", "sku": "LP14", "image_url": "/images/products/laptop.png"},
    {"name": "Wireless Mouse", "price": 3999.00, "cost": 2200.00, "category": "Electronics", "sku": "WM01", "image_url": "/images/products/mouse.png"},
    {"name": "Monitor 27-inch", "price": 34500.00, "cost": 26000.00, "category": "Electronics", "sku": "MN27", "image_url": "/images/products/monitor.png"},
    {"name": "USB-C Hub Adapter", "price": 5500.00, "cost": 3200.00, "category": "Electronics", "sku": "USB-HUB", "image_url": "/images/products/laptop.png"},
    {"name": "Espresso Blend", "price": 2500.00, "cost": 1400.00, "category": "Food", "sku": "EB-500", "image_url": "/images/products/coffee.png"},
    {"name": "Organic Green Tea", "price": 1800.00, "cost": 950.00, "category": "Food", "sku": "GT-ORG", "image_url": "/images/products/tea.png"},
    {"name": "Artisan Chocolate", "price": 1200.00, "cost": 680.00, "category": "Food", "sku": "AC-BL", "image_url": "/images/products/chocolate.png"},
    {"name": "Leather Notebook", "price": 4500.00, "cost": 2800.00, "category": "Stationery", "sku": "NB-LEA", "image_url": "/images/products/notebook.png"},
    {"name": "Fountain Pen", "price": 7500.00, "cost": 4800.00, "category": "Stationery", "sku": "FP-01", "image_url": "/images/products/pen.png"},
    {"name": "A4 Paper Ream", "price": 850.00, "cost": 580.00, "category": "Stationery", "sku": "A4-500", "image_url": "/images/products/notebook.png"},
]

DEMO_CONTACTS = [
    {"name": "Acme Corp", "email": "procurement@acmecorp.co.ke", "phone": "+254700111222", "type": "company", "is_customer": True, "is_vendor": False},
    {"name": "Safaricom PLC", "email": "vendor@safaricom.co.ke", "phone": "+254722000000", "type": "company", "is_customer": True, "is_vendor": False},
    {"name": "Nairobi Office Supplies", "email": "sales@nairobioffice.co.ke", "phone": "+254733444555", "type": "company", "is_customer": True, "is_vendor": True},
    {"name": "TechDistributors EA", "email": "info@techdist.co.ke", "phone": "+254711888999", "type": "company", "is_customer": False, "is_vendor": True},
    {"name": "Kariuki James", "email": "james.kariuki@gmail.com", "phone": "+254725123456", "type": "individual", "is_customer": True, "is_vendor": False},
    {"name": "Wanjiku Foods Ltd", "email": "orders@wanjikufoods.co.ke", "phone": "+254734567890", "type": "company", "is_customer": False, "is_vendor": True},
]

async def _get_or_create(db, model, filters: dict, defaults: dict):
    """Helper to fetch or create a record."""
    stmt = select(model)
    for k, v in filters.items():
        stmt = stmt.where(getattr(model, k) == v)
    obj = (await db.execute(stmt)).scalar_one_or_none()
    if not obj:
        obj = model(**{**filters, **defaults})
        db.add(obj)
        await db.flush()
    return obj


async def seed_pos_demo_data(db: AsyncSession, tenant_id: uuid.UUID):
    """Populate database with rich demo data across all ERP modules."""
    
    now = datetime.now(timezone.utc)
    
    # === 1. PRODUCTS & CATEGORIES ===
    categories = {}
    category_names = list(set(p["category"] for p in DEMO_PRODUCTS))
    for cat_name in category_names:
        cat = await _get_or_create(db, ProductCategory,
            {"name": cat_name, "tenant_id": tenant_id}, {})
        categories[cat_name] = cat
        
    created_products = []
    for p_data in DEMO_PRODUCTS:
        stmt = select(Product).where(Product.sku == p_data["sku"], Product.tenant_id == tenant_id)
        product = (await db.execute(stmt)).scalar_one_or_none()
        if product:
            product.name = p_data["name"]
            product.price = p_data["price"]
            product.cost = p_data.get("cost", 0)
            product.image_url = p_data.get("image_url")
            product.category_id = categories[p_data["category"]].id
        else:
            product = Product(
                tenant_id=tenant_id,
                name=p_data["name"],
                price=p_data["price"],
                cost=p_data.get("cost", 0),
                sku=p_data["sku"],
                image_url=p_data.get("image_url"),
                category_id=categories[p_data["category"]].id,
                type="storable"
            )
            db.add(product)
            await db.flush()
        created_products.append(product)

    # === 2. CONTACTS ===
    contacts = []
    for c_data in DEMO_CONTACTS:
        contact = await _get_or_create(db, Contact,
            {"email": c_data["email"], "tenant_id": tenant_id},
            {"type": c_data["type"], "name": c_data["name"], "phone": c_data.get("phone"),
             "is_customer": c_data["is_customer"], "is_vendor": c_data["is_vendor"]})
        contacts.append(contact)

    acme = contacts[0]        # Customer
    safaricom = contacts[1]   # Customer
    nairobi_office = contacts[2]  # Customer + Vendor
    tech_dist = contacts[3]   # Vendor
    kariuki = contacts[4]     # Individual Customer
    wanjiku = contacts[5]     # Vendor

    # === 3. INVENTORY & WAREHOUSES ===
    warehouse = await _get_or_create(db, Warehouse,
        {"code": "WH-MAIN", "tenant_id": tenant_id},
        {"name": "Main Warehouse"})

    loc_types = ["internal", "vendor", "customer"]
    locations = {}
    for ltype in loc_types:
        stmt = select(StockLocation).where(StockLocation.type == ltype, StockLocation.tenant_id == tenant_id).limit(1)
        loc = (await db.execute(stmt)).scalar_one_or_none()
        if not loc:
            loc = StockLocation(
                tenant_id=tenant_id, 
                name=f"{'Stock' if ltype == 'internal' else ltype.capitalize()} Location", 
                type=ltype,
                warehouse_id=warehouse.id if ltype == "internal" else None
            )
            db.add(loc)
            await db.flush()
        locations[ltype] = loc

    # Seed Stock Quants — varied quantities
    stock_amounts = [50, 200, 75, 120, 300, 250, 180, 90, 60, 500]
    for i, prod in enumerate(created_products):
        stmt = select(StockQuant).where(
            StockQuant.product_id == prod.id, 
            StockQuant.location_id == locations["internal"].id,
            StockQuant.tenant_id == tenant_id
        )
        quant = (await db.execute(stmt)).scalar_one_or_none()
        if not quant:
            quant = StockQuant(
                tenant_id=tenant_id, product_id=prod.id, 
                location_id=locations["internal"].id, 
                quantity=float(stock_amounts[i % len(stock_amounts)])
            )
            db.add(quant)

    await db.flush()

    # === 4. SALES ORDERS (Multiple, varied statuses & dates) ===
    
    DEMO_SALES_ORDERS = [
        {
            "number": "SO-DEMO-01",
            "contact": acme,
            "status": "confirmed",
            "days_ago": 15,
            "lines": [
                {"product_idx": 0, "qty": 2},   # 2x Laptop
                {"product_idx": 1, "qty": 5},   # 5x Mouse
            ]
        },
        {
            "number": "SO-DEMO-02",
            "contact": safaricom,
            "status": "confirmed",
            "days_ago": 10,
            "lines": [
                {"product_idx": 2, "qty": 10},  # 10x Monitor
                {"product_idx": 3, "qty": 10},  # 10x USB Hub
                {"product_idx": 1, "qty": 20},  # 20x Mouse
            ]
        },
        {
            "number": "SO-DEMO-03",
            "contact": kariuki,
            "status": "draft",
            "days_ago": 3,
            "lines": [
                {"product_idx": 0, "qty": 1},   # 1x Laptop
                {"product_idx": 7, "qty": 2},   # 2x Notebook
            ]
        },
        {
            "number": "SO-DEMO-04",
            "contact": nairobi_office,
            "status": "confirmed",
            "days_ago": 7,
            "lines": [
                {"product_idx": 9, "qty": 50},  # 50x A4 Paper
                {"product_idx": 8, "qty": 5},   # 5x Pen
                {"product_idx": 7, "qty": 10},  # 10x Notebook
            ]
        },
        {
            "number": "SO-DEMO-05",
            "contact": acme,
            "status": "draft",
            "days_ago": 1,
            "lines": [
                {"product_idx": 4, "qty": 20},  # 20x Coffee
                {"product_idx": 5, "qty": 15},  # 15x Tea
                {"product_idx": 6, "qty": 30},  # 30x Chocolate
            ]
        },
        {
            "number": "SO-DEMO-06",
            "contact": safaricom,
            "status": "confirmed",
            "days_ago": 20,
            "lines": [
                {"product_idx": 0, "qty": 5},   # 5x Laptop
                {"product_idx": 2, "qty": 5},   # 5x Monitor
            ]
        },
    ]

    created_sales_orders = []
    for so_data in DEMO_SALES_ORDERS:
        stmt = select(SalesOrder).where(
            SalesOrder.order_number == so_data["number"], 
            SalesOrder.tenant_id == tenant_id
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            created_sales_orders.append(existing)
            continue
            
        # Calculate totals
        untaxed = 0.0
        for line_spec in so_data["lines"]:
            prod = created_products[line_spec["product_idx"]]
            untaxed += float(prod.price) * line_spec["qty"]
        
        tax = untaxed * 0.16
        total = untaxed + tax
        order_date = now - timedelta(days=so_data["days_ago"])
        
        so = SalesOrder(
            tenant_id=tenant_id,
            order_number=so_data["number"],
            contact_id=so_data["contact"].id,
            status=so_data["status"],
            amount_untaxed=untaxed,
            amount_tax=tax,
            amount_total=total,
            order_date=order_date,
        )
        db.add(so)
        await db.flush()
        
        for line_spec in so_data["lines"]:
            prod = created_products[line_spec["product_idx"]]
            subtotal = float(prod.price) * line_spec["qty"]
            line = SalesOrderLine(
                tenant_id=tenant_id,
                order_id=so.id,
                product_id=prod.id,
                description=prod.name,
                quantity=line_spec["qty"],
                unit_price=float(prod.price),
                price_subtotal=subtotal,
                price_tax=subtotal * 0.16,
                price_total=subtotal * 1.16
            )
            db.add(line)
        
        await db.flush()
        created_sales_orders.append(so)
    
    # === 4b. DELIVERY PICKINGS for confirmed orders ===
    for so in created_sales_orders:
        if so.status != "confirmed":
            continue
        # Check if delivery already exists
        stmt = select(StockPicking).where(
            StockPicking.origin == so.order_number, 
            StockPicking.tenant_id == tenant_id
        )
        existing_picking = (await db.execute(stmt)).scalar_one_or_none()
        if existing_picking:
            continue
            
        picking = StockPicking(
            tenant_id=tenant_id,
            picking_number=f"OUT-{so.order_number}",
            type="outgoing",
            status="done",
            location_id=locations["internal"].id,
            location_dest_id=locations["customer"].id,
            contact_id=so.contact_id,
            origin=so.order_number,
            date_done=so.order_date + timedelta(days=1)
        )
        db.add(picking)
        await db.flush()
        
        # Reload lines (they are lazy='selectin' on model so should be available)
        so_full = await db.get(SalesOrder, so.id, options=[])
        stmt_lines = select(SalesOrderLine).where(SalesOrderLine.order_id == so.id)
        lines_result = await db.execute(stmt_lines)
        so_lines = lines_result.scalars().all()
        
        for line in so_lines:
            move = StockMove(
                tenant_id=tenant_id,
                picking_id=picking.id,
                name=line.description,
                product_id=line.product_id,
                location_id=locations["internal"].id,
                location_dest_id=locations["customer"].id,
                quantity=float(line.quantity),
                quantity_done=float(line.quantity),
                status="done"
            )
            db.add(move)
    
    await db.flush()
    
    # === 5. INVOICES from confirmed orders ===
    for i, so in enumerate(created_sales_orders):
        if so.status != "confirmed":
            continue
        inv_number = f"INV-DEMO-{i+1:02d}"
        stmt = select(Invoice).where(Invoice.invoice_number == inv_number, Invoice.tenant_id == tenant_id)
        existing_inv = (await db.execute(stmt)).scalar_one_or_none()
        if existing_inv:
            continue
        
        # First confirmed order: fully paid; Second: partial; Third: open
        if i == 0:
            inv_status = "paid"
            residual = 0.0
        elif i == 1:
            inv_status = "open"
            residual = float(so.amount_total) * 0.4  # 60% paid
        else:
            inv_status = "open"
            residual = float(so.amount_total)
            
        inv = Invoice(
            tenant_id=tenant_id,
            invoice_number=inv_number,
            contact_id=so.contact_id,
            sales_order_id=so.id,
            status=inv_status,
            type="out_invoice",
            amount_untaxed=so.amount_untaxed,
            amount_tax=so.amount_tax,
            amount_total=so.amount_total,
            amount_residual=residual
        )
        db.add(inv)
        await db.flush()
        
        # Invoice lines
        stmt_lines = select(SalesOrderLine).where(SalesOrderLine.order_id == so.id)
        lines_result = await db.execute(stmt_lines)
        for line in lines_result.scalars().all():
            il = InvoiceLine(
                tenant_id=tenant_id,
                invoice_id=inv.id,
                product_id=line.product_id,
                description=line.description,
                quantity=float(line.quantity),
                unit_price=float(line.unit_price),
                price_subtotal=float(line.price_subtotal),
                price_tax=float(line.price_tax),
                price_total=float(line.price_total)
            )
            db.add(il)
        
        # Create payment records for paid/partial invoices
        if inv_status == "paid":
            payment = Payment(
                tenant_id=tenant_id,
                invoice_id=inv.id,
                amount=float(so.amount_total),
                payment_method="bank_transfer",
                reference=f"PAY-{inv_number}"
            )
            db.add(payment)
        elif residual < float(so.amount_total):
            # Partial payment
            paid_amount = float(so.amount_total) - residual
            payment = Payment(
                tenant_id=tenant_id,
                invoice_id=inv.id,
                amount=paid_amount,
                payment_method="mpesa",
                reference=f"MPESA-{inv_number}"
            )
            db.add(payment)

    await db.flush()
    
    # === 6. PURCHASE ORDERS ===
    DEMO_PURCHASE_ORDERS = [
        {
            "number": "PO-DEMO-01",
            "vendor": tech_dist, 
            "status": "confirmed",
            "days_ago": 12,
            "lines": [
                {"product_idx": 0, "qty": 20},  # 20x Laptop (at cost)
                {"product_idx": 2, "qty": 15},  # 15x Monitor
            ]
        },
        {
            "number": "PO-DEMO-02",
            "vendor": wanjiku,
            "status": "confirmed",
            "days_ago": 8,
            "lines": [
                {"product_idx": 4, "qty": 100},  # 100x Coffee
                {"product_idx": 5, "qty": 80},   # 80x Tea
                {"product_idx": 6, "qty": 50},   # 50x Chocolate
            ]
        },
        {
            "number": "PO-DEMO-03",
            "vendor": nairobi_office,
            "status": "draft",
            "days_ago": 2,
            "lines": [
                {"product_idx": 9, "qty": 200},  # 200x A4 Paper
                {"product_idx": 8, "qty": 20},   # 20x Pen
            ]
        },
    ]
    
    for po_data in DEMO_PURCHASE_ORDERS:
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.order_number == po_data["number"],
            PurchaseOrder.tenant_id == tenant_id
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            continue
            
        untaxed = 0.0
        for line_spec in po_data["lines"]:
            prod = created_products[line_spec["product_idx"]]
            untaxed += float(prod.cost) * line_spec["qty"]
        
        tax = untaxed * 0.16
        total = untaxed + tax
        order_date = now - timedelta(days=po_data["days_ago"])
        
        po = PurchaseOrder(
            tenant_id=tenant_id,
            order_number=po_data["number"],
            vendor_id=po_data["vendor"].id,
            status=po_data["status"],
            amount_untaxed=untaxed,
            amount_tax=tax,
            amount_total=total,
            order_date=order_date,
        )
        db.add(po)
        await db.flush()
        
        for line_spec in po_data["lines"]:
            prod = created_products[line_spec["product_idx"]]
            subtotal = float(prod.cost) * line_spec["qty"]
            line = PurchaseOrderLine(
                tenant_id=tenant_id,
                order_id=po.id,
                product_id=prod.id,
                description=prod.name,
                quantity=line_spec["qty"],
                unit_price=float(prod.cost),
                price_subtotal=subtotal,
                price_tax=subtotal * 0.16,
                price_total=subtotal * 1.16
            )
            db.add(line)
        
        await db.flush()
        
        # Create incoming receipts for confirmed POs
        if po_data["status"] == "confirmed":
            receipt = StockPicking(
                tenant_id=tenant_id,
                picking_number=f"IN-{po_data['number']}",
                type="incoming",
                status="done",
                location_id=locations["vendor"].id,
                location_dest_id=locations["internal"].id,
                contact_id=po_data["vendor"].id,
                origin=po_data["number"],
                date_done=order_date + timedelta(days=2)
            )
            db.add(receipt)
            await db.flush()
            
            for line_spec in po_data["lines"]:
                prod = created_products[line_spec["product_idx"]]
                move = StockMove(
                    tenant_id=tenant_id,
                    picking_id=receipt.id,
                    name=prod.name,
                    product_id=prod.id,
                    location_id=locations["vendor"].id,
                    location_dest_id=locations["internal"].id,
                    quantity=line_spec["qty"],
                    quantity_done=line_spec["qty"],
                    status="done"
                )
                db.add(move)

    await db.flush()

    # === 7. CRM PIPELINES & LEADS ===
    stmt = select(CrmPipeline).where(CrmPipeline.name == "B2B Sales", CrmPipeline.tenant_id == tenant_id)
    pipeline = (await db.execute(stmt)).scalar_one_or_none()
    
    if not pipeline:
        pipeline = CrmPipeline(tenant_id=tenant_id, name="B2B Sales", is_default=True)
        db.add(pipeline)
        await db.flush()
        
        stages_data = [
            {"name": "New", "sequence": 10, "probability": 10.0},
            {"name": "Qualified", "sequence": 20, "probability": 40.0},
            {"name": "Proposition", "sequence": 30, "probability": 70.0},
            {"name": "Won", "sequence": 40, "probability": 100.0, "fold": True}
        ]
        
        stages = []
        for s in stages_data:
            stages.append(CrmStage(pipeline_id=pipeline.id, **s))
        db.add_all(stages)
        await db.flush()
        
        # Multiple demo leads across stages
        demo_leads = [
            {"name": "Q4 Server Upgrade Project", "contact": acme, "stage_idx": 1, "revenue": 250000.0, "priority": 2},
            {"name": "Office Equipment Refit", "contact": None, "stage_idx": 0, "revenue": 45000.0, "priority": 1},
            {"name": "Safaricom Branch Rollout", "contact": safaricom, "stage_idx": 2, "revenue": 1200000.0, "priority": 3},
            {"name": "Kariuki Home Office Setup", "contact": kariuki, "stage_idx": 0, "revenue": 85000.0, "priority": 1},
            {"name": "NOS Stationery Contract", "contact": nairobi_office, "stage_idx": 1, "revenue": 320000.0, "priority": 2},
        ]
        
        for lead_data in demo_leads:
            lead = CrmLead(
                tenant_id=tenant_id,
                name=lead_data["name"],
                contact_id=lead_data["contact"].id if lead_data["contact"] else None,
                stage_id=stages[lead_data["stage_idx"]].id,
                expected_revenue=lead_data["revenue"],
                probability=stages[lead_data["stage_idx"]].probability,
                priority=lead_data["priority"],
                status="open"
            )
            db.add(lead)

    await db.commit()
