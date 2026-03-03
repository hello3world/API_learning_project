"""
Mining Farm Monitoring API - Main Application Entry Point.

This module initializes the FastAPI application, configures middleware,
and registers all routers.

To run the server:
    uvicorn api.main:app --reload --port 8000

API documentation available at:
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import settings
from api.database import close_db, init_db
from api.exceptions import APIException, api_exception_handler, http_exception_handler
from api.routers import (
    alerts_router,
    auth_router,
    farms_router,
    metrics_router,
    miners_router,
    websocket_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    
    Initializes database on startup and closes connections on shutdown.
    """
    # Startup
    print("Starting Mining Farm Monitoring API...")
    await init_db()
    print("Database initialized.")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await close_db()
    print("Database connections closed.")


# Create FastAPI application
app = FastAPI(
    title="Mining Farm Monitoring API",
    description="""
## Mining Farm Monitoring API

A comprehensive API for monitoring and managing Bitcoin mining farms.

### Features:
- **Authentication**: JWT-based authentication with HTTP-only cookies
- **Mining Farms**: Full CRUD operations for managing mining farms
- **Miners**: Manage individual mining hardware units (ASICs)
- **Metrics**: Track hashrate, temperature, power consumption, and shares
- **Alerts**: Create and manage system alerts with severity levels
- **WebSocket**: Real-time miner status and alert notifications

### Authentication:
1. Register a new account: `POST /api/v1/auth/register`
2. Login to get JWT cookie: `POST /api/v1/auth/login`
3. All subsequent requests will use the cookie automatically

### Roles:
- **viewer**: Read-only access to all resources
- **operator**: Can create/modify farms, miners, metrics, alerts
- **admin**: Full access including delete operations
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)


# Register routers with /api/v1 prefix
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(farms_router, prefix=API_PREFIX)
app.include_router(miners_router, prefix=API_PREFIX)
app.include_router(metrics_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)
app.include_router(websocket_router)  # WebSocket at root level


@app.get(
    "/api/v1/health",
    tags=["Health"],
    summary="Health check endpoint",
    responses={
        200: {"description": "API is healthy"},
    },
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns a simple status indicating the API is running.
    Use this endpoint for monitoring and load balancer health checks.
    
    **Response 200:**
    ```json
    {
        "status": "healthy",
        "version": "1.0.0"
    }
    ```
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint redirecting to documentation."""
    return {
        "message": "Mining Farm Monitoring API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health",
    }
