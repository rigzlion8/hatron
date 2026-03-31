"""Celery tasks for background processing."""

import asyncio
import logging
from typing import Any

from backend.workers.celery_app import celery_app
from backend.core.events import EventBus

logger = logging.getLogger(__name__)

# Note: We avoid importing 'application' from backend.main here at top-level 
# to prevent circular dependencies (Main -> Modules -> Events -> Tasks -> Main).
# Our EventHandlers are registered in the EventBus class's _handlers during 
# module imports, which happen during the server initialization.

@celery_app.task(name="dispatch_event")
def dispatch_event(event_type: str, payload: dict[str, Any]) -> None:
    """A generic Celery task that executes async EventBus handlers in a dedicated loop.
    
    This acts as the bridge separating the synchronous Celery execution from our modern 
    asyncpg database and web framework handlers.
    """
    logger.info(f"Celery received event: {event_type}")
    
    # We lazily ensuring modules are registered locally if we are inside a 
    # separate worker process that didn't boot the full FastAPI app yet.
    # However, in a standard dev run, the EventBus handlers should be already present.
    
    handlers = EventBus._handlers.get(event_type, [])
    if not handlers:
        logger.warning(f"No handlers found for event: {event_type} inside Celery process.")
        return

    # Create a new event loop for this specific task execution
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info(f"Executing {len(handlers)} handler(s) for event '{event_type}'")
        
        async def run_all():
            tasks = [handler(payload) for handler in handlers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for handler_idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Handler {handlers[handler_idx].__name__} failed: {result}", 
                        exc_info=result
                    )
                    
        loop.run_until_complete(run_all())
    finally:
        loop.close()
