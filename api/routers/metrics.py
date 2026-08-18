"""
Metrics router.

This module defines endpoints for miner metrics operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from api.dependencies import AdminUser, DbSession, OperatorUser, Pagination, ViewerUser
from api.exceptions import NotFoundException
from api.schemas.metric import MetricCreate, MetricListResponse, MetricResponse
from api.services.miner_service import MinerService
from api.services.metric_service import MetricService


router = APIRouter(prefix="/miners/{miner_id}/metrics", tags=["Metrics"])


@router.get(
    "",
    response_model=MetricListResponse,
    summary="GET /api/v1/miners/{miner_id}/metrics - Get miner metrics history",
    responses={
        200: {"description": "List of metrics"},
        401: {"description": "Not authenticated"},
        404: {"description": "Miner not found"},
    },
)
async def list_metrics(
    miner_id: UUID,
    db: DbSession,
    current_user: ViewerUser,
    pagination: Pagination,
    from_dt: Optional[datetime] = Query(
        None,
        description="Filter metrics from this datetime (ISO 8601)",
    ),
    to_dt: Optional[datetime] = Query(
        None,
        description="Filter metrics until this datetime (ISO 8601)",
    ),
) -> MetricListResponse:
    """
    Get paginated metrics history for a miner.

    **Path Parameters:**
    - `miner_id` (UUID, required): Miner unique identifier.

    **Query Parameters:**
    - `page` (int, optional): Page number (1-indexed). Default: 1.
    - `size` (int, optional): Page size (1-100, max 1000). Default: 10.
    - `from_dt` (datetime, optional): Start datetime filter (ISO 8601).
    - `to_dt` (datetime, optional): End datetime filter (ISO 8601).

    **Response 200:** Paginated list of metrics, ordered by recorded_at DESC.
    **Response 401:** Not authenticated.
    **Response 404:** Miner not found.
    """
    # Verify miner exists
    miner = await MinerService.get_miner_by_id(db, miner_id)
    if miner is None:
        raise NotFoundException("Miner", str(miner_id))

    metrics, total = await MetricService.get_metrics(
        db=db,
        miner_id=miner_id,
        from_dt=from_dt,
        to_dt=to_dt,
        page=pagination.page,
        size=pagination.size,
    )

    return MetricListResponse(
        items=[MetricResponse.model_validate(m) for m in metrics],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=MetricService.calculate_pages(total, pagination.size),
    )


@router.post(
    "",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="POST /api/v1/miners/{miner_id}/metrics - Submit a metric snapshot",
    responses={
        201: {"description": "Metric created successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Miner not found"},
        422: {"description": "Validation error"},
    },
)
async def create_metric(
    miner_id: UUID,
    metric_data: MetricCreate,
    db: DbSession,
    current_user: OperatorUser,
) -> MetricResponse:
    """
    Submit a new metric snapshot for a miner.

    **Path Parameters:**
    - `miner_id` (UUID, required): Miner unique identifier.

    **Request Body:**
    - `hashrate_th` (float, required): Hashrate in Terahash/second. Must be >= 0.
    - `temperature_c` (float, required): Temperature in Celsius.
    - `fan_speed_rpm` (int, optional): Fan speed in RPM.
    - `power_watts` (float, required): Power consumption in Watts. Must be >= 0.
    - `accepted_shares` (int, optional): Number of accepted shares. Default: 0.
    - `rejected_shares` (int, optional): Number of rejected shares. Default: 0.
    - `pool_difficulty` (float, optional): Current pool difficulty.

    **Response 201:** Metric created successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Miner not found.
    **Response 422:** Request body validation failed.
    """
    # Verify miner exists
    miner = await MinerService.get_miner_by_id(db, miner_id)
    if miner is None:
        raise NotFoundException("Miner", str(miner_id))

    metric = await MetricService.create_metric(db, miner_id, metric_data)
    return MetricResponse.model_validate(metric)


@router.get(
    "/latest",
    response_model=MetricResponse,
    summary="GET /api/v1/miners/{miner_id}/metrics/latest - Get latest metric for a miner",
    responses={
        200: {"description": "Latest metric"},
        401: {"description": "Not authenticated"},
        404: {"description": "Miner not found or no metrics"},
    },
)
async def get_latest_metric(
    miner_id: UUID,
    db: DbSession,
    current_user: ViewerUser,
) -> MetricResponse:
    """
    Get the most recent metric snapshot for a miner.

    **Path Parameters:**
    - `miner_id` (UUID, required): Miner unique identifier.

    **Response 200:** Latest metric snapshot.
    **Response 401:** Not authenticated.
    **Response 404:** Miner not found or no metrics recorded yet.
    """
    # Verify miner exists
    miner = await MinerService.get_miner_by_id(db, miner_id)
    if miner is None:
        raise NotFoundException("Miner", str(miner_id))

    metric = await MetricService.get_latest_metric(db, miner_id)

    if metric is None:
        raise NotFoundException(
            "Metric", f"No metrics found for miner {miner_id}")

    return MetricResponse.model_validate(metric)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="DELETE /api/v1/miners/{miner_id}/metrics - Delete metrics by date range",
    responses={
        204: {"description": "Metrics deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions (requires admin role)"},
        404: {"description": "Miner not found"},
    },
)
async def delete_metrics(
    miner_id: UUID,
    db: DbSession,
    current_user: AdminUser,
    from_dt: Optional[datetime] = Query(
        None,
        description="Delete metrics from this datetime (ISO 8601)",
    ),
    to_dt: Optional[datetime] = Query(
        None,
        description="Delete metrics until this datetime (ISO 8601)",
    ),
) -> None:
    """
    Bulk delete metrics for a miner within a date range.

    **Path Parameters:**
    - `miner_id` (UUID, required): Miner unique identifier.

    **Query Parameters:**
    - `from_dt` (datetime, optional): Delete metrics from this datetime.
    - `to_dt` (datetime, optional): Delete metrics until this datetime.

    If neither from_dt nor to_dt is specified, ALL metrics for the miner are deleted.

    **Response 204:** Metrics deleted successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have admin role.
    **Response 404:** Miner not found.
    """
    # Verify miner exists
    miner = await MinerService.get_miner_by_id(db, miner_id)
    if miner is None:
        raise NotFoundException("Miner", str(miner_id))

    await MetricService.delete_metrics_by_range(db, miner_id, from_dt, to_dt)
