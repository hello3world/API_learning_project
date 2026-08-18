# Mining Farm Monitoring API

A learning project for practicing **httpx** API testing with FastAPI.

## About This Project

This is an educational API created with AI assistance specifically designed for practicing and mastering REST API automation testing. The project serves as a sandbox environment for:

- Testing and validating pet projects related to API automation
- Reinforcing theoretical knowledge of REST API concepts
- Practicing various HTTP methods, authentication patterns, and testing strategies
- Experimenting with modern API development tools and frameworks

Feel free to use this project as a reference, template, or learning resource for your own API automation journey!


## Features

- **REST API** with all HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **WebSocket** endpoints for real-time updates
- **JWT authentication** via HTTP-only cookies
- **Role-based access control** (admin, operator, viewer)
- **PostgreSQL** database with Docker
- **Swagger/OpenAPI** documentation
- **Comprehensive httpx test examples**

## Quick Start

### 1. Prerequisites

- Python 3.13+ (recommended) or Python 3.11+
- Docker & Docker Compose
- Git

**Note**: If you encounter dependency compilation errors with Python 3.13+, the project uses `psycopg` (pure Python PostgreSQL driver) instead of `asyncpg` to avoid C extension compilation issues.

### 2. Clone and Setup

```bash
# Navigate to project directory
cd 

# Create and activate virtual environment (if not exists)
python -m venv .venv
# .venv\Scripts\activate  # Windows

python3 -m venv .venv
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Start PostgreSQL

```bash
# Start PostgreSQL container
docker compose up -d db

# Verify it's running
docker compose ps
```

**Important**: The database is configured to run on port **5433** to avoid conflicts with local PostgreSQL installations. If you need to use the default port 5432, ensure no other PostgreSQL instance is running on your system.

### 4. Configure Environment

```bash
# Copy example environment file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env and change SECRET_KEY to a secure random string
```

### 5. Run Database Migrations

```bash
# Apply migrations
alembic upgrade head
```

### 6. Start the API Server

```bash
# Run with auto-reload for development
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

```

### 7. Access the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## Running Tests

```bash
# Run all tests
pytest api/tests/ -v

# Run specific test file
pytest api/tests/test_auth.py -v

# Run with coverage
*pytest api/tests/ -v --cov=api --cov-report=html*
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user |
| POST | /api/v1/auth/login | Login (sets JWT cookie) |
| POST | /api/v1/auth/logout | Logout (clears cookie) |
| GET | /api/v1/auth/me | Get current user |
| PATCH | /api/v1/auth/me | Update current user |
| DELETE | /api/v1/auth/users/{id} | Delete user by ID |

### Mining Farms
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/farms | List farms (paginated) |
| POST | /api/v1/farms | Create farm |
| GET | /api/v1/farms/{id} | Get farm |
| PUT | /api/v1/farms/{id} | Full update |
| PATCH | /api/v1/farms/{id} | Partial update |
| DELETE | /api/v1/farms/{id} | Delete farm |

### Miners
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/farms/{farm_id}/miners | List miners |
| POST | /api/v1/farms/{farm_id}/miners | Create miner |
| GET | /api/v1/farms/{farm_id}/miners/{id} | Get miner |
| PUT | /api/v1/farms/{farm_id}/miners/{id} | Full update |
| PATCH | /api/v1/farms/{farm_id}/miners/{id} | Partial update |
| DELETE | /api/v1/farms/{farm_id}/miners/{id} | Delete miner |

### Metrics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/miners/{miner_id}/metrics | List metrics |
| POST | /api/v1/miners/{miner_id}/metrics | Create metric |
| GET | /api/v1/miners/{miner_id}/metrics/latest | Get latest |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/alerts | List alerts |
| POST | /api/v1/alerts | Create alert |
| PATCH | /api/v1/alerts/{id}/acknowledge | Acknowledge |
| DELETE | /api/v1/alerts/{id} | Delete alert |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| ws://host/ws/miners/{id}/status?token=JWT | Miner status stream |
| ws://host/ws/farms/{id}/alerts?token=JWT | Farm alerts stream |

