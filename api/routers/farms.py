"""
Mining farms router.

This module defines endpoints for mining farm CRUD operations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from api.dependencies import AdminUser, DbSession, OperatorUser, Pagination, ViewerUser
from api.exceptions import NotFoundException
from api.models.farm import FarmStatus
from api.schemas.farm import (
    FarmCreate,
    FarmListResponse,
    FarmPatch,
    FarmResponse,
    FarmSummary,
    FarmUpdate,
)
from api.services.farm_service import FarmService


router = APIRouter(prefix="/farms", tags=["Mining Farms"])


@router.get(
    "",
    response_model=FarmListResponse,
    summary="List all mining farms",
    responses={
        200: {"description": "List of mining farms"},
        401: {"description": "Not authenticated"},
    },
)
async def list_farms(
    db: DbSession,
    current_user: ViewerUser,
    pagination: Pagination,
    status_filter: Optional[FarmStatus] = Query(
        None,
        alias="status",
        description="Filter by farm status",
    ),
) -> FarmListResponse:
    """
    Get a paginated list of all mining farms.
    
    **Query Parameters:**
    - `page` (int, optional): Page number (1-indexed). Default: 1.
    - `size` (int, optional): Page size (1-100). Default: 10.
    - `status` (str, optional): Filter by status (online, offline, maintenance).
    
    **Response 200:** Paginated list of farms.
    **Response 401:** Not authenticated.
    """
    farms, total = await FarmService.get_farms(
        db=db,
        status=status_filter,
        page=pagination.page,
        size=pagination.size,
    )
    
    # Add miners_count to each farm
    items = []
    for farm in farms:
        farm_dict = FarmResponse.model_validate(farm).model_dump()
        farm_dict["miners_count"] = len(farm.miners) if farm.miners else 0
        items.append(FarmResponse.model_validate(farm_dict))
    
    return FarmListResponse(
        items=items,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=FarmService.calculate_pages(total, pagination.size),
    )


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new mining farm",
    responses={
        201: {"description": "Farm created successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions (requires operator role)"},
        422: {"description": "Validation error"},
    },
)
async def create_farm(
    farm_data: FarmCreate,
    db: DbSession,
    current_user: OperatorUser,
) -> FarmResponse:
    """
    Create a new mining farm.
    
    **Request Body:**
    - `name` (str, required): Farm display name. 1-100 characters.
    - `location` (str, optional): Physical location description.
    - `total_power_kw` (float, optional): Total available power in kilowatts. Must be > 0.
    - `status` (str, optional): Initial status. One of: online, offline, maintenance. Default: offline.
    
    **Response 201:** Farm created successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have operator or admin role.
    **Response 422:** Request body validation failed.
    """
    farm = await FarmService.create_farm(
        db=db,
        farm_data=farm_data,
        owner_id=current_user.id,
    )
    
    response = FarmResponse.model_validate(farm)
    response.miners_count = 0
    return response


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Get a mining farm by ID",
    responses={
        200: {"description": "Farm details"},
        401: {"description": "Not authenticated"},
        404: {"description": "Farm not found"},
    },
)
async def get_farm(
    farm_id: UUID,
    db: DbSession,
    current_user: ViewerUser,
) -> FarmResponse:
    """
    Get details of a specific mining farm.
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Farm unique identifier.
    
    **Response 200:** Farm details.
    **Response 401:** Not authenticated.
    **Response 404:** Farm not found.
    """
    farm = await FarmService.get_farm_by_id(db, farm_id)
    
    if farm is None:
        raise NotFoundException("Farm", str(farm_id))
    
    response = FarmResponse.model_validate(farm)
    response.miners_count = len(farm.miners) if farm.miners else 0
    return response


@router.put(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Full update of a mining farm",
    responses={
        200: {"description": "Farm updated successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Farm not found"},
        422: {"description": "Validation error"},
    },
)
async def update_farm(
    farm_id: UUID,
    farm_data: FarmUpdate,
    db: DbSession,
    current_user: OperatorUser,
) -> FarmResponse:
    """
    Full update of a mining farm (all fields required).
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Farm unique identifier.
    
    **Request Body:**
    - `name` (str, required): Farm display name. 1-100 characters.
    - `location` (str, optional): Physical location description.
    - `total_power_kw` (float, optional): Total available power in kilowatts.
    - `status` (str, required): Status. One of: online, offline, maintenance.
    
    **Response 200:** Farm updated successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm not found.
    **Response 422:** Request body validation failed.
    """
    farm = await FarmService.get_farm_by_id(db, farm_id)
    
    if farm is None:
        raise NotFoundException("Farm", str(farm_id))
    
    farm = await FarmService.update_farm(db, farm, farm_data)
    
    response = FarmResponse.model_validate(farm)
    response.miners_count = len(farm.miners) if farm.miners else 0
    return response


@router.patch(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Partial update of a mining farm",
    responses={
        200: {"description": "Farm updated successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Farm not found"},
        422: {"description": "Validation error"},
    },
)
async def patch_farm(
    farm_id: UUID,
    farm_data: FarmPatch,
    db: DbSession,
    current_user: OperatorUser,
) -> FarmResponse:
    """
    Partial update of a mining farm (only provided fields are updated).
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Farm unique identifier.
    
    **Request Body (all optional):**
    - `name` (str): Farm display name. 1-100 characters.
    - `location` (str): Physical location description.
    - `total_power_kw` (float): Total available power in kilowatts.
    - `status` (str): Status. One of: online, offline, maintenance.
    
    **Response 200:** Farm updated successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm not found.
    **Response 422:** Request body validation failed.
    """
    farm = await FarmService.get_farm_by_id(db, farm_id)
    
    if farm is None:
        raise NotFoundException("Farm", str(farm_id))
    
    farm = await FarmService.patch_farm(db, farm, farm_data)
    
    response = FarmResponse.model_validate(farm)
    response.miners_count = len(farm.miners) if farm.miners else 0
    return response


@router.delete(
    "/{farm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a mining farm",
    responses={
        204: {"description": "Farm deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions (requires admin role)"},
        404: {"description": "Farm not found"},
    },
)
async def delete_farm(
    farm_id: UUID,
    db: DbSession,
    current_user: AdminUser,
) -> None:
    """
    Delete a mining farm and all related data (miners, metrics, alerts).
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Farm unique identifier.
    
    **Response 204:** Farm deleted successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have admin role.
    **Response 404:** Farm not found.
    """
    farm = await FarmService.get_farm_by_id(db, farm_id)
    
    if farm is None:
        raise NotFoundException("Farm", str(farm_id))
    
    await FarmService.delete_farm(db, farm)


@router.get(
    "/{farm_id}/summary",
    response_model=FarmSummary,
    summary="Get farm aggregated statistics",
    responses={
        200: {"description": "Farm summary statistics"},
        401: {"description": "Not authenticated"},
        404: {"description": "Farm not found"},
    },
)
async def get_farm_summary(
    farm_id: UUID,
    db: DbSession,
    current_user: ViewerUser,
) -> FarmSummary:
    """
    Get aggregated statistics for a mining farm.
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Farm unique identifier.
    
    **Response 200:** Farm summary with:
    - `total_hashrate_th`: Total hashrate in TH/s.
    - `active_miners`: Number of active miners.
    - `total_miners`: Total number of miners.
    - `total_power_watts`: Total power consumption in Watts.
    - `avg_temperature_c`: Average temperature in Celsius.
    
    **Response 401:** Not authenticated.
    **Response 404:** Farm not found.
    """
    summary = await FarmService.get_farm_summary(db, farm_id)
    
    if summary is None:
        raise NotFoundException("Farm", str(farm_id))
    
    return summary
