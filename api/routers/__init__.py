"""
API Routers.

This package contains all API endpoint routers.
"""

from api.routers.auth import router as auth_router
from api.routers.farms import router as farms_router
from api.routers.miners import router as miners_router
from api.routers.metrics import router as metrics_router
from api.routers.alerts import router as alerts_router
from api.routers.websocket import router as websocket_router

__all__ = [
    "auth_router",
    "farms_router",
    "miners_router",
    "metrics_router",
    "alerts_router",
    "websocket_router",
]
