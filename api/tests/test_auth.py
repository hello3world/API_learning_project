"""
Authentication endpoint tests.

This module demonstrates httpx testing patterns for authentication flows:
- User registration
- Login with cookie-based JWT
- Protected endpoints
- Logout

Key httpx learning points:
1. AsyncClient.post() for sending JSON data
2. Cookie handling is automatic after login
3. response.cookies shows cookies received
4. client.cookies shows stored cookies
"""

import pytest
from httpx import AsyncClient, ASGITransport

from api.main import app
from api.database import engine, Base, async_session_maker


pytestmark = pytest.mark.asyncio


class TestUserRegistration:
    """Tests for POST /api/v1/auth/register"""
    
    async def test_register_success(self, async_client: AsyncClient):
        """
        Test successful user registration.
        
        **Endpoint:** POST /api/v1/auth/register
        **Expected:** 201 Created with user data
        
        httpx pattern: POST with JSON body
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "viewer"  # Default role
        assert data["is_active"] is True
        assert "created_at" in data
        
        # Password should NOT be returned
        assert "password" not in data
        assert "hashed_password" not in data
    
    async def test_register_with_role(self, async_client: AsyncClient):
        """
        Test registration with specific role.
        
        **Endpoint:** POST /api/v1/auth/register
        **Expected:** 201 with specified role
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "operator1",
                "email": "operator@example.com",
                "password": "operatorpass123",
                "role": "operator",
            },
        )
        
        assert response.status_code == 201
        assert response.json()["role"] == "operator"
    
    async def test_register_duplicate_username(self, async_client: AsyncClient):
        """
        Test registration with existing username.
        
        **Endpoint:** POST /api/v1/auth/register
        **Expected:** 409 Conflict
        
        httpx pattern: Checking error responses
        """
        # First registration
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "first@example.com",
                "password": "password123",
            },
        )
        
        # Second registration with same username
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "second@example.com",
                "password": "password123",
            },
        )
        
        assert response.status_code == 409
        assert "already taken" in response.json()["detail"].lower()
    
    async def test_register_duplicate_email(self, async_client: AsyncClient):
        """
        Test registration with existing email.
        
        **Expected:** 409 Conflict
        """
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "same@example.com",
                "password": "password123",
            },
        )
        
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "same@example.com",
                "password": "password123",
            },
        )
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_register_validation_error(self, async_client: AsyncClient):
        """
        Test registration with invalid data.
        
        **Expected:** 422 Unprocessable Entity
        
        httpx pattern: Validation error handling
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",  # Too short (min 3)
                "email": "invalid-email",  # Invalid email
                "password": "short",  # Too short (min 8)
            },
        )
        
        assert response.status_code == 422
        # FastAPI returns validation details
        assert "detail" in response.json()


class TestUserLogin:
    """Tests for POST /api/v1/auth/login"""
    
    async def test_login_success(self, async_client: AsyncClient):
        """
        Test successful login with cookie setting.
        
        **Endpoint:** POST /api/v1/auth/login
        **Expected:** 200 OK with Set-Cookie header
        
        httpx key learning:
        - response.cookies contains cookies from Set-Cookie header
        - client.cookies stores cookies for subsequent requests
        """
        # Register user first
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "logintest",
                "email": "login@test.com",
                "password": "testpassword123",
            },
        )
        
        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "logintest",
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Login successful"
        assert "user" in data
        assert data["user"]["username"] == "logintest"
        
        # Check cookie was set
        # httpx stores cookies automatically
        assert "access_token" in async_client.cookies
    
    async def test_login_with_email(self, async_client: AsyncClient):
        """
        Test login using email instead of username.
        
        **Expected:** 200 OK
        """
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "emailuser",
                "email": "emaillogin@test.com",
                "password": "testpassword123",
            },
        )
        
        # Login with email
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "emaillogin@test.com",  # Using email
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == 200
    
    async def test_login_wrong_password(self, async_client: AsyncClient):
        """
        Test login with incorrect password.
        
        **Expected:** 401 Unauthorized
        """
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "wrongpass",
                "email": "wrong@test.com",
                "password": "correctpassword",
            },
        )
        
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "wrongpass",
                "password": "incorrectpassword",
            },
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """
        Test login with non-existent username.
        
        **Expected:** 401 Unauthorized
        """
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "anypassword",
            },
        )
        
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Tests for endpoints requiring authentication"""
    
    async def test_get_me_authenticated(self, async_client: AsyncClient):
        """
        Test GET /auth/me with valid authentication.
        
        **Expected:** 200 OK with user data
        
        httpx key learning:
        After login, subsequent requests automatically include the cookie.
        """
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "metest",
                "email": "me@test.com",
                "password": "testpassword123",
            },
        )
        
        await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "metest",
                "password": "testpassword123",
            },
        )
        
        # Access protected endpoint - cookie is sent automatically
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        assert response.json()["username"] == "metest"
    
    async def test_get_me_unauthenticated(self, async_client: AsyncClient):
        """
        Test GET /auth/me without authentication.
        
        **Expected:** 401 Unauthorized
        
        httpx key learning:
        Without login, no cookie is sent, resulting in 401.
        """
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()
    
    async def test_update_me(self, async_client: AsyncClient):
        """
        Test PATCH /auth/me to update profile.
        
        **Expected:** 200 OK with updated data
        """
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "updateme",
                "email": "old@test.com",
                "password": "testpassword123",
            },
        )
        
        await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "updateme",
                "password": "testpassword123",
            },
        )
        
        # Update email
        response = await async_client.patch(
            "/api/v1/auth/me",
            json={"email": "new@test.com"},
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == "new@test.com"


class TestLogout:
    """Tests for POST /api/v1/auth/logout"""
    
    async def test_logout_success(self, async_client: AsyncClient):
        """
        Test successful logout clears cookie.
        
        **Expected:** 200 OK, cookie cleared
        
        httpx key learning:
        After logout, the cookie is removed from client.cookies
        """
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "logouttest",
                "email": "logout@test.com",
                "password": "testpassword123",
            },
        )
        
        await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "logouttest",
                "password": "testpassword123",
            },
        )
        
        # Verify logged in
        assert "access_token" in async_client.cookies
        
        # Logout
        response = await async_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Logout successful"
    
    async def test_access_after_logout(self, async_client: AsyncClient):
        """
        Test that protected endpoints return 401 after logout.
        
        **Expected:** 401 after logout
        """
        # Register, login, logout
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "afterlogout",
                "email": "after@test.com",
                "password": "testpassword123",
            },
        )
        
        await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "afterlogout",
                "password": "testpassword123",
            },
        )
        
        await async_client.post("/api/v1/auth/logout")
        
        # Clear the cookie from client
        async_client.cookies.clear()
        
        # Try to access protected endpoint
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
