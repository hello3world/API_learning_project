"""
Alerts endpoint tests.

This module demonstrates httpx testing patterns for:
- Filtering with multiple query parameters
- State transitions (acknowledge)
- Error handling for business logic

Key httpx learning points:
1. Multiple query parameters
2. Testing state changes
3. Business rule validation (already acknowledged)
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestListAlerts:
    """Tests for GET /api/v1/alerts"""
    
    async def test_list_alerts(self, viewer_client: AsyncClient):
        """
        Test listing all alerts.
        
        **Endpoint:** GET /api/v1/alerts
        **Expected:** 200 OK with paginated response
        """
        response = await viewer_client.get("/api/v1/alerts")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
    
    async def test_list_alerts_with_filters(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test filtering alerts by multiple parameters.
        
        **Query params:** ?farm_id=...&severity=critical&is_acknowledged=false
        **Expected:** Only matching alerts
        
        httpx pattern: Multiple query parameters
        """
        farm_id = created_farm["id"]
        
        # Create alerts with different severities
        await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "severity": "critical",
                "alert_type": "high_temp",
                "message": "Critical alert",
            },
        )
        await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "severity": "info",
                "message": "Info alert",
            },
        )
        
        # Filter by severity
        response = await operator_client.get(
            "/api/v1/alerts",
            params={
                "farm_id": farm_id,
                "severity": "critical",
            },
        )
        
        assert response.status_code == 200
        
        for item in response.json()["items"]:
            assert item["severity"] == "critical"


class TestCreateAlert:
    """Tests for POST /api/v1/alerts"""
    
    async def test_create_alert_success(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test creating a manual alert.
        
        **Endpoint:** POST /api/v1/alerts
        **Expected:** 201 Created
        """
        farm_id = created_farm["id"]
        
        response = await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "severity": "warning",
                "alert_type": "low_hashrate",
                "message": "Hashrate dropped below 90 TH/s",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["farm_id"] == farm_id
        assert data["severity"] == "warning"
        assert data["alert_type"] == "low_hashrate"
        assert data["is_acknowledged"] is False
        assert data["acknowledged_by"] is None
    
    async def test_create_alert_with_miner(
        self,
        operator_client: AsyncClient,
        created_farm: dict,
        created_miner: dict,
    ):
        """
        Test creating an alert linked to a specific miner.
        
        **Expected:** 201 with miner_id set
        """
        farm_id = created_farm["id"]
        miner_id = created_miner["id"]
        
        response = await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "miner_id": miner_id,
                "severity": "critical",
                "alert_type": "high_temp",
                "message": "Miner temperature exceeded 85C",
            },
        )
        
        assert response.status_code == 201
        assert response.json()["miner_id"] == miner_id
    
    async def test_create_alert_farm_not_found(
        self, operator_client: AsyncClient
    ):
        """
        Test creating alert for non-existent farm.
        
        **Expected:** 404 Not Found
        """
        fake_farm_id = "00000000-0000-0000-0000-000000000000"
        
        response = await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": fake_farm_id,
                "message": "Test alert",
            },
        )
        
        assert response.status_code == 404


class TestGetAlert:
    """Tests for GET /api/v1/alerts/{alert_id}"""
    
    async def test_get_alert_success(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test getting a single alert by ID.
        
        **Expected:** 200 OK
        """
        farm_id = created_farm["id"]
        
        # Create alert
        create_response = await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "message": "Test alert",
            },
        )
        alert_id = create_response.json()["id"]
        
        # Get alert
        response = await operator_client.get(f"/api/v1/alerts/{alert_id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == alert_id
    
    async def test_get_alert_not_found(self, viewer_client: AsyncClient):
        """
        Test getting non-existent alert.
        
        **Expected:** 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = await viewer_client.get(f"/api/v1/alerts/{fake_id}")
        
        assert response.status_code == 404


class TestAcknowledgeAlert:
    """Tests for PATCH /api/v1/alerts/{alert_id}/acknowledge"""
    
    async def test_acknowledge_alert_success(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test acknowledging an alert.
        
        **Endpoint:** PATCH /api/v1/alerts/{alert_id}/acknowledge
        **Expected:** 200 OK with acknowledgment info
        
        httpx pattern: State transition endpoint
        """
        farm_id = created_farm["id"]
        
        # Create alert
        create_response = await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "severity": "critical",
                "message": "Alert to acknowledge",
            },
        )
        alert_id = create_response.json()["id"]
        
        # Acknowledge
        response = await operator_client.patch(
            f"/api/v1/alerts/{alert_id}/acknowledge"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_acknowledged"] is True
        assert data["acknowledged_by"] is not None
        assert data["acknowledged_at"] is not None
    
    async def test_acknowledge_already_acknowledged(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test acknowledging an already acknowledged alert.
        
        **Expected:** 400 Bad Request
        
        httpx pattern: Business rule validation
        """
        farm_id = created_farm["id"]
        
        # Create and acknowledge alert
        create_response = await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "message": "Already acked alert",
            },
        )
        alert_id = create_response.json()["id"]
        
        # First acknowledge
        await operator_client.patch(f"/api/v1/alerts/{alert_id}/acknowledge")
        
        # Second acknowledge - should fail
        response = await operator_client.patch(
            f"/api/v1/alerts/{alert_id}/acknowledge"
        )
        
        assert response.status_code == 400
        assert "already acknowledged" in response.json()["detail"].lower()
    
    async def test_acknowledge_as_viewer_forbidden(
        self, viewer_client: AsyncClient, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test that viewers cannot acknowledge alerts.
        
        **Expected:** 403 Forbidden
        """
        farm_id = created_farm["id"]
        
        # Create alert as operator
        create_response = await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "message": "Viewer cannot ack",
            },
        )
        alert_id = create_response.json()["id"]
        
        # Try to acknowledge as viewer
        response = await viewer_client.patch(
            f"/api/v1/alerts/{alert_id}/acknowledge"
        )
        
        assert response.status_code == 403


class TestDeleteAlert:
    """Tests for DELETE /api/v1/alerts/{alert_id}"""
    
    async def test_delete_alert_as_admin(self, admin_client: AsyncClient):
        """
        Test deleting an alert as admin.
        
        **Expected:** 204 No Content
        """
        # Create farm and alert
        farm_response = await admin_client.post(
            "/api/v1/farms",
            json={"name": "Alert Delete Test"},
        )
        farm_id = farm_response.json()["id"]
        
        alert_response = await admin_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "message": "Alert to delete",
            },
        )
        alert_id = alert_response.json()["id"]
        
        # Delete
        response = await admin_client.delete(f"/api/v1/alerts/{alert_id}")
        
        assert response.status_code == 204
        
        # Verify deleted
        get_response = await admin_client.get(f"/api/v1/alerts/{alert_id}")
        assert get_response.status_code == 404
    
    async def test_delete_alert_as_operator_forbidden(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test that operators cannot delete alerts.
        
        **Expected:** 403 Forbidden
        """
        farm_id = created_farm["id"]
        
        # Create alert
        create_response = await operator_client.post(
            "/api/v1/alerts",
            json={
                "farm_id": farm_id,
                "message": "Operator cannot delete",
            },
        )
        alert_id = create_response.json()["id"]
        
        # Try to delete
        response = await operator_client.delete(f"/api/v1/alerts/{alert_id}")
        
        assert response.status_code == 403
