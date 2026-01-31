# Developer Guide - FastAPI Microservice Skeleton

This guide explains how developers can use the FastAPI microservice skeleton to build microservices with modular database configuration.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure Overview](#project-structure-overview)
3. [Creating a New Service](#creating-a-new-service)
4. [Common Patterns](#common-patterns)
5. [Best Practices](#best-practices)
6. [Testing Guidelines](#testing-guidelines)
7. [Deployment](#deployment)

---

## Getting Started

### Prerequisites

Before starting, ensure you have:
- Python 3.11+ installed
- Docker and Docker Compose installed
- Access to PostgreSQL, Redis, MongoDB (or use Docker Compose)
- Basic understanding of FastAPI, SQLAlchemy, and Pydantic

### Initial Setup

```bash
# 1. Clone or copy the skeleton
cp -r fastapi-microservice-skeleton/ my-new-service

# 2. Navigate to the new service
cd my-new-service

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env with your service-specific settings
```

### Start Development Environment

```bash
# Start all dependencies with Docker Compose
docker-compose up -d

# Start the FastAPI application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Or use the start script
chmod +x scripts/start.sh
./scripts/start.sh
```

Access the API documentation at: http://localhost:8080/docs

---

## Configuring Database Connections

### Overview

The FastAPI skeleton supports **modular database configuration**, allowing each microservice to enable only the databases it needs. This reduces resource usage, speeds up startup time, and simplifies deployment.

### Database Enable Flags

Three environment variables control database initialization:

- `ENABLE_POSTGRES` - Enable PostgreSQL (default: `true`)
- `ENABLE_MONGODB` - Enable MongoDB (default: `true`)
- `ENABLE_REDIS` - Enable Redis cache (default: `true`)

### Database Selection Guide

Choose the database combination that best fits your microservice requirements:

| Database Combination | Use Case | When to Use |
|---------------------|----------|-------------|
| **PostgreSQL Only** | Structured data with ACID compliance | Financial transactions, user accounts, inventory |
| **MongoDB Only** | Flexible schemas, document storage | Content management, product catalogs, logs |
| **Redis Only** | High-speed caching, session storage | Session management, rate limiting, pub/sub |
| **PostgreSQL + Redis** | Structured data with caching | Core services needing relational data with cache |
| **MongoDB + Redis** | Document storage with caching | Document-heavy services with caching needs |
| **All Three** | Complex requirements | Multi-paradigm data needs |

### Configuration Examples

#### Example 1: Relational Database Only (PostgreSQL)

```bash
# .env for relational-only service
APP_NAME=my-transaction-service

# Enable only PostgreSQL
ENABLE_POSTGRES=true
ENABLE_MONGODB=false
ENABLE_REDIS=false

# PostgreSQL configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=my_service_db
POSTGRES_USER=db_user
POSTGRES_PASSWORD=secure_password
```

**Result:** Service initializes PostgreSQL only. MongoDB and Redis connections are skipped.

#### Example 2: Document Database with Cache (MongoDB + Redis)

```bash
# .env for document-based service
APP_NAME=my-document-service

# Enable MongoDB and Redis
ENABLE_POSTGRES=false
ENABLE_MONGODB=true
ENABLE_REDIS=true

# MongoDB configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=my_service_db

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Result:** Service initializes MongoDB and Redis. PostgreSQL is skipped.

#### Example 3: Cache Only (Redis)

```bash
# .env for session-only service
APP_NAME=my-session-service

# Enable only Redis
ENABLE_POSTGRES=false
ENABLE_MONGODB=false
ENABLE_REDIS=true

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**Result:** Service initializes Redis only for session management or caching.

### How It Works

1. **Startup Check**: During application startup, the `lifespan()` function checks each database enable flag
2. **Conditional Initialization**: Only enabled databases are initialized
3. **Graceful Skipping**: Disabled databases log an info message and skip initialization
4. **Health Checks**: The `/health` endpoint reports status for enabled databases only
5. **Dependency Protection**: If code attempts to use a disabled database, a clear error is raised

### Startup Log Example

```
INFO: Starting application app_name=my-service version=1.0.0 environment=production
INFO: Database configuration enabled_databases=['PostgreSQL'] postgres=True mongodb=False redis=False
INFO: Initializing PostgreSQL connection...
INFO: PostgreSQL connection established successfully
INFO: MongoDB initialization skipped (disabled)
INFO: Redis initialization skipped (disabled)
INFO: Application started successfully enabled_databases=['PostgreSQL']
```

### Error Handling

If your code attempts to use a disabled database:

```python
from fastapi import Depends
from app.db import get_redis

@app.get("/cache")
async def get_cache(redis = Depends(get_redis)):
    # If ENABLE_REDIS=false, this raises:
    # RuntimeError: Redis is not enabled. Set ENABLE_REDIS=true in your configuration...
    pass
```

**Best Practice:** Only use database dependencies that are enabled for your service type.

### Performance Benefits

- **Faster Startup**: Skip unused database connections
- **Lower Resource Usage**: No connection pools for unused databases
- **Reduced Dependencies**: Don't need to run unused databases in development
- **Cleaner Logs**: Only see logs for databases your service uses

### Troubleshooting

**Problem:** Service fails to start with database connection error

**Solution:** Check that enabled databases are actually running and accessible

```bash
# Check which databases are enabled
grep ENABLE_ .env

# For PostgreSQL
psql -h localhost -U postgres -c "SELECT 1"

# For MongoDB
mongosh --host localhost --eval "db.adminCommand('ping')"

# For Redis
redis-cli ping
```

**Problem:** Code raises "database is not enabled" error

**Solution:** Either enable the required database or remove the code that uses it

```bash
# Enable the database
echo "ENABLE_REDIS=true" >> .env

# OR remove the endpoint/feature that requires it
```

---

## Project Structure Overview

```
app/
├── api/              # API layer - add your endpoints here
│   ├── deps.py      # Common dependencies (auth, cache, etc.)
│   └── v1/
│       └── endpoints/  # Add your endpoint modules
│           ├── health.py      # Keep health checks
│           └── users.py       # Example: remove or modify
│
├── core/             # Core utilities - use as-is
│   ├── config.py     # Add your service-specific settings
│   ├── logging.py    # Use as-is for structured logging
│   └── security.py   # Use as-is for JWT, password hashing
│
├── db/               # Database layer - use as-is
│   ├── postgres.py    # Use get_db() dependency
│   ├── redis.py       # Use get_cache_service() dependency
│   └── mongodb.py     # Use MongoRepository for document operations
│
├── models/           # SQLAlchemy models - add your domain models
│   ├── base.py      # Use BaseModel as base class
│   └── user.py       # Example: remove or modify
│
├── schemas/          # Pydantic schemas - add your request/response schemas
│   ├── common.py     # Use for standard responses
│   └── user.py       # Example: remove or modify
│
├── middleware/       # Custom middleware - use as-is
│   ├── error_handler.py  # Use existing exception classes
│   └── logging.py      # Use as-is for request logging
│
├── services/         # Business logic - add your service logic here
│   └── __init__.py  # Create service classes
│
└── main.py           # Application entry point - update as needed
```

---

## Creating a New Service

### Step 1: Update Configuration

Edit [`app/core/config.py`](app/core/config.py) to add service-specific settings:

```python
class Settings(BaseSettings):
    # Keep existing settings...
    
    # Add your service-specific settings
    SERVICE_NAME: str = Field(default="my-service", description="Service name")
    SERVICE_ENABLED: bool = Field(default=True, description="Enable this service")
    
    # Example: Product service settings
    PRODUCT_CACHE_TTL: int = Field(default=3600, description="Product cache TTL")
    MAX_ITEMS_PER_PAGE: int = Field(default=50, description="Max items per page")
```

### Step 2: Create Database Models

Create models in [`app/models/`](app/models/):

```python
# app/models/product.py
from sqlalchemy import Boolean, DateTime, Numeric, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Product(BaseModel):
    """Product model example."""
    
    __tablename__ = "products"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

### Step 3: Create Pydantic Schemas

Create schemas in [`app/schemas/`](app/schemas/):

```python
# app/schemas/product.py
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., gt=0)
    quantity: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: UUID
    name: str
    description: Optional[str]
    price: float
    quantity: int
    is_active: bool
```

### Step 4: Create API Endpoints

Create endpoints in [`app/api/v1/endpoints/`](app/api/v1/endpoints/):

```python
# app/api/v1/endpoints/products.py
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.logging import get_logger
from app.middleware.error_handler import NotFoundException
from app.models.product import Product
from app.schemas.common import SuccessResponse
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=SuccessResponse[List[ProductResponse]],
    tags=["Products"],
)
async def list_products(
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[List[ProductResponse]]:
    """List all products."""
    result = await db.execute(select(Product).where(Product.is_active == True))
    products = result.scalars().all()
    
    return SuccessResponse(
        message="Products retrieved successfully",
        data=[ProductResponse.model_validate(p) for p in products],
    )


@router.post(
    "/",
    response_model=SuccessResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    tags=["Products"],
)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[ProductResponse]:
    """Create a new product."""
    product = Product(**product_in.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    logger.info("Product created", product_id=str(product.id))
    
    return SuccessResponse(
        message="Product created successfully",
        data=ProductResponse.model_validate(product),
    )
```

### Step 5: Register the Router

Update [`app/api/v1/__init__.py`](app/api/v1/__init__.py):

```python
from fastapi import APIRouter

from app.api.v1.endpoints import health_router, users_router, products_router

api_router = APIRouter()

# Include existing routers
api_router.include_router(health_router)
api_router.include_router(users_router, tags=["Users"])

# Add your new router
api_router.include_router(products_router, prefix="/products", tags=["Products"])
```

### Step 6: Create Business Logic Services

Create service classes in [`app/services/`](app/services/):

```python
# app/services/product_service.py
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.middleware.error_handler import NotFoundException
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

logger = get_logger(__name__)


class ProductService:
    """Business logic for product management."""
    
    async def get_product(
        self,
        product_id: UUID,
        db: AsyncSession,
    ) -> Product:
        """Get a product by ID."""
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            raise NotFoundException("Product not found")
        
        return product
    
    async def update_product(
        self,
        product_id: UUID,
        update_data: ProductUpdate,
        db: AsyncSession,
    ) -> Product:
        """Update a product."""
        product = await self.get_product(product_id, db)
        
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        
        await db.commit()
        await db.refresh(product)
        
        logger.info("Product updated", product_id=str(product_id))
        
        return product
```

### Step 7: Add Tests

Create tests in [`tests/unit/`](tests/unit/):

```python
# tests/unit/test_products.py
import pytest
from httpx import AsyncClient

from app.schemas.product import ProductCreate, ProductResponse


@pytest.mark.unit
class TestProductEndpoints:
    """Test product endpoints."""
    
    async def test_list_products(self, client: AsyncClient):
        """Test listing products."""
        response = await client.get("/api/v1/products")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    async def test_create_product(self, client: AsyncClient, auth_headers):
        """Test creating a product."""
        # Create product
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "price": 99.99,
            "quantity": 10,
        }
        
        response = await client.post(
            "/api/v1/products",
            json=product_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["name"] == "Test Product"
```

---

## Common Patterns

### Repository Pattern

Use the [`MongoRepository`](app/db/mongodb.py) base class for MongoDB operations:

```python
from app.db.mongodb import MongoRepository


class DocumentRepository(MongoRepository):
    """Repository for document operations."""
    
    def __init__(self):
        super().__init__("documents")
    
    async def find_by_id(self, document_id: str):
        """Find document by ID."""
        return await self.find_one({"_id": document_id})
    
    async def search_by_title(self, query: str):
        """Search documents by title."""
        return await self.find_many(
            {"title": {"$regex": query, "$options": "i"}},
            limit=20
        )
```

### Cache Pattern

Use the [`CacheService`](app/db/redis.py) for caching:

```python
from app.api.deps import get_cache_service


@router.get("/plans")
async def list_plans(
    cache: CacheService = Depends(get_cache_service),
):
    # Try cache first
    cached = await cache.get("plans:all")
    if cached:
        return json.loads(cached)
    
    # Query database
    plans = await get_plans_from_db()
    
    # Cache result
    await cache.set("plans:all", json.dumps(plans), ttl=3600)
    
    return plans
```

### Event Publishing Pattern

Use Kafka for event-driven communication:

```python
from aiokafka import AIOKafkaProducer

# In app/core/config.py
KAFKA_BROKERS: str = Field(default="localhost:9092")
KAFKA_TOPIC_PREFIX: str = Field(default="microservice")

# In your service
async def publish_event(event_type: str, event_data: dict):
    """Publish event to Kafka."""
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BROKERS.split(",")
    )
    
    topic = f"{settings.KAFKA_TOPIC_PREFIX}.{event_type}"
    
    await producer.send_and_wait(
        topic,
        value=json.dumps(event_data).encode("utf-8"),
    )
    
    await producer.stop()
```

### Error Handling Pattern

Use custom exceptions from [`app/middleware/error_handler.py`](app/middleware/error_handler.py):

```python
from app.middleware.error_handler import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)


async def create_item(name: str, category_id: UUID):
    # Check if exists
    existing = await get_item_by_name(name)
    if existing:
        raise ConflictException("Item with this name already exists")
    
    # Check if category exists
    category = await get_category(category_id)
    if not category:
        raise NotFoundException("Category not found")
    
    # Create item
    return await create_item(name, category_id)
```

---

## Best Practices

### Code Organization

1. **Separation of Concerns**
   - Keep models in [`app/models/`](app/models/)
   - Keep schemas in [`app/schemas/`](app/schemas/)
   - Keep endpoints in [`app/api/v1/endpoints/`](app/api/v1/endpoints/)
   - Keep business logic in [`app/services/`](app/services/)

2. **Dependency Injection**
   - Use FastAPI's `Depends()` for all dependencies
   - Create reusable dependencies in [`app/api/deps.py`](app/api/deps.py)
   - Use type hints for all dependencies

3. **Configuration Management**
   - Add all settings to [`app/core/config.py`](app/core/config.py)
   - Use Pydantic for validation
   - Provide sensible defaults
   - Document all settings in `.env.example`

### Database Best Practices

1. **Async Operations**
   - Always use async database operations
   - Use `await db.commit()` and `await db.refresh()`
   - Use connection pooling (configured in [`app/db/postgres.py`](app/db/postgres.py))

2. **Query Optimization**
   - Use SQLAlchemy's `select()` for queries
   - Use `scalar_one_or_none()` for single results
   - Use `scalars().all()` for multiple results
   - Implement pagination for large datasets

3. **Transaction Management**
   - Use database sessions with automatic rollback
   - Commit only after successful operations
   - Handle exceptions with rollback

### API Design Best Practices

1. **RESTful Endpoints**
   - Use appropriate HTTP methods (GET, POST, PUT, DELETE)
   - Use correct status codes (200, 201, 404, 409, 422)
   - Implement pagination for list endpoints
   - Use query parameters for filtering and sorting

2. **Response Format**
   - Use [`SuccessResponse`](app/schemas/common.py) for successful responses
   - Use [`ErrorResponse`](app/schemas/common.py) for errors
   - Include consistent message format
   - Add pagination metadata for list responses

3. **Documentation**
   - Add docstrings to all endpoints
   - Use Pydantic Field descriptions
   - Add OpenAPI tags for grouping
   - Include examples in schemas

### Security Best Practices

1. **Authentication**
   - Always validate JWT tokens
   - Use `get_current_user` for authenticated endpoints
   - Use `get_current_user_optional` for optional auth
   - Implement role-based access control

2. **Input Validation**
   - Use Pydantic schemas for all inputs
   - Validate email, phone, UUID formats
   - Implement password strength requirements
   - Sanitize user inputs

3. **Data Protection**
   - Never log sensitive data (passwords, tokens)
   - Use environment variables for secrets
   - Hash tokens before storage
   - Implement rate limiting

---

## Testing Guidelines

### Unit Tests

Create unit tests in [`tests/unit/`](tests/unit/):

```python
# tests/unit/test_product_service.py
import pytest

@pytest.mark.unit
class TestProductService:
    """Test product service business logic."""
    
    async def test_calculate_discount_price(self):
        """Test discount price calculation."""
        from app.services.product_service import ProductService
        
        service = ProductService()
        
        # Test percentage discount
        discounted = await service.calculate_discount_price(
            original_price=100.00,
            discount_percent=20,
        )
        
        assert discounted == 80.00
```

### Integration Tests

Create integration tests in [`tests/integration/`](tests/integration/):

```python
# tests/integration/test_product_flow.py
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
class TestProductFlow:
    """Test product flow end-to-end."""
    
    async def test_full_product_flow(self, client: AsyncClient):
        """Test complete product creation flow."""
        
        # 1. Register user
        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123",
            "first_name": "Test",
            "last_name": "User",
        }
        register_response = await client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        assert login_response.status_code == 200
        
        token = login_response.json()["data"]["access_token"]
        
        # 3. Create product
        product_data = {
            "name": "Integration Test Product",
            "description": "A test product",
            "price": 49.99,
            "quantity": 5,
        }
        product_response = await client.post(
            "/api/v1/products",
            json=product_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert product_response.status_code == 201
        
        # 4. Get product
        product_id = product_response.json()["data"]["id"]
        get_response = await client.get(
            f"/api/v1/products/{product_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
```

### Test Coverage

Run tests with coverage:

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

Target: 80%+ code coverage

---

## Deployment

### Local Development

Use Docker Compose for local development:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Production Deployment

#### Docker

```bash
# Build image
docker build -t registry.example.com/my-service:v1.0.0 .

# Push to registry
docker push registry.example.com/my-service:v1.0.0

# Run container
docker run -d \
  --name my-service \
  -p 8080:8080 \
  -e POSTGRES_HOST=postgres-service \
  -e REDIS_HOST=redis-service \
  registry.example.com/my-service:v1.0.0
```

#### Kubernetes

```bash
# Apply deployment
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=my-service

# View logs
kubectl logs -f app=my-service

# Scale up
kubectl scale deployment/my-service --replicas=5

# Update deployment
kubectl set image deployment/my-service \
  my-service=registry.example.com/my-service:v1.1.0
```

### Environment Variables

Update `.env` for production:

```bash
# Production settings
APP_ENV=production
DEBUG=false
WORKERS=4

# Database (use managed services)
POSTGRES_HOST=postgres-service.production.svc.cluster.local
REDIS_HOST=redis-service.production.svc.cluster.local

# Security (use secrets management)
JWT_SECRET_KEY=<from-secret-manager>
POSTGRES_PASSWORD=<from-secret-manager>
```

---

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check if PostgreSQL is running
   - Verify connection string in `.env`
   - Check network connectivity

2. **Import Errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`
   - Check Python version (3.11+)

3. **Port Already in Use**
   - Kill process using port 8080
   - Use different port in `.env`
   - Check for other running services

4. **Docker Build Failures**
   - Clear Docker cache: `docker system prune -a`
   - Check Dockerfile syntax
   - Verify base image exists

### Debugging

Enable debug mode:

```bash
# In .env
DEBUG=true

# Restart application
python -m uvicorn app.main:app --reload
```

View logs:

```bash
# Docker logs
docker-compose logs -f api

# Application logs
tail -f logs/app.log
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

---

## Conclusion

This FastAPI microservice skeleton provides a solid foundation for building production-ready microservices. By following the patterns and best practices outlined in this guide, developers can efficiently create scalable, maintainable microservices with modular database configuration.

The modular design allows for easy extension and customization while maintaining consistency across all services. Start with the provided examples and adapt them to your specific service requirements.