## User Roles

| Role | Permissions |
|------|-------------|
| **viewer** | Read-only access to all resources |
| **operator** | Create/modify farms, miners, metrics, alerts |
| **admin** | Full access including delete operations |

## httpx Learning Guide

### Basic GET Request
```python
import httpx

async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
    response = await client.get("/api/v1/health")
    print(response.status_code)  # 200
    print(response.json())       # {"status": "healthy"}
```

### Authentication with Cookies
```python
async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
    # Login - cookie is automatically stored
    await client.post("/api/v1/auth/login", json={
        "username": "myuser",
        "password": "mypassword"
    })
    
    # Cookie is automatically sent with subsequent requests
    response = await client.get("/api/v1/farms")
    print(response.json())
```

### POST with JSON Body
```python
response = await client.post("/api/v1/farms", json={
    "name": "My Farm",
    "location": "Warehouse A",
    "status": "offline"
})
farm = response.json()
```

### PUT vs PATCH
```python
# PUT - Full update (all fields required)
await client.put(f"/api/v1/farms/{farm_id}", json={
    "name": "Updated Name",
    "location": "New Location",
    "total_power_kw": 500.0,
    "status": "online"
})

# PATCH - Partial update (only changed fields)
await client.patch(f"/api/v1/farms/{farm_id}", json={
    "status": "maintenance"
})
```

### Query Parameters
```python
# Pagination
response = await client.get("/api/v1/farms", params={
    "page": 1,
    "size": 20
})

# Filtering
response = await client.get("/api/v1/alerts", params={
    "severity": "critical",
    "is_acknowledged": False
})
```

### WebSocket Connection
```python
# Using httpx-ws
from httpx_ws import aconnect_ws

async with aconnect_ws(
    "ws://localhost:8000/ws/miners/{miner_id}/status",
    params={"token": jwt_token}
) as ws:
    message = await ws.receive_json()
    print(message)  # {"type": "metric_update", ...}
```

## Project Structure

```
httpx_allure/
├── docker-compose.yml      # PostgreSQL setup
├── requirements.txt        # Python dependencies
├── alembic.ini            # Migrations config
├── alembic/               # Migration scripts
├── api/
│   ├── config.py          # Settings
│   ├── main.py            # FastAPI app
│   ├── database.py        # SQLAlchemy setup
│   ├── dependencies.py    # Auth dependencies
│   ├── models/            # ORM models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── routers/           # API endpoints
│   └── tests/             # httpx test examples
│       ├── conftest.py    # Test fixtures
│       ├── test_auth.py
│       ├── test_farms.py
│       ├── test_miners.py
│       ├── test_metrics.py
│       ├── test_alerts.py
│       └── test_websocket.py
```

## Troubleshooting

### Database Connection Error
```bash
# Check if PostgreSQL is running
docker compose ps

# View logs
docker compose logs db

# Restart container
docker compose restart db

# If you see "password authentication failed" or "connection refused":
# 1. Ensure Docker PostgreSQL is running on port 5433
# 2. Check that no local PostgreSQL is running on port 5432
lsof -i :5432
lsof -i :5433
```

### Migration Issues
```bash
# Check current revision
alembic current

# View migration history
alembic history

# Reset database (caution: deletes all data)
alembic downgrade base
alembic upgrade head
```

### Port Already in Use
```bash
# If port 8000 is in use, change port in uvicorn command
uvicorn api.main:app --reload --port 8001

# If port 5433 (PostgreSQL) is in use, check what's using it:
lsof -i :5433
# Then either stop that service or change the port in docker-compose.yml
# and update DATABASE_URL in api/config.py accordingly
```

## License

This project is open source and available under the **MIT License**. You are free to use, modify, distribute, and adapt this project for your own learning, pet projects, or educational purposes.

See the [LICENSE](LICENSE) file for full details.

---

**Created with ❤️ for the API automation testing community**

# API_learning_project
