"""Request logging middleware for observability."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("erp.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with timing, status, and correlation ID."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.monotonic()

        # Inject request ID for downstream logging
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = time.monotonic() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"FAILED in {duration:.3f}s — {type(exc).__name__}: {exc}"
            )
            raise

        duration = time.monotonic() - start_time
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"→ {response.status_code} in {duration:.3f}s"
        )

        response.headers["X-Request-ID"] = request_id
        return response
