"""
Metrics endpoint tests.

This module demonstrates httpx testing patterns for:
- Time-series data
- Date range filters
- Query parameter handling

Key httpx learning points:
1. DateTime query parameters (ISO 8601 format)
2. Testing pagination with filters
3. Bulk delete operations
"""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestCreateMetric:
    """Tests for POST /api/v1/miners/{miner_id}/metrics"""
    
    async def test_create_metric_success(
        self, operator_client: AsyncClient, created_miner: dict
    ):
        """
        Test creating a metric snapshot.
        
        **Endpoint:** POST /api/v1/miners/{miner_id}/metrics
        **Expected:** 201 Created
        """
        miner_id = created_miner["id"]
        
        response = await operator_client.post(
            f"/api/v1/miners/{miner_id}/metrics",
            json={
                "hashrate_th": 110.5,
                "temperature_c": 65.0,
                "fan_speed_rpm": 4500,
                "power_watts": 3250.0,
                "accepted_shares": 1250,
                "rejected_shares": 3,
                "pool_difficulty": 65536.0,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["hashrate_th"] == 110.5
        assert data["temperature_c"] == 65.0
        assert data["power_watts"] == 3250.0
        assert data["miner_id"] == miner_id
        assert "recorded_at" in data
    
    async def test_create_metric_minimal(
        self, operator_client: AsyncClient, created_miner: dict
    ):
        """
        Test creating metric with only required fields.
        
        **Expected:** 201 with defaults for optional fields
        """
        miner_id = created_miner["id"]
        
        response = await operator_client.post(
            f"/api/v1/miners/{miner_id}/metrics",
            json={
                "hashrate_th": 100.0,
                "temperature_c": 60.0,
                "power_watts": 3000.0,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["accepted_shares"] == 0  # Default
        assert data["rejected_shares"] == 0  # Default
        assert data["fan_speed_rpm"] is None
    
    async def test_create_metric_miner_not_found(
        self, operator_client: AsyncClient
    ):
        """
        Test creating metric for non-existent miner.
        
        **Expected:** 404 Not Found
        """
        fake_miner_id = "00000000-0000-0000-0000-000000000000"
        
        response = await operator_client.post(
            f"/api/v1/miners/{fake_miner_id}/metrics",
            json={
                "hashrate_th": 100.0,
                "temperature_c": 60.0,
                "power_watts": 3000.0,
            },
        )
        
        assert response.status_code == 404


class TestListMetrics:
    """Tests for GET /api/v1/miners/{miner_id}/metrics"""
    
    async def test_list_metrics(
        self, operator_client: AsyncClient, created_miner: dict
    ):
        """
        Test listing metrics for a miner.
        
        **Expected:** 200 OK with paginated response
        """
        miner_id = created_miner["id"]
        
        # Create some metrics
        for i in range(3):
            await operator_client.post(
                f"/api/v1/miners/{miner_id}/metrics",
                json={
                    "hashrate_th": 100.0 + i,
                    "temperature_c": 60.0 + i,
                    "power_watts": 3000.0,
                },
            )
        
        response = await operator_client.get(f"/api/v1/miners/{miner_id}/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 3
        assert len(data["items"]) == 3
    
    async def test_list_metrics_with_date_filter(
        self, operator_client: AsyncClient, created_miner: dict
    ):
        """
        Test filtering metrics by date range.
        
        **Query params:** ?from_dt=...&to_dt=...
        **Expected:** Only metrics within range
        
        httpx pattern: DateTime query parameters
        """
        miner_id = created_miner["id"]
        
        # Create a metric
        await operator_client.post(
            f"/api/v1/miners/{miner_id}/metrics",
            json={
                "hashrate_th": 100.0,
                "temperature_c": 60.0,
                "power_watts": 3000.0,
            },
        )
        
        # Query with date range
        now = datetime.now(timezone.utc)
        from_dt = (now - timedelta(hours=1)).isoformat()
        to_dt = (now + timedelta(hours=1)).isoformat()
        
        response = await operator_client.get(
            f"/api/v1/miners/{miner_id}/metrics",
            params={
                "from_dt": from_dt,
                "to_dt": to_dt,
            },
        )
        
        assert response.status_code == 200
        assert response.json()["total"] >= 1


class TestLatestMetric:
    """Tests for GET /api/v1/miners/{miner_id}/metrics/latest"""
    
    async def test_get_latest_metric(
        self, operator_client: AsyncClient, created_miner: dict
    ):
        """
        Test getting the latest metric.
        
        **Endpoint:** GET /api/v1/miners/{miner_id}/metrics/latest
        **Expected:** 200 OK with single metric
        """
        miner_id = created_miner["id"]
        
        # Create metrics
        await operator_client.post(
            f"/api/v1/miners/{miner_id}/metrics",
            json={
                "hashrate_th": 100.0,
                "temperature_c": 60.0,
                "power_watts": 3000.0,
            },
        )
        await operator_client.post(
            f"/api/v1/miners/{miner_id}/metrics",
            json={
                "hashrate_th": 110.0,  # Latest
                "temperature_c": 65.0,
                "power_watts": 3100.0,
            },
        )
        
        response = await operator_client.get(
            f"/api/v1/miners/{miner_id}/metrics/latest"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be the latest one
        assert data["hashrate_th"] == 110.0
    
    async def test_get_latest_metric_no_metrics(
        self, viewer_client: AsyncClient, created_miner: dict
    ):
        """
        Test getting latest metric when none exist.
        
        **Expected:** 404 Not Found
        """
        miner_id = created_miner["id"]
        
        response = await viewer_client.get(
            f"/api/v1/miners/{miner_id}/metrics/latest"
        )
        
        assert response.status_code == 404


class TestDeleteMetrics:
    """Tests for DELETE /api/v1/miners/{miner_id}/metrics"""
    
    async def test_delete_metrics_all(self, admin_client: AsyncClient):
        """
        Test bulk deleting all metrics for a miner.
        
        **Endpoint:** DELETE /api/v1/miners/{miner_id}/metrics
        **Expected:** 204 No Content
        """
        # Create farm and miner
        farm_response = await admin_client.post(
            "/api/v1/farms",
            json={"name": "Metric Delete Test Farm"},
        )
        farm_id = farm_response.json()["id"]
        
        miner_response = await admin_client.post(
            f"/api/v1/farms/{farm_id}/miners",
            json={"name": "Miner", "model": "Antminer"},
        )
        miner_id = miner_response.json()["id"]
        
        # Create metrics
        for _ in range(3):
            await admin_client.post(
                f"/api/v1/miners/{miner_id}/metrics",
                json={
                    "hashrate_th": 100.0,
                    "temperature_c": 60.0,
                    "power_watts": 3000.0,
                },
            )
        
        # Delete all metrics
        response = await admin_client.delete(f"/api/v1/miners/{miner_id}/metrics")
        
        assert response.status_code == 204
        
        # Verify deleted
        list_response = await admin_client.get(
            f"/api/v1/miners/{miner_id}/metrics"
        )
        assert list_response.json()["total"] == 0
    
    async def test_delete_metrics_requires_admin(
        self, operator_client: AsyncClient, created_miner: dict
    ):
        """
        Test that only admins can delete metrics.
        
        **Expected:** 403 Forbidden
        """
        miner_id = created_miner["id"]
        
        response = await operator_client.delete(
            f"/api/v1/miners/{miner_id}/metrics"
        )
        
        assert response.status_code == 403
