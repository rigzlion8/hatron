"""In-process event bus for cross-module communication.

Modules publish events when business actions occur. Other modules
subscribe to these events without creating direct dependencies.

When a module is eventually extracted to a microservice, this bus
can be swapped for RabbitMQ/Kafka with minimal code changes.
"""

import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

from backend.settings import settings

logger = logging.getLogger(__name__)

# Type alias for async event handlers
EventHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class EventBus:
    """Simple in-process async event bus.

    Usage:
        # Publishing (in sales module)
        await EventBus.publish("sales.order.confirmed", {"order_id": "..."})

        # Subscribing (in invoicing module)
        @EventBus.on("sales.order.confirmed")
        async def handle_order_confirmed(payload):
            await create_invoice(payload["order_id"])
    """

    _handlers: dict[str, list[EventHandler]] = defaultdict(list)

    @classmethod
    def on(cls, event_type: str) -> Callable:
        """Decorator to register an event handler.

        Args:
            event_type: Event name in format "module.resource.action"
        """

        def decorator(func: EventHandler) -> EventHandler:
            cls._handlers[event_type].append(func)
            logger.debug(
                f"Registered handler {func.__name__} for event '{event_type}'"
            )
            return func

        return decorator

    @classmethod
    def subscribe(cls, event_type: str, handler: EventHandler) -> None:
        """Programmatically subscribe a handler to an event type."""
        cls._handlers[event_type].append(handler)

    @classmethod
    async def publish(cls, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event by dispatching it to the Celery background queue.
        
        This moves heavy automated workflows (like drafting invoices from confirmed orders)
        out of the HTTP request-response cycle and into isolated background workers.
        """
        handlers = cls._handlers.get(event_type, [])
        if not handlers:
            logger.debug(f"No handlers mapping to '{event_type}', ignoring.")
            return

        logger.info(
            f"Enqueueing event '{event_type}' explicitly to Celery background task worker "
            f"({len(handlers)} handler(s) will execute offline)."
        )

        try:
            from backend.workers.tasks import dispatch_event
        except Exception as e:
            logger.warning(f"Celery not available, running event handlers inline: {e}")
            # Fallback: execute handlers immediately in current process
            async def run_handlers():
                results = await asyncio.gather(*[h(payload) for h in handlers], return_exceptions=True)
                for idx, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Handler {handlers[idx].__name__} failed: {result}", exc_info=result)

            import asyncio
            await run_handlers()
            return

        # Dispatch the celery task
        # We fire and forget, utilizing Celery's `.delay` syntactic sugar
        try:
            dispatch_event.delay(event_type, payload)
        except AttributeError:
            # If Celery is not installed or .delay unavailable, run inline for local dev.
            logger.info("dispatch_event has no delay; executing inline.")
            async def run_handlers():
                results = await asyncio.gather(*[h(payload) for h in handlers], return_exceptions=True)
                for idx, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Handler {handlers[idx].__name__} failed: {result}", exc_info=result)

            import asyncio
            await run_handlers()

    @classmethod
    def clear(cls) -> None:
        """Clear all handlers. Useful for testing."""
        cls._handlers.clear()


# Create a singleton instance for global use
event_bus = EventBus()
