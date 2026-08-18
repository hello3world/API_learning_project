"""
Miner Metric schemas.

This module defines Pydantic schemas for miner metrics operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MetricCreate(BaseModel):
    """
    Schema for creating a new miner metric snapshot.

    **Request Body:**
    - `hashrate_th` (float, required): Hashrate in Terahash/second. Must be >= 0.
    - `temperature_c` (float, required): Temperature in Celsius.
    - `fan_speed_rpm` (int, optional): Fan speed in RPM.
    - `power_watts` (float, required): Power consumption in Watts. Must be >= 0.
    - `accepted_shares` (int, optional): Number of accepted shares. Default: 0.
    - `rejected_shares` (int, optional): Number of rejected shares. Default: 0.
    - `pool_difficulty` (float, optional): Current pool difficulty.

    **Response 201:** MetricResponse - newly created metric snapshot.
    **Response 401:** Missing or invalid authentication cookie.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Miner not found.
    **Response 422:** Request body validation failed.
    """
    hashrate_th: float = Field(
        ...,
        ge=0,
        description="Hashrate in Terahash/second. Must be >= 0.",
        examples=[110.5],
    )
    temperature_c: float = Field(
        ...,
        description="Temperature in Celsius.",
        examples=[65.0],
    )
    fan_speed_rpm: Optional[int] = Field(
        default=None,
        ge=0,
        description="Fan speed in RPM.",
        examples=[4500],
    )
    power_watts: float = Field(
        ...,
        ge=0,
        description="Power consumption in Watts. Must be >= 0.",
        examples=[3250.0],
    )
    accepted_shares: Optional[int] = Field(
        default=0,
        ge=0,
        description="Number of accepted shares.",
        examples=[1250],
    )
    rejected_shares: Optional[int] = Field(
        default=0,
        ge=0,
        description="Number of rejected shares.",
        examples=[3],
    )
    pool_difficulty: Optional[float] = Field(
        default=None,
        ge=0,
        description="Current pool difficulty.",
        examples=[65536.0],
    )


class MetricResponse(BaseModel):
    """
    Schema for metric response.

    **Fields:**
    - `id` (UUID): Metric unique identifier.
    - `miner_id` (UUID): Parent miner ID.
    - `recorded_at` (datetime): When the metric was recorded.
    - `hashrate_th` (float): Hashrate in TH/s.
    - `temperature_c` (float): Temperature in Celsius.
    - `fan_speed_rpm` (int | null): Fan speed in RPM.
    - `power_watts` (float): Power consumption in Watts.
    - `accepted_shares` (int): Accepted shares count.
    - `rejected_shares` (int): Rejected shares count.
    - `pool_difficulty` (float | null): Pool difficulty.
    """
    id: UUID = Field(..., description="Metric unique identifier.")
    miner_id: UUID = Field(..., description="Parent miner ID.")
    recorded_at: datetime = Field(
        ..., description="When the metric was recorded in ISO 8601 format.")
    hashrate_th: float = Field(...,
                               description="Hashrate in TH/s. Must be >= 0.")
    temperature_c: float = Field(..., description="Temperature in Celsius.")
    fan_speed_rpm: Optional[int] = Field(
        None, description="Fan speed in RPM. Must be >= 0.")
    power_watts: float = Field(...,
                               description="Power consumption in Watts. Must be >= 0.")
    accepted_shares: int = Field(...,
                                 description="Accepted shares count. Must be >= 0.")
    rejected_shares: int = Field(...,
                                 description="Rejected shares count. Must be >= 0.")
    pool_difficulty: Optional[float] = Field(
        None, description="Pool difficulty. Must be >= 0.")

    model_config = ConfigDict(from_attributes=True)


class MetricListResponse(BaseModel):
    """
    Schema for paginated metric list response.

    **Fields:**
    - `items` (list): List of metrics.
    - `total` (int): Total number of metrics.
    - `page` (int): Current page number.
    - `size` (int): Page size.
    - `pages` (int): Total number of pages.
    """
    items: list[MetricResponse] = Field(..., description="List of metrics.")
    total: int = Field(..., description="Total number of metrics.")
    page: int = Field(..., description="Current page number (1-indexed).")
    size: int = Field(..., description="Page size.")
    pages: int = Field(..., description="Total number of pages.")


class MetricLatestResponse(BaseModel):
    """
    Schema for latest metric response with miner info.

    **Fields:**
    - `metric` (MetricResponse | null): Latest metric or null if no metrics.
    - `miner_id` (UUID): Miner ID.
    - `miner_name` (str): Miner display name.
    """
    metric: Optional[MetricResponse] = Field(
        None, description="Latest metric or null.")
    miner_id: UUID = Field(..., description="Miner ID.")
    miner_name: str = Field(..., description="Miner display name.")
