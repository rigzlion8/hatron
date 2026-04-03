"""Celery tasks for background processing."""

import asyncio
import logging
from typing import Any

from backend.workers.celery_app import celery_app
from backend.core.events import EventBus

logger = logging.getLogger(__name__)

# Import modules to register event handlers in the Celery worker process
# This ensures event handlers are available when Celery runs in a separate process
import backend.modules.invoicing.service  # noqa: F401
import backend.modules.purchase.service  # noqa: F401

# Note: We avoid importing 'application' from backend.main here at top-level 
# to prevent circular dependencies (Main -> Modules -> Events -> Tasks -> Main).
# Our EventHandlers are registered in the EventBus class's _handlers during 
# module imports, which happen during the server initialization.

@celery_app.task(name="dispatch_event")
def dispatch_event(event_type: str, payload: dict[str, Any]) -> None:
    """A synchronous Celery task that executes event handlers.
    
    This acts as the bridge between the synchronous Celery execution 
    and our event-driven system.
    """
    logger.info(f"Celery received event: {event_type}")
    
    # We lazily ensuring modules are registered locally if we are inside a 
    # separate worker process that didn't boot the full FastAPI app yet.
    # However, in a standard dev run, the EventBus handlers should be already present.
    
    handlers = EventBus._handlers.get(event_type, [])
    if not handlers:
        logger.warning(f"No handlers found for event: {event_type} inside Celery process.")
        return

    logger.info(f"Executing {len(handlers)} handler(s) for event '{event_type}'")
    
    # For now, we have a special case for sales.order.confirmed
    # In the future, we should make all event handlers synchronous
    if event_type == "sales.order.confirmed":
        from backend.modules.invoicing.service import generate_invoice_from_sales_order_sync
        try:
            generate_invoice_from_sales_order_sync(payload)
            logger.info("Handler generate_invoice_from_sales_order_sync completed successfully")
        except Exception as e:
            logger.error(f"Handler generate_invoice_from_sales_order_sync failed: {e}", exc_info=e)
    else:
        # For other events, try to execute them synchronously
        # This is a temporary solution until all handlers are made synchronous
        for handler in handlers:
            try:
                # If it's a coroutine function, we can't call it directly
                if hasattr(handler, '__call__'):
                    logger.warning(f"Skipping async handler {handler.__name__} - not supported in sync context")
                else:
                    handler(payload)
                    logger.info(f"Handler {handler.__name__} completed successfully")
            except Exception as e:
                logger.error(f"Handler {handler.__name__} failed: {e}", exc_info=e)
