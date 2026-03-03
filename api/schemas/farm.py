"""
Mining Farm schemas.

This module defines Pydantic schemas for mining farm CRUD operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.models.farm import FarmStatus


class FarmCreate(BaseModel):
    """
    Schema for creating a new mining farm.
    
    **Request Body:**
    - `name` (str, required): Farm display name. 1-100 characters.
    - `location` (str, optional): Physical location description.
    - `total_power_kw` (float, optional): Total available power in kilowatts. Must be > 0.
    - `status` (str, optional): Initial status. One of: online, offline, maintenance. Default: offline.
    
    **Response 201:** FarmResponse - newly created farm object.
    **Response 400:** Name already exists for this owner.
    **Response 401:** Missing or invalid authentication cookie.
    **Response 403:** User does not have operator or admin role.
    **Response 422:** Request body validation failed.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Farm display name. 1-100 characters.",
        examples=["Main Bitcoin Farm"],
    )
    location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Physical location description.",
        examples=["Warehouse A, Industrial Zone"],
    )
    total_power_kw: Optional[float] = Field(
        default=None,
        gt=0,
        description="Total available power in kilowatts. Must be > 0.",
        examples=[500.0],
    )
    status: Optional[FarmStatus] = Field(
        default=FarmStatus.OFFLINE,
        description="Initial status. One of: online, offline, maintenance.",
    )


class FarmUpdate(BaseModel):
    """
    Schema for full farm update (PUT).
    
    All fields are required for full replacement.
    
    **Request Body:**
    - `name` (str, required): Farm display name. 1-100 characters.
    - `location` (str, optional): Physical location description.
    - `total_power_kw` (float, optional): Total available power in kilowatts.
    - `status` (str, required): Status. One of: online, offline, maintenance.
    
    **Response 200:** FarmResponse - updated farm object.
    **Response 401:** Missing or invalid authentication cookie.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm not found.
    **Response 422:** Request body validation failed.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Farm display name. 1-100 characters.",
    )
    location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Physical location description.",
    )
    total_power_kw: Optional[float] = Field(
        default=None,
        gt=0,
        description="Total available power in kilowatts.",
    )
    status: FarmStatus = Field(
        ...,
        description="Status. One of: online, offline, maintenance.",
    )


class FarmPatch(BaseModel):
    """
    Schema for partial farm update (PATCH).
    
    All fields are optional - only provided fields are updated.
    
    **Request Body:**
    - `name` (str, optional): Farm display name. 1-100 characters.
    - `location` (str, optional): Physical location description.
    - `total_power_kw` (float, optional): Total available power in kilowatts.
    - `status` (str, optional): Status. One of: online, offline, maintenance.
    
    **Response 200:** FarmResponse - updated farm object.
    **Response 401:** Missing or invalid authentication cookie.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm not found.
    **Response 422:** Request body validation failed.
    """
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Farm display name. 1-100 characters.",
    )
    location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Physical location description.",
    )
    total_power_kw: Optional[float] = Field(
        default=None,
        gt=0,
        description="Total available power in kilowatts.",
    )
    status: Optional[FarmStatus] = Field(
        default=None,
        description="Status. One of: online, offline, maintenance.",
    )


class FarmResponse(BaseModel):
    """
    Schema for farm response.
    
    **Fields:**
    - `id` (UUID): Farm unique identifier.
    - `name` (str): Farm display name.
    - `location` (str | null): Physical location.
    - `owner_id` (UUID): Owner user ID.
    - `total_power_kw` (float | null): Total power capacity.
    - `status` (str): Operational status.
    - `created_at` (datetime): Creation timestamp.
    - `updated_at` (datetime): Last update timestamp.
    - `miners_count` (int): Number of miners in the farm.
    """
    id: UUID = Field(..., description="Farm unique identifier.")
    name: str = Field(..., description="Farm display name.")
    location: Optional[str] = Field(None, description="Physical location.")
    owner_id: UUID = Field(..., description="Owner user ID.")
    total_power_kw: Optional[float] = Field(None, description="Total power capacity in kW.")
    status: FarmStatus = Field(..., description="Operational status.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")
    miners_count: int = Field(default=0, description="Number of miners in the farm.")
    
    model_config = ConfigDict(from_attributes=True)


class FarmListResponse(BaseModel):
    """
    Schema for paginated farm list response.
    
    **Fields:**
    - `items` (list): List of farms.
    - `total` (int): Total number of farms.
    - `page` (int): Current page number.
    - `size` (int): Page size.
    - `pages` (int): Total number of pages.
    """
    items: list[FarmResponse] = Field(..., description="List of farms.")
    total: int = Field(..., description="Total number of farms.")
    page: int = Field(..., description="Current page number (1-indexed).")
    size: int = Field(..., description="Page size.")
    pages: int = Field(..., description="Total number of pages.")


class FarmSummary(BaseModel):
    """
    Schema for farm summary/aggregated statistics.
    
    **Fields:**
    - `farm_id` (UUID): Farm identifier.
    - `total_hashrate_th` (float): Total hashrate in TH/s.
    - `active_miners` (int): Number of active miners.
    - `total_miners` (int): Total number of miners.
    - `total_power_watts` (float): Total power consumption in Watts.
    - `avg_temperature_c` (float): Average temperature in Celsius.
    """
    farm_id: UUID = Field(..., description="Farm identifier.")
    total_hashrate_th: float = Field(..., description="Total hashrate in TH/s.")
    active_miners: int = Field(..., description="Number of active miners.")
    total_miners: int = Field(..., description="Total number of miners.")
    total_power_watts: float = Field(..., description="Total power consumption in Watts.")
    avg_temperature_c: float = Field(..., description="Average temperature in Celsius.")
