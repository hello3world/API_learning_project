"""
Alert schemas.

This module defines Pydantic schemas for alert operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.models.alert import AlertSeverity, AlertType


class AlertCreate(BaseModel):
    """
    Schema for creating a new alert.

    **Request Body:**
    - `farm_id` (UUID, required): Target farm ID.
    - `miner_id` (UUID, optional): Target miner ID (for miner-specific alerts).
    - `severity` (str, optional): Alert severity. One of: info, warning, critical. Default: info.
    - `alert_type` (str, optional): Alert type. One of: high_temp, low_hashrate, offline, power_spike, custom. Default: custom.
    - `message` (str, required): Human-readable alert message.

    **Response 201:** AlertResponse - newly created alert.
    **Response 401:** Missing or invalid authentication cookie.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Farm or miner not found.
    **Response 422:** Request body validation failed.
    """
    farm_id: UUID = Field(
        ...,
        description="Target farm ID.",
    )
    miner_id: Optional[UUID] = Field(
        default=None,
        description="Target miner ID (for miner-specific alerts).",
    )
    severity: Optional[AlertSeverity] = Field(
        default=AlertSeverity.INFO,
        description="Alert severity. One of: info, warning, critical.",
    )
    alert_type: Optional[AlertType] = Field(
        default=AlertType.CUSTOM,
        description="Alert type. One of: high_temp, low_hashrate, offline, power_spike, custom.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Human-readable alert message.",
        examples=["Miner temperature exceeded 80°C threshold"],
    )


class AlertAcknowledge(BaseModel):
    """
    Schema for acknowledging an alert.

    **Request Body:**
    This endpoint does not require a request body. The authenticated user is
    recorded as the acknowledger.

    **Response 200:** AlertResponse - acknowledged alert.
    **Response 400:** Alert already acknowledged.
    **Response 401:** Missing or invalid authentication cookie.
    **Response 403:** User does not have operator or admin role.
    **Response 404:** Alert not found.
    """
    pass  # No fields needed - user comes from auth


class AlertResponse(BaseModel):
    """
    Schema for alert response.

    **Fields:**
    - `id` (UUID): Alert unique identifier.
    - `miner_id` (UUID | null): Target miner ID.
    - `farm_id` (UUID): Target farm ID.
    - `severity` (str): Alert severity.
    - `alert_type` (str): Alert type.
    - `message` (str): Alert message.
    - `is_acknowledged` (bool): Whether alert is acknowledged.
    - `acknowledged_by` (UUID | null): User who acknowledged.
    - `acknowledged_at` (datetime | null): When acknowledged.
    - `created_at` (datetime): Creation timestamp.
    """
    id: UUID = Field(..., description="Alert unique identifier.")
    miner_id: Optional[UUID] = Field(None, description="Target miner ID.")
    farm_id: UUID = Field(..., description="Target farm ID.")
    severity: AlertSeverity = Field(
        ..., description="Alert severity. Possible values: info, warning, critical.")
    alert_type: AlertType = Field(
        ..., description="Alert type. Possible values: high_temp, low_hashrate, offline, power_spike, custom.")
    message: str = Field(..., description="Alert message.")
    is_acknowledged: bool = Field(...,
                                  description="Whether alert is acknowledged. True or False.")
    acknowledged_by: Optional[UUID] = Field(
        None, description="User who acknowledged.")
    acknowledged_at: Optional[datetime] = Field(
        None, description="When acknowledged in ISO 8601 format.")
    created_at: datetime = Field(...,
                                 description="Creation timestamp in ISO 8601 format.")

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    """
    Schema for paginated alert list response.

    **Fields:**
    - `items` (list): List of alerts.
    - `total` (int): Total number of alerts.
    - `page` (int): Current page number.
    - `size` (int): Page size.
    - `pages` (int): Total number of pages.
    """
    items: list[AlertResponse] = Field(..., description="List of alerts.")
    total: int = Field(..., description="Total number of alerts.")
    page: int = Field(..., description="Current page number (1-indexed).")
    size: int = Field(..., description="Page size.")
    pages: int = Field(..., description="Total number of pages.")
