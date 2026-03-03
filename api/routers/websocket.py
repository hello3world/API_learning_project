"""
WebSocket router.

This module defines WebSocket endpoints for real-time updates.
"""

import asyncio
import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from api.config import settings
from api.database import async_session_maker
from api.services.auth_service import AuthService
from api.services.farm_service import FarmService
from api.services.miner_service import MinerService
from api.services.metric_service import MetricService


router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Manages WebSocket connections for broadcasting updates.
    
    Maintains separate connection pools for:
    - Miner status updates (per miner)
    - Farm alerts (per farm)
    """
    
    def __init__(self):
        # miner_id -> list of websockets
        self.miner_connections: dict[UUID, list[WebSocket]] = {}
        # farm_id -> list of websockets
        self.farm_connections: dict[UUID, list[WebSocket]] = {}
    
    async def connect_miner(self, websocket: WebSocket, miner_id: UUID):
        """Connect a websocket to miner status updates."""
        await websocket.accept()
        if miner_id not in self.miner_connections:
            self.miner_connections[miner_id] = []
        self.miner_connections[miner_id].append(websocket)
    
    async def connect_farm(self, websocket: WebSocket, farm_id: UUID):
        """Connect a websocket to farm alert updates."""
        await websocket.accept()
        if farm_id not in self.farm_connections:
            self.farm_connections[farm_id] = []
        self.farm_connections[farm_id].append(websocket)
    
    def disconnect_miner(self, websocket: WebSocket, miner_id: UUID):
        """Disconnect a websocket from miner status updates."""
        if miner_id in self.miner_connections:
            if websocket in self.miner_connections[miner_id]:
                self.miner_connections[miner_id].remove(websocket)
            if not self.miner_connections[miner_id]:
                del self.miner_connections[miner_id]
    
    def disconnect_farm(self, websocket: WebSocket, farm_id: UUID):
        """Disconnect a websocket from farm alert updates."""
        if farm_id in self.farm_connections:
            if websocket in self.farm_connections[farm_id]:
                self.farm_connections[farm_id].remove(websocket)
            if not self.farm_connections[farm_id]:
                del self.farm_connections[farm_id]
    
    async def broadcast_to_miner(self, miner_id: UUID, message: dict):
        """Broadcast a message to all connections for a miner."""
        if miner_id in self.miner_connections:
            disconnected = []
            for websocket in self.miner_connections[miner_id]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.append(websocket)
            
            for ws in disconnected:
                self.disconnect_miner(ws, miner_id)
    
    async def broadcast_to_farm(self, farm_id: UUID, message: dict):
        """Broadcast a message to all connections for a farm."""
        if farm_id in self.farm_connections:
            disconnected = []
            for websocket in self.farm_connections[farm_id]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.append(websocket)
            
            for ws in disconnected:
                self.disconnect_farm(ws, farm_id)


# Global connection manager instance
manager = ConnectionManager()


async def verify_token(token: Optional[str]) -> bool:
    """Verify JWT token for WebSocket authentication."""
    if token is None:
        return False
    
    token_data = AuthService.decode_token(token)
    if token_data is None:
        return False
    
    # Verify user exists and is active
    async with async_session_maker() as db:
        user = await AuthService.get_user_by_id(db, token_data.user_id)
        return user is not None and user.is_active


@router.websocket("/ws/miners/{miner_id}/status")
async def miner_status_websocket(
    websocket: WebSocket,
    miner_id: UUID,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
):
    """
    WebSocket endpoint for real-time miner status updates.
    
    **Connection URL:**
    `ws://localhost:8000/ws/miners/{miner_id}/status?token={jwt_token}`
    
    **Authentication:**
    JWT token must be provided as query parameter since browsers cannot
    set cookies on WebSocket handshake.
    
    **Server Messages:**
    ```json
    {
        "type": "metric_update",
        "miner_id": "uuid",
        "data": {
            "hashrate_th": 110.5,
            "temperature_c": 65.0,
            "power_watts": 3250.0,
            "status": "active"
        }
    }
    ```
    
    **Client Messages:**
    ```json
    {"type": "ping"}
    ```
    Server responds with: `{"type": "pong"}`
    
    **Close Codes:**
    - 1008: Authentication failed (invalid or missing token)
    - 1000: Normal closure
    """
    # Verify authentication
    if not await verify_token(token):
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    # Verify miner exists
    async with async_session_maker() as db:
        miner = await MinerService.get_miner_by_id(db, miner_id)
        if miner is None:
            await websocket.close(code=1008, reason="Miner not found")
            return
    
    await manager.connect_miner(websocket, miner_id)
    
    try:
        # Send initial status
        async with async_session_maker() as db:
            latest_metric = await MetricService.get_latest_metric(db, miner_id)
            miner = await MinerService.get_miner_by_id(db, miner_id)
            
            initial_data = {
                "type": "metric_update",
                "miner_id": str(miner_id),
                "data": {
                    "status": miner.status.value if miner else "unknown",
                    "hashrate_th": latest_metric.hashrate_th if latest_metric else 0,
                    "temperature_c": latest_metric.temperature_c if latest_metric else 0,
                    "power_watts": latest_metric.power_watts if latest_metric else 0,
                }
            }
            await websocket.send_json(initial_data)
        
        # Listen for client messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect_miner(websocket, miner_id)


@router.websocket("/ws/farms/{farm_id}/alerts")
async def farm_alerts_websocket(
    websocket: WebSocket,
    farm_id: UUID,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
):
    """
    WebSocket endpoint for real-time farm alert notifications.
    
    **Connection URL:**
    `ws://localhost:8000/ws/farms/{farm_id}/alerts?token={jwt_token}`
    
    **Authentication:**
    JWT token must be provided as query parameter.
    
    **Server Messages:**
    ```json
    {
        "type": "new_alert",
        "alert_id": "uuid",
        "severity": "critical",
        "alert_type": "high_temp",
        "message": "Miner temperature exceeded 80C",
        "miner_id": "uuid or null"
    }
    ```
    
    **Client Messages:**
    ```json
    {"type": "ping"}
    ```
    Server responds with: `{"type": "pong"}`
    
    **Close Codes:**
    - 1008: Authentication failed (invalid or missing token)
    - 1000: Normal closure
    """
    # Verify authentication
    if not await verify_token(token):
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    # Verify farm exists
    async with async_session_maker() as db:
        farm = await FarmService.get_farm_by_id(db, farm_id)
        if farm is None:
            await websocket.close(code=1008, reason="Farm not found")
            return
    
    await manager.connect_farm(websocket, farm_id)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "farm_id": str(farm_id),
            "message": "Subscribed to alert notifications"
        })
        
        # Listen for client messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect_farm(websocket, farm_id)


# Helper functions to broadcast updates (called from other routers)
async def broadcast_metric_update(
    miner_id: UUID,
    hashrate_th: float,
    temperature_c: float,
    power_watts: float,
    status: str,
):
    """Broadcast a metric update to all connected clients for a miner."""
    message = {
        "type": "metric_update",
        "miner_id": str(miner_id),
        "data": {
            "hashrate_th": hashrate_th,
            "temperature_c": temperature_c,
            "power_watts": power_watts,
            "status": status,
        }
    }
    await manager.broadcast_to_miner(miner_id, message)


async def broadcast_new_alert(
    farm_id: UUID,
    alert_id: UUID,
    severity: str,
    alert_type: str,
    message: str,
    miner_id: Optional[UUID] = None,
):
    """Broadcast a new alert to all connected clients for a farm."""
    alert_message = {
        "type": "new_alert",
        "alert_id": str(alert_id),
        "severity": severity,
        "alert_type": alert_type,
        "message": message,
        "miner_id": str(miner_id) if miner_id else None,
    }
    await manager.broadcast_to_farm(farm_id, alert_message)
