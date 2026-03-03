"""
Miners endpoint tests.

This module demonstrates httpx testing patterns for nested resources.
Miners belong to farms, so URLs include farm_id.

Key httpx learning points:
1. Testing nested resource URLs
2. Validating response relationships
3. Testing unique constraints (duplicate IP)
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestListMiners:
    """Tests for GET /api/v1/farms/{farm_id}/miners"""
    
    async def test_list_miners(
        self, viewer_client: AsyncClient, created_farm: dict
    ):
        """
        Test listing miners in a farm.
        
        **Endpoint:** GET /api/v1/farms/{farm_id}/miners
        **Expected:** 200 OK with paginated response
        """
        farm_id = created_farm["id"]
        
        response = await viewer_client.get(f"/api/v1/farms/{farm_id}/miners")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
    
    async def test_list_miners_farm_not_found(self, viewer_client: AsyncClient):
        """
        Test listing miners for non-existent farm.
        
        **Expected:** 404 Not Found
        """
        fake_farm_id = "00000000-0000-0000-0000-000000000000"
        
        response = await viewer_client.get(f"/api/v1/farms/{fake_farm_id}/miners")
        
        assert response.status_code == 404


class TestCreateMiner:
    """Tests for POST /api/v1/farms/{farm_id}/miners"""
    
    async def test_create_miner_success(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test creating a miner in a farm.
        
        **Endpoint:** POST /api/v1/farms/{farm_id}/miners
        **Expected:** 201 Created
        """
        farm_id = created_farm["id"]
        
        response = await operator_client.post(
            f"/api/v1/farms/{farm_id}/miners",
            json={
                "name": "Miner-001",
                "model": "Antminer S19 Pro",
                "ip_address": "192.168.1.101",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "status": "active",
                "worker_name": "farm1.worker001",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Miner-001"
        assert data["model"] == "Antminer S19 Pro"
        assert data["ip_address"] == "192.168.1.101"
        assert data["farm_id"] == farm_id
        assert data["status"] == "active"
    
    async def test_create_miner_duplicate_ip(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test creating miner with duplicate IP address.
        
        **Expected:** 409 Conflict
        """
        farm_id = created_farm["id"]
        
        # First miner
        await operator_client.post(
            f"/api/v1/farms/{farm_id}/miners",
            json={
                "name": "Miner-1",
                "model": "Antminer S19",
                "ip_address": "192.168.1.50",
            },
        )
        
        # Second miner with same IP
        response = await operator_client.post(
            f"/api/v1/farms/{farm_id}/miners",
            json={
                "name": "Miner-2",
                "model": "Antminer S19",
                "ip_address": "192.168.1.50",  # Duplicate
            },
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
    
    async def test_create_miner_as_viewer_forbidden(
        self, viewer_client: AsyncClient, created_farm: dict
    ):
        """
        Test that viewers cannot create miners.
        
        **Expected:** 403 Forbidden
        """
        farm_id = created_farm["id"]
        
        response = await viewer_client.post(
            f"/api/v1/farms/{farm_id}/miners",
            json={
                "name": "Miner",
                "model": "Antminer",
            },
        )
        
        assert response.status_code == 403


class TestGetMiner:
    """Tests for GET miner endpoints"""
    
    async def test_get_miner_via_farm(
        self, viewer_client: AsyncClient, created_miner: dict, created_farm: dict
    ):
        """
        Test getting miner via farm path.
        
        **Endpoint:** GET /api/v1/farms/{farm_id}/miners/{miner_id}
        **Expected:** 200 OK
        """
        farm_id = created_farm["id"]
        miner_id = created_miner["id"]
        
        response = await viewer_client.get(
            f"/api/v1/farms/{farm_id}/miners/{miner_id}"
        )
        
        assert response.status_code == 200
        assert response.json()["id"] == miner_id
    
    async def test_get_miner_direct(
        self, viewer_client: AsyncClient, created_miner: dict
    ):
        """
        Test getting miner directly by ID.
        
        **Endpoint:** GET /api/v1/miners/{miner_id}
        **Expected:** 200 OK
        """
        miner_id = created_miner["id"]
        
        response = await viewer_client.get(f"/api/v1/miners/{miner_id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == miner_id


class TestUpdateMiner:
    """Tests for PUT and PATCH miner endpoints"""
    
    async def test_update_miner_full(
        self,
        operator_client: AsyncClient,
        created_miner: dict,
        created_farm: dict,
    ):
        """
        Test full update of a miner.
        
        **Endpoint:** PUT /api/v1/farms/{farm_id}/miners/{miner_id}
        **Expected:** 200 OK
        """
        farm_id = created_farm["id"]
        miner_id = created_miner["id"]
        
        response = await operator_client.put(
            f"/api/v1/farms/{farm_id}/miners/{miner_id}",
            json={
                "name": "Updated Miner",
                "model": "Antminer S21",
                "ip_address": "192.168.1.200",
                "mac_address": "11:22:33:44:55:66",
                "status": "maintenance",
                "worker_name": "updated.worker",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated Miner"
        assert data["model"] == "Antminer S21"
        assert data["status"] == "maintenance"
    
    async def test_patch_miner_status(
        self,
        operator_client: AsyncClient,
        created_miner: dict,
        created_farm: dict,
    ):
        """
        Test partial update - change status only.
        
        **Endpoint:** PATCH /api/v1/farms/{farm_id}/miners/{miner_id}
        **Expected:** 200 OK, only status changed
        """
        farm_id = created_farm["id"]
        miner_id = created_miner["id"]
        original_name = created_miner["name"]
        
        response = await operator_client.patch(
            f"/api/v1/farms/{farm_id}/miners/{miner_id}",
            json={"status": "error"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "error"
        assert data["name"] == original_name  # Unchanged


class TestDeleteMiner:
    """Tests for DELETE /api/v1/farms/{farm_id}/miners/{miner_id}"""
    
    async def test_delete_miner_as_admin(self, admin_client: AsyncClient):
        """
        Test deleting a miner as admin.
        
        **Expected:** 204 No Content
        """
        # Create farm and miner
        farm_response = await admin_client.post(
            "/api/v1/farms",
            json={"name": "Farm for deletion test"},
        )
        farm_id = farm_response.json()["id"]
        
        miner_response = await admin_client.post(
            f"/api/v1/farms/{farm_id}/miners",
            json={
                "name": "Miner to delete",
                "model": "Antminer S19",
            },
        )
        miner_id = miner_response.json()["id"]
        
        # Delete miner
        response = await admin_client.delete(
            f"/api/v1/farms/{farm_id}/miners/{miner_id}"
        )
        
        assert response.status_code == 204
        
        # Verify deleted
        get_response = await admin_client.get(
            f"/api/v1/farms/{farm_id}/miners/{miner_id}"
        )
        assert get_response.status_code == 404
    
    async def test_delete_miner_as_operator_forbidden(
        self,
        operator_client: AsyncClient,
        created_miner: dict,
        created_farm: dict,
    ):
        """
        Test that operators cannot delete miners.
        
        **Expected:** 403 Forbidden
        """
        farm_id = created_farm["id"]
        miner_id = created_miner["id"]
        
        response = await operator_client.delete(
            f"/api/v1/farms/{farm_id}/miners/{miner_id}"
        )
        
        assert response.status_code == 403
