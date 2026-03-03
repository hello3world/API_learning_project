"""
Miner schemas.

This module defines Pydantic schemas for miner CRUD operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.models.miner import MinerStatus


class MinerCreate(BaseModel):
    """
    Schema for creating a new miner.
    
    **Request Body:**
    - `name` (str, required): Miner display name. 1-100 characters.
    - `model` (str, required): Hardware model (e.g., "Antminer S19 Pro"). 1-100 characters.
    - `ip_address` (str, optional): Network IP address (IPv4 or IPv6).
    - `mac_address` (str, optional): Network MAC address (XX:XX:XX:XX:XX:XX format).
    - `status` (str, optional): Initial status. One of: active, inactive, error, maintenance. Default: inactive.
    - `worker_name` (str, optional): Pool worker identifier.
    
    **Response 201:** MinerResponse - newly created miner object.
    **Response 401:** Missing or invalid authentication cookie.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm not found.
    **Response 409:** IP address already exists in this farm.
    **Response 422:** Request body validation failed.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Miner display name. 1-100 characters.",
        examples=["Miner-001"],
    )
    model: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Hardware model name.",
        examples=["Antminer S19 Pro"],
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="Network IP address (IPv4 or IPv6).",
        examples=["192.168.1.100"],
    )
    mac_address: Optional[str] = Field(
        default=None,
        max_length=17,
        pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$",
        description="Network MAC address (XX:XX:XX:XX:XX:XX format).",
        examples=["AA:BB:CC:DD:EE:FF"],
    )
    status: Optional[MinerStatus] = Field(
        default=MinerStatus.INACTIVE,
        description="Initial status. One of: active, inactive, error, maintenance.",
    )
    worker_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Pool worker identifier.",
        examples=["farm1.worker001"],
    )


class MinerUpdate(BaseModel):
    """
    Schema for full miner update (PUT).
    
    All fields are required for full replacement.
    
    **Request Body:**
    - `name` (str, required): Miner display name. 1-100 characters.
    - `model` (str, required): Hardware model. 1-100 characters.
    - `ip_address` (str, optional): Network IP address.
    - `mac_address` (str, optional): Network MAC address.
    - `status` (str, required): Status. One of: active, inactive, error, maintenance.
    - `worker_name` (str, optional): Pool worker identifier.
    
    **Response 200:** MinerResponse - updated miner object.
    **Response 401:** Missing or invalid authentication cookie.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Miner or farm not found.
    **Response 409:** IP address already exists.
    **Response 422:** Request body validation failed.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Miner display name.",
    )
    model: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Hardware model name.",
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="Network IP address.",
    )
    mac_address: Optional[str] = Field(
        default=None,
        max_length=17,
        pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$",
        description="Network MAC address.",
    )
    status: MinerStatus = Field(
        ...,
        description="Status. One of: active, inactive, error, maintenance.",
    )
    worker_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Pool worker identifier.",
    )


class MinerPatch(BaseModel):
    """
    Schema for partial miner update (PATCH).
    
    All fields are optional - only provided fields are updated.
    
    **Request Body:**
    - `name` (str, optional): Miner display name. 1-100 characters.
    - `model` (str, optional): Hardware model.
    - `ip_address` (str, optional): Network IP address.
    - `mac_address` (str, optional): Network MAC address.
    - `status` (str, optional): Status. One of: active, inactive, error, maintenance.
    - `worker_name` (str, optional): Pool worker identifier.
    
    **Response 200:** MinerResponse - updated miner object.
    **Response 401:** Missing or invalid authentication cookie.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Miner or farm not found.
    **Response 422:** Request body validation failed.
    """
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Miner display name.",
    )
    model: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Hardware model name.",
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="Network IP address.",
    )
    mac_address: Optional[str] = Field(
        default=None,
        max_length=17,
        pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$",
        description="Network MAC address.",
    )
    status: Optional[MinerStatus] = Field(
        default=None,
        description="Status.",
    )
    worker_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Pool worker identifier.",
    )


class MinerResponse(BaseModel):
    """
    Schema for miner response.
    
    **Fields:**
    - `id` (UUID): Miner unique identifier.
    - `farm_id` (UUID): Parent farm ID.
    - `name` (str): Miner display name.
    - `model` (str): Hardware model.
    - `ip_address` (str | null): Network IP address.
    - `mac_address` (str | null): Network MAC address.
    - `status` (str): Operational status.
    - `worker_name` (str | null): Pool worker ID.
    - `created_at` (datetime): Registration timestamp.
    - `updated_at` (datetime): Last update timestamp.
    """
    id: UUID = Field(..., description="Miner unique identifier.")
    farm_id: UUID = Field(..., description="Parent farm ID.")
    name: str = Field(..., description="Miner display name.")
    model: str = Field(..., description="Hardware model.")
    ip_address: Optional[str] = Field(None, description="Network IP address.")
    mac_address: Optional[str] = Field(None, description="Network MAC address.")
    status: MinerStatus = Field(..., description="Operational status.")
    worker_name: Optional[str] = Field(None, description="Pool worker identifier.")
    created_at: datetime = Field(..., description="Registration timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")
    
    model_config = ConfigDict(from_attributes=True)


class MinerListResponse(BaseModel):
    """
    Schema for paginated miner list response.
    
    **Fields:**
    - `items` (list): List of miners.
    - `total` (int): Total number of miners.
    - `page` (int): Current page number.
    - `size` (int): Page size.
    - `pages` (int): Total number of pages.
    """
    items: list[MinerResponse] = Field(..., description="List of miners.")
    total: int = Field(..., description="Total number of miners.")
    page: int = Field(..., description="Current page number (1-indexed).")
    size: int = Field(..., description="Page size.")
    pages: int = Field(..., description="Total number of pages.")
