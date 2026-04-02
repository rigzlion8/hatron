#!/usr/bin/env python3
"""Seed script to populate database with demo data.

Usage:
    python -m scripts.seed_data [--clean]

Options:
    --clean    Clean existing data before seeding
"""

import asyncio
import sys
import os
import uuid
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.settings import settings
from backend.modules.pos.seeds import seed_pos_demo_data

# Import all models to ensure they're registered with SQLAlchemy
from backend.core.models import TenantModel
from backend.core.security import hash_password
from backend.modules.auth.models import User, Role
from backend.modules.contacts.models import Contact
from backend.modules.sales.models import Product, ProductCategory, SalesOrder, SalesOrderLine
from backend.modules.inventory.models import StockMove, StockPicking, StockQuant
from backend.modules.invoicing.models import Invoice, InvoiceLine, Payment
from backend.modules.crm.models import CrmLead, CrmActivity, CrmStage, CrmPipeline
from backend.modules.purchase.models import PurchaseOrder, PurchaseOrderLine


async def seed_database(clean: bool = False):
    """Seed the database with demo data."""

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        if clean:
            print("Cleaning existing data...")
            from sqlalchemy import delete
            from backend.modules.invoicing.models import InvoiceLine, Invoice, Payment
            from backend.modules.purchase.models import PurchaseOrder, PurchaseOrderLine
            from backend.modules.crm.models import CrmLead, CrmActivity, CrmStage, CrmPipeline
            from backend.modules.contacts.models import Contact
            from backend.modules.sales.models import Product, ProductCategory
            from backend.modules.inventory.models import StockMove, StockPicking, StockQuant

            # Delete in dependency order
            await db.execute(delete(CrmActivity))
            await db.execute(delete(CrmLead))
            await db.execute(delete(Payment))
            await db.execute(delete(InvoiceLine))
            await db.execute(delete(Invoice))
            await db.execute(delete(PurchaseOrderLine))
            await db.execute(delete(PurchaseOrder))
            await db.execute(delete(StockMove))
            await db.execute(delete(StockPicking))
            await db.execute(delete(StockQuant))
            await db.execute(delete(Product))
            await db.execute(delete(ProductCategory))
            await db.execute(delete(Contact))
            await db.commit()
            print("Existing data cleaned.")

        # Get or create a demo tenant
        from backend.core.models import TenantModel
        from sqlalchemy import select

        stmt = select(TenantModel).where(TenantModel.name == "Demo Tenant")
        tenant = (await db.execute(stmt)).scalar_one_or_none()

        if not tenant:
            tenant = TenantModel(name="Demo Tenant", slug="demo")
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)
            print(f"Created demo tenant: {tenant.name} ({tenant.id})")
        else:
            print(f"Using existing tenant: {tenant.name} ({tenant.id})")

        # Create admin user for demo, from env vars only (no credentials in code)
        from sqlalchemy import select

        admin_email = os.getenv("SEED_ADMIN_EMAIL")
        admin_password = os.getenv("SEED_ADMIN_PASSWORD")

        if not admin_email or not admin_password:
            raise RuntimeError(
                "SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD must be set in the environment "
                "before running seed_data.py"
            )

        admin_role_stmt = select(Role).where(Role.name == "Admin", Role.tenant_id == tenant.id)
        admin_role = (await db.execute(admin_role_stmt)).scalar_one_or_none()
        if not admin_role:
            admin_role = Role(name="Admin", tenant_id=tenant.id, description="Administrator role", is_system=True)
            db.add(admin_role)
            await db.flush()

        admin_user_stmt = select(User).where(User.email == admin_email, User.tenant_id == tenant.id)
        admin_user = (await db.execute(admin_user_stmt)).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                tenant_id=tenant.id,
                email=admin_email,
                full_name="Admin ERP",
                password_hash=hash_password(admin_password),
                is_active=True,
                is_superuser=True,
            )
            admin_user.roles.append(admin_role)
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            print(f"Created admin user: {admin_user.email}")
        else:
            print(f"Existing admin user found: {admin_user.email}")

        # Seed POS demo data
        print("Seeding POS demo data...")
        await seed_pos_demo_data(db, tenant.id)
        print("Database seeded successfully!")

        print("\nDemo data includes:")
        print("  - 10 products across 3 categories")
        print("  - 6 contacts (customers and vendors)")
        print("  - 6 sales orders with various statuses")
        print("  - 3 purchase orders")
        print("  - Inventory stock levels")
        print("  - CRM pipeline with leads")
        print("  - Invoices and payments")


def main():
    parser = argparse.ArgumentParser(description="Seed database with demo data")
    parser.add_argument("--clean", action="store_true", help="Clean existing data before seeding")
    args = parser.parse_args()

    asyncio.run(seed_database(clean=args.clean))


if __name__ == "__main__":
    main()
