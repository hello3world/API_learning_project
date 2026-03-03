"""
Miners router.

This module defines endpoints for miner CRUD operations within farms.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from api.dependencies import AdminUser, DbSession, OperatorUser, Pagination, ViewerUser
from api.exceptions import ConflictException, NotFoundException
from api.models.miner import MinerStatus
from api.schemas.miner import (
    MinerCreate,
    MinerListResponse,
    MinerPatch,
    MinerResponse,
    MinerUpdate,
)
from api.services.farm_service import FarmService
from api.services.miner_service import MinerService


router = APIRouter(tags=["Miners"])


@router.get(
    "/farms/{farm_id}/miners",
    response_model=MinerListResponse,
    summary="List miners in a farm",
    responses={
        200: {"description": "List of miners"},
        401: {"description": "Not authenticated"},
        404: {"description": "Farm not found"},
    },
)
async def list_miners(
    farm_id: UUID,
    db: DbSession,
    current_user: ViewerUser,
    pagination: Pagination,
    status_filter: Optional[MinerStatus] = Query(
        None,
        alias="status",
        description="Filter by miner status",
    ),
) -> MinerListResponse:
    """
    Get a paginated list of miners in a farm.
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Parent farm ID.
    
    **Query Parameters:**
    - `page` (int, optional): Page number (1-indexed). Default: 1.
    - `size` (int, optional): Page size (1-100). Default: 10.
    - `status` (str, optional): Filter by status (active, inactive, error, maintenance).
    
    **Response 200:** Paginated list of miners.
    **Response 401:** Not authenticated.
    **Response 404:** Farm not found.
    """
    # Verify farm exists
    farm = await FarmService.get_farm_by_id(db, farm_id)
    if farm is None:
        raise NotFoundException("Farm", str(farm_id))
    
    miners, total = await MinerService.get_miners(
        db=db,
        farm_id=farm_id,
        status=status_filter,
        page=pagination.page,
        size=pagination.size,
    )
    
    return MinerListResponse(
        items=[MinerResponse.model_validate(m) for m in miners],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=MinerService.calculate_pages(total, pagination.size),
    )


@router.post(
    "/farms/{farm_id}/miners",
    response_model=MinerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a miner to a farm",
    responses={
        201: {"description": "Miner created successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Farm not found"},
        409: {"description": "IP address already exists in this farm"},
        422: {"description": "Validation error"},
    },
)
async def create_miner(
    farm_id: UUID,
    miner_data: MinerCreate,
    db: DbSession,
    current_user: OperatorUser,
) -> MinerResponse:
    """
    Add a new miner to a farm.
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Parent farm ID.
    
    **Request Body:**
    - `name` (str, required): Miner display name. 1-100 characters.
    - `model` (str, required): Hardware model (e.g., "Antminer S19 Pro").
    - `ip_address` (str, optional): Network IP address.
    - `mac_address` (str, optional): Network MAC address (XX:XX:XX:XX:XX:XX).
    - `status` (str, optional): Initial status. Default: inactive.
    - `worker_name` (str, optional): Pool worker identifier.
    
    **Response 201:** Miner created successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm not found.
    **Response 409:** IP address already exists in this farm.
    **Response 422:** Request body validation failed.
    """
    # Verify farm exists
    farm = await FarmService.get_farm_by_id(db, farm_id)
    if farm is None:
        raise NotFoundException("Farm", str(farm_id))
    
    # Check for duplicate IP
    if miner_data.ip_address:
        if await MinerService.check_ip_exists(db, farm_id, miner_data.ip_address):
            raise ConflictException(
                f"IP address '{miner_data.ip_address}' already exists in this farm"
            )
    
    miner = await MinerService.create_miner(db, farm_id, miner_data)
    return MinerResponse.model_validate(miner)


@router.get(
    "/farms/{farm_id}/miners/{miner_id}",
    response_model=MinerResponse,
    summary="Get a miner by ID",
    responses={
        200: {"description": "Miner details"},
        401: {"description": "Not authenticated"},
        404: {"description": "Farm or miner not found"},
    },
)
async def get_miner(
    farm_id: UUID,
    miner_id: UUID,
    db: DbSession,
    current_user: ViewerUser,
) -> MinerResponse:
    """
    Get details of a specific miner.
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Parent farm ID.
    - `miner_id` (UUID, required): Miner unique identifier.
    
    **Response 200:** Miner details.
    **Response 401:** Not authenticated.
    **Response 404:** Farm or miner not found.
    """
    miner = await MinerService.get_miner_by_id(db, miner_id, farm_id)
    
    if miner is None:
        raise NotFoundException("Miner", str(miner_id))
    
    return MinerResponse.model_validate(miner)


@router.get(
    "/miners/{miner_id}",
    response_model=MinerResponse,
    summary="Get a miner by ID (direct access)",
    responses={
        200: {"description": "Miner details"},
        401: {"description": "Not authenticated"},
        404: {"description": "Miner not found"},
    },
)
async def get_miner_direct(
    miner_id: UUID,
    db: DbSession,
    current_user: ViewerUser,
) -> MinerResponse:
    """
    Get details of a specific miner by ID (without farm_id).
    
    **Path Parameters:**
    - `miner_id` (UUID, required): Miner unique identifier.
    
    **Response 200:** Miner details.
    **Response 401:** Not authenticated.
    **Response 404:** Miner not found.
    """
    miner = await MinerService.get_miner_by_id(db, miner_id)
    
    if miner is None:
        raise NotFoundException("Miner", str(miner_id))
    
    return MinerResponse.model_validate(miner)


@router.put(
    "/farms/{farm_id}/miners/{miner_id}",
    response_model=MinerResponse,
    summary="Full update of a miner",
    responses={
        200: {"description": "Miner updated successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Farm or miner not found"},
        409: {"description": "IP address already exists"},
        422: {"description": "Validation error"},
    },
)
async def update_miner(
    farm_id: UUID,
    miner_id: UUID,
    miner_data: MinerUpdate,
    db: DbSession,
    current_user: OperatorUser,
) -> MinerResponse:
    """
    Full update of a miner (all fields required).
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Parent farm ID.
    - `miner_id` (UUID, required): Miner unique identifier.
    
    **Request Body:**
    - `name` (str, required): Miner display name.
    - `model` (str, required): Hardware model.
    - `ip_address` (str, optional): Network IP address.
    - `mac_address` (str, optional): Network MAC address.
    - `status` (str, required): Status.
    - `worker_name` (str, optional): Pool worker identifier.
    
    **Response 200:** Miner updated successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm or miner not found.
    **Response 409:** IP address already exists.
    **Response 422:** Request body validation failed.
    """
    miner = await MinerService.get_miner_by_id(db, miner_id, farm_id)
    
    if miner is None:
        raise NotFoundException("Miner", str(miner_id))
    
    # Check for duplicate IP (exclude current miner)
    if miner_data.ip_address and miner_data.ip_address != miner.ip_address:
        if await MinerService.check_ip_exists(
            db, farm_id, miner_data.ip_address, exclude_miner_id=miner_id
        ):
            raise ConflictException(
                f"IP address '{miner_data.ip_address}' already exists in this farm"
            )
    
    miner = await MinerService.update_miner(db, miner, miner_data)
    return MinerResponse.model_validate(miner)


@router.patch(
    "/farms/{farm_id}/miners/{miner_id}",
    response_model=MinerResponse,
    summary="Partial update of a miner",
    responses={
        200: {"description": "Miner updated successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Farm or miner not found"},
        422: {"description": "Validation error"},
    },
)
async def patch_miner(
    farm_id: UUID,
    miner_id: UUID,
    miner_data: MinerPatch,
    db: DbSession,
    current_user: OperatorUser,
) -> MinerResponse:
    """
    Partial update of a miner (only provided fields are updated).
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Parent farm ID.
    - `miner_id` (UUID, required): Miner unique identifier.
    
    **Request Body (all optional):**
    - `name` (str): Miner display name.
    - `model` (str): Hardware model.
    - `ip_address` (str): Network IP address.
    - `mac_address` (str): Network MAC address.
    - `status` (str): Status.
    - `worker_name` (str): Pool worker identifier.
    
    **Response 200:** Miner updated successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm or miner not found.
    **Response 422:** Request body validation failed.
    """
    miner = await MinerService.get_miner_by_id(db, miner_id, farm_id)
    
    if miner is None:
        raise NotFoundException("Miner", str(miner_id))
    
    miner = await MinerService.patch_miner(db, miner, miner_data)
    return MinerResponse.model_validate(miner)


@router.delete(
    "/farms/{farm_id}/miners/{miner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a miner",
    responses={
        204: {"description": "Miner deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions (requires admin role)"},
        404: {"description": "Farm or miner not found"},
    },
)
async def delete_miner(
    farm_id: UUID,
    miner_id: UUID,
    db: DbSession,
    current_user: AdminUser,
) -> None:
    """
    Delete a miner and all related data (metrics, alerts).
    
    **Path Parameters:**
    - `farm_id` (UUID, required): Parent farm ID.
    - `miner_id` (UUID, required): Miner unique identifier.
    
    **Response 204:** Miner deleted successfully.
    **Response 401:** Not authenticated.
    **Response 403:** User does not have admin role.
    **Response 404:** Farm or miner not found.
    """
    miner = await MinerService.get_miner_by_id(db, miner_id, farm_id)
    
    if miner is None:
        raise NotFoundException("Miner", str(miner_id))
    
    await MinerService.delete_miner(db, miner)
