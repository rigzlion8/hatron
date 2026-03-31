"""Pagination utilities supporting both offset and cursor-based pagination."""

import math
from dataclasses import dataclass

from fastapi import Query
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.schemas import PaginatedResponse, PaginationMeta


@dataclass
class PaginationParams:
    """Standard pagination parameters extracted from query string."""

    page: int = 1
    per_page: int = 20


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    """FastAPI dependency for pagination query parameters."""
    return PaginationParams(page=page, per_page=per_page)


async def paginate(
    db: AsyncSession,
    query: Select,
    params: PaginationParams,
    response_schema,
) -> PaginatedResponse:
    """Execute a paginated query and return a PaginatedResponse.

    Args:
        db: Async database session.
        query: SQLAlchemy select statement (before limit/offset).
        params: Pagination parameters.
        response_schema: Pydantic schema class to serialize each row.

    Returns:
        PaginatedResponse with data and meta.
    """
    # Count total rows
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Calculate pagination
    total_pages = math.ceil(total / params.per_page) if total > 0 else 0
    offset = (params.page - 1) * params.per_page

    # Fetch page data
    paginated_query = query.offset(offset).limit(params.per_page)
    result = await db.execute(paginated_query)
    rows = result.scalars().all()

    # Serialize
    data = [response_schema.model_validate(row) for row in rows]

    meta = PaginationMeta(
        total=total,
        page=params.page,
        per_page=params.per_page,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_prev=params.page > 1,
    )

    return PaginatedResponse(data=data, meta=meta)
