# FastAPI Microservice Skeleton

A production-ready, comprehensive FastAPI microservice boilerplate with modular database support. This template follows industry best practices for scalability, maintainability, and security.

## 🚀 Features

- **Modular Database Configuration**: Enable/disable PostgreSQL, MongoDB, and Redis per service
- **Modular Architecture**: Clean separation of concerns with organized modules
- **Multi-Database Support**: PostgreSQL, Redis, and MongoDB integration
- **Authentication**: JWT-based authentication with refresh tokens
- **Security**: Comprehensive security middleware and error handling
- **Logging**: Structured logging with JSON and text formats
- **Docker**: Multi-stage Dockerfile for production deployment
- **Testing**: Pytest configuration with coverage reporting
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Health Checks**: Database-aware health and readiness endpoints
- **CORS**: Configurable CORS middleware
- **Environment Management**: Pydantic settings with validation

## 🗄️ Modular Database Configuration

This boilerplate supports **selective database initialization** - each microservice can enable only the databases it needs, reducing resource overhead and improving startup time.

### Database Enable Flags

Control which databases are initialized by setting these environment variables:

```bash
ENABLE_POSTGRES=true   # Enable PostgreSQL (default: true)
ENABLE_MONGODB=true    # Enable MongoDB (default: true)
ENABLE_REDIS=true      # Enable Redis (default: true)
```

### Example Configuration Profiles

Choose the database combination that best fits your microservice needs:

| Profile | PostgreSQL | MongoDB | Redis | Use Case |
|---------|-----------|---------|-------|----------|
| **Relational + Cache** | ✓ | ✗ | ✓ | Services needing structured data with caching |
| **Relational Only** | ✓ | ✗ | ✗ | Services needing only structured data |
| **Document + Cache** | ✗ | ✓ | ✓ | Services needing flexible schemas with caching |
| **Cache Only** | ✗ | ✗ | ✓ | Services needing only caching/sessions |
| **All Databases** | ✓ | ✓ | ✓ | Services needing multiple storage paradigms |

### Example: Creating a Service with PostgreSQL Only

```bash
# 1. Copy the skeleton
cp -r fastapi-microservice-skeleton/ my-new-service
cd my-new-service

# 2. Configure for relational-only service
cat > .env << EOF
APP_NAME=my-new-service
ENABLE_POSTGRES=true
ENABLE_MONGODB=false
ENABLE_REDIS=false

POSTGRES_HOST=localhost
POSTGRES_DB=my_service_db
EOF

# 3. Start the service
python -m uvicorn app.main:app --reload
```

The service will only initialize PostgreSQL, skipping MongoDB and Redis entirely.

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose (for local development)
- At least one of the following (based on your service needs):
  - PostgreSQL 15+ (or use Docker)
  - Redis 7+ (or use Docker)
  - MongoDB 7+ (or use Docker)

## 🛠️ Installation

### Local Development

1. **Clone the repository**:
```bash
git clone <repository-url>
cd fastapi-microservice-skeleton
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start services with Docker Compose**:
```bash
docker-compose up -d
```

6. **Run the application**:
```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Or use the start script
chmod +x scripts/start.sh
./scripts/start.sh
```

### Docker Deployment

1. **Build the Docker image**:
```bash
docker build -t my-service:latest .
```

2. **Run the container**:
```bash
docker run -p 8080:8080 \
  -e POSTGRES_HOST=postgres \
  -e REDIS_HOST=redis \
  my-service:latest
```

## 📁 Project Structure

```
fastapi-microservice-skeleton/
├── app/
│   ├── api/
│   │   ├── deps.py              # Common dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py      # Health check endpoints
│   │           └── users.py       # User management endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Application configuration
│   │   ├── logging.py           # Logging configuration
│   │   └── security.py          # Security utilities (JWT, password hashing)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── postgres.py          # PostgreSQL connection
│   │   ├── redis.py             # Redis connection
│   │   └── mongodb.py           # MongoDB connection
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── database_check.py     # Database availability middleware
│   │   ├── error_handler.py     # Error handling middleware
│   │   └── logging.py          # Request/response logging
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # Base model with common fields
│   │   └── user.py             # User model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py           # Common schemas
│   │   └── user.py             # User schemas
│   ├── services/                 # Business logic services
│   └── main.py                 # Application entry point
├── tests/
│   ├── conftest.py              # Pytest configuration
│   ├── unit/                   # Unit tests
│   └── integration/             # Integration tests
├── scripts/
│   └── start.sh                 # Start script
├── k8s/                        # Kubernetes configurations
├── .env.example                 # Environment variables template
├── .gitignore                  # Git ignore rules
├── .dockerignore               # Docker ignore rules
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose configuration
├── pytest.ini                  # Pytest configuration
├── requirements.txt             # Production dependencies
├── requirements-dev.txt        # Development dependencies
└── README.md                   # This file
```

## 🔧 Configuration

All configuration is managed through environment variables. Copy [`.env.example`](.env.example) to `.env` and configure as needed.

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|----------|
| `APP_NAME` | Application name | `microservice-api` |
| `APP_ENV` | Environment (development/staging/production) | `development` |
| `DEBUG` | Debug mode | `false` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `MONGODB_HOST` | MongoDB host | `localhost` |
| `MONGODB_PORT` | MongoDB port | `27017` |
| `JWT_SECRET_KEY` | JWT secret key | *(required)* |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Integration Tests Only

```bash
pytest tests/integration/
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/unit/test_health.py -v
```

## 📊 API Documentation

Once the application is running, access the API documentation:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

### Available Endpoints

#### Health Checks
- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check endpoint

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/forgot-password` - Initiate password reset
- `POST /api/v1/auth/reset-password` - Complete password reset

#### Users
- `GET /api/v1/users/me` - Get current user info
- `PUT /api/v1/users/me` - Update current user

## 🔐 Security

This skeleton includes several security features:

- **JWT Authentication**: RS256 algorithm with access and refresh tokens
- **Password Hashing**: Bcrypt with configurable rounds
- **CORS**: Configurable CORS middleware
- **Rate Limiting**: Ready for rate limiting integration
- **Input Validation**: Pydantic schemas for request validation
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **Error Handling**: Comprehensive exception handling without exposing sensitive data

## 🚢 Deployment

### Kubernetes

See the `k8s/` directory for Kubernetes deployment manifests.

### Docker

```bash
# Build image
docker build -t registry.example.com/my-service:v1.0.0 .

# Push to registry
docker push registry.example.com/my-service:v1.0.0
```

### Production Server

```bash
# Using gunicorn
gunicorn app.main:app \
  --bind 0.0.0.0:8080 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120
```

## 📝 Development Guidelines

### Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run formatters and linters:
```bash
black app/
isort app/
flake8 app/
mypy app/
```

### Commit Messages

Follow conventional commits:
- `feat: add user registration`
- `fix: resolve login bug`
- `docs: update README`
- `refactor: improve database connection`

### Branching

- `main` - Production code
- `develop` - Development code
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Hotfix branches

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## 📄 License

This project is proprietary software.

## 📞 Support

For support, contact your development team or project maintainers.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [Uvicorn](https://www.uvicorn.org/)
- [Gunicorn](https://gunicorn.org/)
