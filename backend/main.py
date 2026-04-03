"""FastAPI application factory and configuration.

This is the main entry point — registers all middleware, exception handlers,
and module routers.
"""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.core.exceptions import ERPException
from backend.core.middleware.logging import RequestLoggingMiddleware
from backend.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("erp")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Ensure all models are loaded into Metadata
    from backend.core.models import TenantModel # noqa
    from backend.modules.auth.models import User, Role # noqa
    from backend.modules.pos.models import POSSession, POSOrder # noqa

    application = FastAPI(
        title=settings.APP_NAME,
        description="Modular ERP System — API Documentation",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ─── Middleware (order matters: last added = first executed) ───
    # CORSMiddleware must be outermost (added last) so it always
    # injects CORS headers — even on 500 error responses.

    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Exception Handlers ───

    @application.exception_handler(ERPException)
    async def erp_exception_handler(request: Request, exc: ERPException):
        """Handle all custom business exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.code,
                "message": exc.message,
            },
        )

    @application.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions with file-based logging."""
        import traceback
        tb = traceback.format_exc()
        logger.exception(f"Unhandled exception: {exc}")
        
        with open("backend_error.log", "a") as f:
            f.write(f"\n--- ERROR AT {request.url} ---\n")
            f.write(tb)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": str(exc),
                "traceback": tb if settings.DEBUG else None
            },
        )

    # ─── Routes ───

    @application.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring."""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "environment": settings.APP_ENV,
        }

    # Register module routers
    _register_routers(application)

    # ─── Static Files ───
    # Mount uploads directory for serving uploaded files
    uploads_dir = settings.UPLOAD_DIR
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    application.mount("/api/v1/uploads", StaticFiles(directory=uploads_dir), name="uploads")

    logger.info(
        f"🚀 {settings.APP_NAME} initialized "
        f"(env={settings.APP_ENV}, debug={settings.DEBUG})"
    )

    return application


def _register_routers(application: FastAPI) -> None:
    """Register all module routers under the API version prefix."""
    from backend.modules.auth.router import router as auth_router
    from backend.modules.contacts.router import router as contacts_router
    
    # Phase 2
    from backend.modules.crm.router import router as crm_router
    from backend.modules.sales.router import sales_router
    from backend.modules.sales.router import products_router
    from backend.modules.invoicing.router import router as invoicing_router
    
    # Phase 3
    from backend.modules.hr.router import router as hr_router
    from backend.modules.pos.router import router as pos_router
    from backend.modules.elearning.router import router as elearning_router
    from backend.modules.inventory.router import router as inventory_router
    from backend.modules.purchase.router import router as purchase_router
    from backend.modules.property.router import router as property_router
    from backend.modules.school.router import router as school_router
    from backend.modules.settings.router import router as settings_router

    prefix = settings.API_V1_PREFIX
    
    @application.get(f"{prefix}/health", tags=["System"])
    async def api_health_check():
        return {"status": "ok", "message": "API V1 is up and running"}

    application.include_router(auth_router, prefix=prefix)
    application.include_router(contacts_router, prefix=prefix)
    application.include_router(crm_router, prefix=prefix)
    application.include_router(products_router, prefix=prefix)
    application.include_router(sales_router, prefix=prefix)
    application.include_router(invoicing_router, prefix=prefix)
    application.include_router(hr_router, prefix=prefix)
    application.include_router(pos_router, prefix=prefix)
    application.include_router(elearning_router, prefix=prefix)
    application.include_router(inventory_router, prefix=prefix)
    application.include_router(purchase_router, prefix=prefix)
    application.include_router(property_router, prefix=prefix)
    application.include_router(school_router, prefix=prefix)
    application.include_router(settings_router, prefix=prefix)


# Create the app instance
app = create_app()
