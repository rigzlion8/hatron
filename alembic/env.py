"""Alembic environment configuration for async SQLAlchemy.

This file drives both online (connected to DB) and offline (SQL script)
migration modes. It imports all models to ensure Alembic can auto-detect
schema changes.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from backend.settings import settings

# Alembic Config object
config = context.config

# Set the database URL from our settings (overrides alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─── Import ALL models so Alembic can detect them ───
# The order matters: Base must be imported first, then all models
from backend.core.database import Base
from backend.core.models import BaseModel, TenantModel  # noqa: F401
from backend.modules.auth.models import User, Role, RolePermission, user_roles  # noqa: F401
from backend.modules.contacts.models import Contact, Address  # noqa: F401
from backend.modules.crm.models import CrmActivity, CrmLead, CrmPipeline, CrmStage  # noqa: F401
from backend.modules.sales.models import Product, ProductCategory, SalesOrder, SalesOrderLine  # noqa: F401
from backend.modules.invoicing.models import Invoice, InvoiceLine, Payment, TaxRule  # noqa: F401
from backend.modules.inventory.models import Warehouse, StockLocation, StockQuant, StockPicking, StockMove  # noqa: F401
from backend.modules.purchase.models import PurchaseOrder, PurchaseOrderLine  # noqa: F401
from backend.modules.hr.models import Employee, Department, TimeOffRequest  # noqa: F401
from backend.modules.projects.models import Project, ProjectTask, Timesheet  # noqa: F401
from backend.modules.manufacturing.models import BillOfMaterial, BillOfMaterialLine, ManufacturingOrder  # noqa: F401
from backend.modules.elearning.models import Course, CourseModule, Enrollment  # noqa: F401
from backend.modules.pos.models import POSSession, POSOrder, POSOrderLine  # noqa: F401
from backend.modules.settings.models import SystemSettings  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL without connecting."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with an active connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations — runs the async version."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
