"""
WebSocket endpoint tests.

This module demonstrates httpx-ws testing patterns for WebSocket connections.

Key httpx learning points:
1. WebSocket connection with httpx-ws
2. Token authentication via query parameter
3. Sending and receiving JSON messages
4. Testing connection lifecycle

Note: These tests require the httpx-ws package.
Install with: pip install httpx-ws
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from api.main import app
from api.database import engine, Base, async_session_maker
from api.models.user import UserRole
from api.services.auth_service import AuthService


pytestmark = pytest.mark.asyncio


async def create_test_user_and_get_token(
    username: str,
    role: UserRole,
) -> str:
    """Helper to create user and get JWT token."""
    from api.schemas.auth import UserCreate
    
    async with async_session_maker() as db:
        user_data = UserCreate(
            username=username,
            email=f"{username}@test.com",
            password="testpassword123",
            role=role,
        )
        user = await AuthService.create_user(db, user_data)
        await db.commit()
        
        return AuthService.create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
        )


class TestMinerStatusWebSocket:
    """
    Tests for WS /ws/miners/{miner_id}/status
    
    These tests demonstrate WebSocket patterns with httpx-ws.
    """
    
    async def test_websocket_connection_info(self):
        """
        Information about WebSocket testing with httpx-ws.
        
        To test WebSocket endpoints with httpx, you need:
        
        1. Install httpx-ws:
           pip install httpx-ws
        
        2. Use the aconnect_ws context manager:
           ```python
           from httpx_ws import aconnect_ws
           
           async with aconnect_ws(
               f"ws://localhost:8000/ws/miners/{miner_id}/status",
               params={"token": jwt_token}
           ) as ws:
               # Receive message
               message = await ws.receive_json()
               
               # Send message
               await ws.send_json({"type": "ping"})
               
               # Receive pong
               pong = await ws.receive_json()
           ```
        
        3. Test authentication:
           - With valid token: connection accepted
           - Without token: close code 1008
           - With invalid token: close code 1008
        
        4. Test message flow:
           - Server sends initial metric_update on connect
           - Client sends ping, server responds with pong
           - Server broadcasts metric updates when new metrics are posted
        """
        # This is a documentation test - actual WebSocket tests require
        # either httpx-ws or using the TestClient from Starlette
        pass


class TestWebSocketAuthenticationPatterns:
    """
    Demonstrates WebSocket authentication testing patterns.
    
    Since browsers cannot send cookies in WebSocket handshakes,
    we pass the JWT token as a query parameter.
    """
    
    async def test_websocket_auth_pattern_documentation(self):
        """
        WebSocket Authentication Pattern:
        
        1. User logs in via REST API:
           POST /api/v1/auth/login
           Response sets JWT cookie
        
        2. Client extracts token from cookie or response
        
        3. Client connects to WebSocket with token in query:
           ws://host/ws/miners/{id}/status?token={jwt}
        
        4. Server validates token before accepting connection
        
        Example client code (JavaScript):
        ```javascript
        // After login, get token from cookie
        const token = getCookie('access_token');
        
        // Connect to WebSocket
        const ws = new WebSocket(
            `ws://localhost:8000/ws/miners/${minerId}/status?token=${token}`
        );
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'metric_update') {
                updateMinerDisplay(data.data);
            }
        };
        
        // Send ping
        ws.send(JSON.stringify({type: 'ping'}));
        ```
        
        Example client code (Python with httpx-ws):
        ```python
        from httpx_ws import aconnect_ws
        
        async def monitor_miner(miner_id: str, token: str):
            url = f"ws://localhost:8000/ws/miners/{miner_id}/status"
            
            async with aconnect_ws(url, params={"token": token}) as ws:
                while True:
                    message = await ws.receive_json()
                    
                    if message["type"] == "metric_update":
                        print(f"Hashrate: {message['data']['hashrate_th']} TH/s")
        ```
        """
        pass


class TestWebSocketMessageFormats:
    """
    Documents the WebSocket message formats for reference.
    """
    
    async def test_message_format_documentation(self):
        """
        WebSocket Message Formats:
        
        1. Miner Status Messages (Server -> Client):
        ```json
        {
            "type": "metric_update",
            "miner_id": "uuid-string",
            "data": {
                "hashrate_th": 110.5,
                "temperature_c": 65.0,
                "power_watts": 3250.0,
                "status": "active"
            }
        }
        ```
        
        2. Alert Messages (Server -> Client):
        ```json
        {
            "type": "new_alert",
            "alert_id": "uuid-string",
            "severity": "critical",
            "alert_type": "high_temp",
            "message": "Temperature exceeded threshold",
            "miner_id": "uuid-string or null"
        }
        ```
        
        3. Connection Confirmation (Server -> Client):
        ```json
        {
            "type": "connected",
            "farm_id": "uuid-string",
            "message": "Subscribed to alert notifications"
        }
        ```
        
        4. Ping/Pong (Client <-> Server):
        ```json
        // Client sends:
        {"type": "ping"}
        
        // Server responds:
        {"type": "pong"}
        ```
        
        5. Error Codes:
        - 1008: Policy violation (auth failed, resource not found)
        - 1000: Normal closure
        """
        pass


# Example of how WebSocket tests would look with httpx-ws
# (Commented out as httpx-ws may not be installed)

# async def test_websocket_connect_with_httpx_ws():
#     """
#     Example WebSocket test using httpx-ws.
#     
#     Uncomment and run if httpx-ws is installed.
#     """
#     from httpx_ws import aconnect_ws
#     
#     # Setup
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     
#     # Create user and get token
#     token = await create_test_user_and_get_token("wsuser", UserRole.VIEWER)
#     
#     # Create farm and miner via REST API first
#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://test") as client:
#         # Login
#         await client.post(
#             "/api/v1/auth/login",
#             json={"username": "wsuser", "password": "testpassword123"}
#         )
#         
#         # Create farm
#         farm_resp = await client.post(
#             "/api/v1/farms",
#             json={"name": "WS Test Farm"}
#         )
#         farm_id = farm_resp.json()["id"]
#         
#         # Create miner
#         miner_resp = await client.post(
#             f"/api/v1/farms/{farm_id}/miners",
#             json={"name": "WS Miner", "model": "Antminer"}
#         )
#         miner_id = miner_resp.json()["id"]
#     
#     # Connect to WebSocket
#     async with aconnect_ws(
#         f"http://test/ws/miners/{miner_id}/status",
#         params={"token": token}
#     ) as ws:
#         # Receive initial message
#         message = await ws.receive_json()
#         assert message["type"] == "metric_update"
#         assert message["miner_id"] == miner_id
#         
#         # Send ping
#         await ws.send_json({"type": "ping"})
#         
#         # Receive pong
#         pong = await ws.receive_json()
#         assert pong["type"] == "pong"
#     
#     # Cleanup
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
