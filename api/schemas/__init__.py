"""
Pydantic schemas for request/response validation.

This package contains all Pydantic schemas for API data validation.
"""

from api.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    TokenData,
)
from api.schemas.farm import (
    FarmCreate,
    FarmUpdate,
    FarmPatch,
    FarmResponse,
    FarmListResponse,
    FarmSummary,
)
from api.schemas.miner import (
    MinerCreate,
    MinerUpdate,
    MinerPatch,
    MinerResponse,
    MinerListResponse,
)
from api.schemas.metric import (
    MetricCreate,
    MetricResponse,
    MetricListResponse,
)
from api.schemas.alert import (
    AlertCreate,
    AlertResponse,
    AlertListResponse,
    AlertAcknowledge,
)

__all__ = [
    # Auth
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "TokenData",
    # Farm
    "FarmCreate",
    "FarmUpdate",
    "FarmPatch",
    "FarmResponse",
    "FarmListResponse",
    "FarmSummary",
    # Miner
    "MinerCreate",
    "MinerUpdate",
    "MinerPatch",
    "MinerResponse",
    "MinerListResponse",
    # Metric
    "MetricCreate",
    "MetricResponse",
    "MetricListResponse",
    # Alert
    "AlertCreate",
    "AlertResponse",
    "AlertListResponse",
    "AlertAcknowledge",
]
