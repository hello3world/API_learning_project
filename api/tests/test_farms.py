"""
Mining Farms endpoint tests.

This module demonstrates httpx testing patterns for CRUD operations:
- GET (list and single item)
- POST (create)
- PUT (full update)
- PATCH (partial update)
- DELETE

Key httpx learning points:
1. JSON request bodies with json= parameter
2. Path parameters in URL
3. Query parameters with params= dict
4. Response status code and body assertions
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestListFarms:
    """Tests for GET /api/v1/farms"""
    
    async def test_list_farms_authenticated(self, viewer_client: AsyncClient):
        """
        Test listing farms with valid authentication.
        
        **Endpoint:** GET /api/v1/farms
        **Expected:** 200 OK with paginated response
        
        httpx pattern: GET request with automatic cookie auth
        """
        response = await viewer_client.get("/api/v1/farms")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        
        assert isinstance(data["items"], list)
        assert data["page"] == 1
        assert data["size"] == 10  # Default
    
    async def test_list_farms_unauthenticated(self, async_client: AsyncClient):
        """
        Test listing farms without authentication.
        
        **Expected:** 401 Unauthorized
        """
        response = await async_client.get("/api/v1/farms")
        
        assert response.status_code == 401
    
    async def test_list_farms_with_pagination(
        self, operator_client: AsyncClient
    ):
        """
        Test listing farms with custom pagination.
        
        **Query params:** ?page=1&size=5
        **Expected:** 200 OK with specified page size
        
        httpx pattern: Query parameters with params dict
        """
        # Create some farms first
        for i in range(3):
            await operator_client.post(
                "/api/v1/farms",
                json={"name": f"Farm {i}", "status": "offline"},
            )
        
        # Request with pagination
        response = await operator_client.get(
            "/api/v1/farms",
            params={"page": 1, "size": 2},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["size"] == 2
        assert len(data["items"]) <= 2
    
    async def test_list_farms_with_status_filter(
        self, operator_client: AsyncClient
    ):
        """
        Test filtering farms by status.
        
        **Query params:** ?status=online
        **Expected:** Only farms with matching status
        
        httpx pattern: Query parameter filtering
        """
        # Create farms with different statuses
        await operator_client.post(
            "/api/v1/farms",
            json={"name": "Online Farm", "status": "online"},
        )
        await operator_client.post(
            "/api/v1/farms",
            json={"name": "Offline Farm", "status": "offline"},
        )
        
        # Filter by status
        response = await operator_client.get(
            "/api/v1/farms",
            params={"status": "online"},
        )
        
        assert response.status_code == 200
        
        for item in response.json()["items"]:
            assert item["status"] == "online"


class TestCreateFarm:
    """Tests for POST /api/v1/farms"""
    
    async def test_create_farm_as_operator(self, operator_client: AsyncClient):
        """
        Test creating a farm as operator.
        
        **Endpoint:** POST /api/v1/farms
        **Expected:** 201 Created
        
        httpx pattern: POST with JSON body
        """
        response = await operator_client.post(
            "/api/v1/farms",
            json={
                "name": "Bitcoin Farm Alpha",
                "location": "Warehouse A, Industrial District",
                "total_power_kw": 500.0,
                "status": "offline",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response
        assert "id" in data
        assert data["name"] == "Bitcoin Farm Alpha"
        assert data["location"] == "Warehouse A, Industrial District"
        assert data["total_power_kw"] == 500.0
        assert data["status"] == "offline"
        assert "created_at" in data
        assert "updated_at" in data
        assert data["miners_count"] == 0
    
    async def test_create_farm_as_viewer_forbidden(
        self, viewer_client: AsyncClient
    ):
        """
        Test that viewers cannot create farms.
        
        **Expected:** 403 Forbidden
        
        httpx pattern: Testing role-based access
        """
        response = await viewer_client.post(
            "/api/v1/farms",
            json={"name": "Unauthorized Farm"},
        )
        
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()
    
    async def test_create_farm_minimal(self, operator_client: AsyncClient):
        """
        Test creating farm with only required fields.
        
        **Expected:** 201 with defaults applied
        """
        response = await operator_client.post(
            "/api/v1/farms",
            json={"name": "Minimal Farm"},
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Minimal Farm"
        assert data["location"] is None
        assert data["total_power_kw"] is None
        assert data["status"] == "offline"  # Default
    
    async def test_create_farm_validation_error(
        self, operator_client: AsyncClient
    ):
        """
        Test creating farm with invalid data.
        
        **Expected:** 422 Unprocessable Entity
        """
        response = await operator_client.post(
            "/api/v1/farms",
            json={
                "name": "",  # Empty name not allowed
                "total_power_kw": -100,  # Must be > 0
            },
        )
        
        assert response.status_code == 422


class TestGetFarm:
    """Tests for GET /api/v1/farms/{farm_id}"""
    
    async def test_get_farm_success(
        self, viewer_client: AsyncClient, created_farm: dict
    ):
        """
        Test getting a single farm by ID.
        
        **Endpoint:** GET /api/v1/farms/{farm_id}
        **Expected:** 200 OK with farm data
        
        httpx pattern: Path parameters in URL
        """
        farm_id = created_farm["id"]
        
        response = await viewer_client.get(f"/api/v1/farms/{farm_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == farm_id
        assert data["name"] == created_farm["name"]
    
    async def test_get_farm_not_found(self, viewer_client: AsyncClient):
        """
        Test getting non-existent farm.
        
        **Expected:** 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = await viewer_client.get(f"/api/v1/farms/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateFarm:
    """Tests for PUT /api/v1/farms/{farm_id}"""
    
    async def test_update_farm_full(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test full update of a farm (PUT).
        
        **Endpoint:** PUT /api/v1/farms/{farm_id}
        **Expected:** 200 OK with all fields updated
        
        httpx pattern: PUT with full object replacement
        """
        farm_id = created_farm["id"]
        
        response = await operator_client.put(
            f"/api/v1/farms/{farm_id}",
            json={
                "name": "Updated Farm Name",
                "location": "New Location",
                "total_power_kw": 750.0,
                "status": "online",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated Farm Name"
        assert data["location"] == "New Location"
        assert data["total_power_kw"] == 750.0
        assert data["status"] == "online"


class TestPatchFarm:
    """Tests for PATCH /api/v1/farms/{farm_id}"""
    
    async def test_patch_farm_status_only(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test partial update - only change status.
        
        **Endpoint:** PATCH /api/v1/farms/{farm_id}
        **Expected:** 200 OK, only status changed
        
        httpx pattern: PATCH with partial data
        """
        farm_id = created_farm["id"]
        original_name = created_farm["name"]
        
        response = await operator_client.patch(
            f"/api/v1/farms/{farm_id}",
            json={"status": "maintenance"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Status changed
        assert data["status"] == "maintenance"
        # Name unchanged
        assert data["name"] == original_name
    
    async def test_patch_farm_multiple_fields(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test partial update with multiple fields.
        
        **Expected:** Only specified fields updated
        """
        farm_id = created_farm["id"]
        
        response = await operator_client.patch(
            f"/api/v1/farms/{farm_id}",
            json={
                "name": "Patched Name",
                "total_power_kw": 999.9,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Patched Name"
        assert data["total_power_kw"] == 999.9


class TestDeleteFarm:
    """Tests for DELETE /api/v1/farms/{farm_id}"""
    
    async def test_delete_farm_as_admin(
        self, admin_client: AsyncClient
    ):
        """
        Test deleting a farm as admin.
        
        **Endpoint:** DELETE /api/v1/farms/{farm_id}
        **Expected:** 204 No Content
        
        httpx pattern: DELETE request, expect no body
        """
        # Create a farm to delete
        create_response = await admin_client.post(
            "/api/v1/farms",
            json={"name": "Farm To Delete"},
        )
        farm_id = create_response.json()["id"]
        
        # Delete
        response = await admin_client.delete(f"/api/v1/farms/{farm_id}")
        
        assert response.status_code == 204
        
        # Verify deleted
        get_response = await admin_client.get(f"/api/v1/farms/{farm_id}")
        assert get_response.status_code == 404
    
    async def test_delete_farm_as_operator_forbidden(
        self, operator_client: AsyncClient, created_farm: dict
    ):
        """
        Test that operators cannot delete farms.
        
        **Expected:** 403 Forbidden
        """
        farm_id = created_farm["id"]
        
        response = await operator_client.delete(f"/api/v1/farms/{farm_id}")
        
        assert response.status_code == 403
    
    async def test_delete_farm_not_found(self, admin_client: AsyncClient):
        """
        Test deleting non-existent farm.
        
        **Expected:** 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = await admin_client.delete(f"/api/v1/farms/{fake_id}")
        
        assert response.status_code == 404


class TestFarmSummary:
    """Tests for GET /api/v1/farms/{farm_id}/summary"""
    
    async def test_get_farm_summary(
        self, viewer_client: AsyncClient, created_farm: dict
    ):
        """
        Test getting farm aggregated statistics.
        
        **Endpoint:** GET /api/v1/farms/{farm_id}/summary
        **Expected:** 200 OK with aggregated data
        """
        farm_id = created_farm["id"]
        
        response = await viewer_client.get(f"/api/v1/farms/{farm_id}/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure (empty farm)
        assert data["farm_id"] == farm_id
        assert "total_hashrate_th" in data
        assert "active_miners" in data
        assert "total_miners" in data
        assert "total_power_watts" in data
        assert "avg_temperature_c" in data
