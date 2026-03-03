"""
Alerts router.

This module defines endpoints for alert operations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from api.dependencies import AdminUser, DbSession, OperatorUser, Pagination, ViewerUser
from api.exceptions import BadRequestException, NotFoundException
from api.models.alert import AlertSeverity, AlertType
from api.schemas.alert import AlertCreate, AlertListResponse, AlertResponse
from api.services.alert_service import AlertService
from api.services.farm_service import FarmService
from api.services.miner_service import MinerService


router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List alerts with filters",
    responses={
        200: {"description": "List of alerts"},
        401: {"description": "Not authenticated"},
    },
)
async def list_alerts(
    db: DbSession,
    current_user: ViewerUser,
    pagination: Pagination,
    farm_id: Optional[UUID] = Query(
        None,
        description="Filter by farm ID",
    ),
    miner_id: Optional[UUID] = Query(
        None,
        description="Filter by miner ID",
    ),
    severity: Optional[AlertSeverity] = Query(
        None,
        description="Filter by severity (info, warning, critical)",
    ),
    alert_type: Optional[AlertType] = Query(
        None,
        description="Filter by type (high_temp, low_hashrate, offline, power_spike, custom)",
    ),
    is_acknowledged: Optional[bool] = Query(
        None,
        description="Filter by acknowledgment status",
    ),
) -> AlertListResponse:
    """
    Get paginated list of alerts with optional filters.
    
    **Query Parameters:**
    - `page` (int, optional): Page number (1-indexed). Default: 1.
    - `size` (int, optional): Page size (1-100). Default: 10.
    - `farm_id` (UUID, optional): Filter by farm.
    - `miner_id` (UUID, optional): Filter by miner.
    - `severity` (str, optional): Filter by severity (info, warning, critical).
    - `alert_type` (str, optional): Filter by type.
    - `is_acknowledged` (bool, optional): Filter by acknowledgment status.
    
    **Response 200:** Paginated list of alerts, ordered by created_at DESC.
    **Response 401:** Not authenticated.
    """
    alerts, total = await AlertService.get_alerts(
        db=db,
        farm_id=farm_id,
        miner_id=miner_id,
        severity=severity,
        alert_type=alert_type,
        is_acknowledged=is_acknowledged,
        page=pagination.page,
        size=pagination.size,
    )
    
    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=AlertService.calculate_pages(total, pagination.size),
    )


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manual alert",
    responses={
        201: {"description": "Alert created successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Farm or miner not found"},
        422: {"description": "Validation error"},
    },
)
async def create_alert(
    alert_data: AlertCreate,
    db: DbSession,
    current_user: OperatorUser,
) -> AlertResponse:
    """
    Create a new manual alert.
    
    **Request Body:**
    - `farm_id` (UUID, required): Target farm ID.
    - `miner_id` (UUID, optional): Target miner ID (for miner-specific alerts).
    - `severity` (str, optional): Alert severity. Default: info.
    - `alert_type` (str, optional): Alert type. Default: custom.
    - `message` (str, required): Human-readable alert message.
    
    **Response 201:** Alert created successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm or miner not found.
    **Response 422:** Request body validation failed.
    """
    # Verify farm exists
    farm = await FarmService.get_farm_by_id(db, alert_data.farm_id)
    if farm is None:
        raise NotFoundException("Farm", str(alert_data.farm_id))
    
    # Verify miner exists if provided
    if alert_data.miner_id:
        miner = await MinerService.get_miner_by_id(
            db, alert_data.miner_id, alert_data.farm_id
        )
        if miner is None:
            raise NotFoundException("Miner", str(alert_data.miner_id))
    
    alert = await AlertService.create_alert(db, alert_data)
    return AlertResponse.model_validate(alert)


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get an alert by ID",
    responses={
        200: {"description": "Alert details"},
        401: {"description": "Not authenticated"},
        404: {"description": "Alert not found"},
    },
)
async def get_alert(
    alert_id: UUID,
    db: DbSession,
    current_user: ViewerUser,
) -> AlertResponse:
    """
    Get details of a specific alert.
    
    **Path Parameters:**
    - `alert_id` (UUID, required): Alert unique identifier.
    
    **Response 200:** Alert details.
    **Response 401:** Not authenticated.
    **Response 404:** Alert not found.
    """
    alert = await AlertService.get_alert_by_id(db, alert_id)
    
    if alert is None:
        raise NotFoundException("Alert", str(alert_id))
    
    return AlertResponse.model_validate(alert)


@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Acknowledge an alert",
    responses={
        200: {"description": "Alert acknowledged successfully"},
        400: {"description": "Alert already acknowledged"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Alert not found"},
    },
)
async def acknowledge_alert(
    alert_id: UUID,
    db: DbSession,
    current_user: OperatorUser,
) -> AlertResponse:
    """
    Mark an alert as acknowledged.
    
    **Path Parameters:**
    - `alert_id` (UUID, required): Alert unique identifier.
    
    The authenticated user is recorded as the acknowledger with timestamp.
    
    **Response 200:** Alert acknowledged successfully.
    **Response 400:** Alert is already acknowledged.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Alert not found.
    """
    alert = await AlertService.get_alert_by_id(db, alert_id)
    
    if alert is None:
        raise NotFoundException("Alert", str(alert_id))
    
    if alert.is_acknowledged:
        raise BadRequestException("Alert is already acknowledged")
    
    alert = await AlertService.acknowledge_alert(db, alert, current_user.id)
    return AlertResponse.model_validate(alert)


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an alert",
    responses={
        204: {"description": "Alert deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions (requires admin role)"},
        404: {"description": "Alert not found"},
    },
)
async def delete_alert(
    alert_id: UUID,
    db: DbSession,
    current_user: AdminUser,
) -> None:
    """
    Delete an alert.
    
    **Path Parameters:**
    - `alert_id` (UUID, required): Alert unique identifier.
    
    **Response 204:** Alert deleted successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have admin role.
    **Response 404:** Alert not found.
    """
    alert = await AlertService.get_alert_by_id(db, alert_id)
    
    if alert is None:
        raise NotFoundException("Alert", str(alert_id))
    
    await AlertService.delete_alert(db, alert)
