# Testing Guide

This document provides comprehensive guidance on running tests with the modular database configuration.

## Overview

The test suite supports modular database configuration, allowing you to run tests with different combinations of databases enabled or disabled. This is particularly useful when developing service-specific instances that only use a subset of the available databases.

## Database-Specific Test Markers

Tests are marked with database-specific markers to indicate their dependencies:

- `@pytest.mark.postgres` - Tests requiring PostgreSQL
- `@pytest.mark.mongodb` - Tests requiring MongoDB
- `@pytest.mark.redis` - Tests requiring Redis

Tests with these markers will be **automatically skipped** if the corresponding database is disabled in your environment configuration.

## Running Tests

### 1. All Databases Enabled (Default)

Run all tests with all databases enabled:

```bash
# Default configuration (all databases enabled)
pytest

# Or explicitly
ENABLE_POSTGRES=true ENABLE_MONGODB=true ENABLE_REDIS=true pytest
```

### 2. Service-Specific Test Configurations

#### Relational Database Service (PostgreSQL only)

```bash
# Set environment variables
export ENABLE_POSTGRES=true
export ENABLE_MONGODB=false
export ENABLE_REDIS=false

# Run tests
pytest

# Only PostgreSQL tests will run, others will be skipped
```

#### Document Database Service (MongoDB + Redis)

```bash
# Set environment variables
export ENABLE_POSTGRES=false
export ENABLE_MONGODB=true
export ENABLE_REDIS=true

# Run tests
pytest

# PostgreSQL tests will be skipped
```

#### Structured Data with Cache (PostgreSQL + Redis)

```bash
# Set environment variables
export ENABLE_POSTGRES=true
export ENABLE_MONGODB=false
export ENABLE_REDIS=true

# Run tests
pytest

# MongoDB tests will be skipped
```

### 3. Running Specific Database Tests

Run only tests for a specific database:

```bash
# Run only PostgreSQL tests
pytest -m postgres

# Run only MongoDB tests
pytest -m mongodb

# Run only Redis tests
pytest -m redis
```

### 4. Running Tests Without Database Dependencies

Run tests that don't require any databases:

```bash
# Run tests excluding all database markers
pytest -m "not postgres and not mongodb and not redis"
```

## Test Configuration Files

### Using .env File

Create a `.env.test` file for test-specific configuration:

```bash
# .env.test for Relational Database Service testing
ENABLE_POSTGRES=true
ENABLE_MONGODB=false
ENABLE_REDIS=false

# PostgreSQL connection (only needed if enabled)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=test_db
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password
```

Then run tests with:

```bash
# Load test environment
export $(cat .env.test | xargs)
pytest
```

### Using pytest.ini

The `pytest.ini` file already includes the database markers. No additional configuration needed.

## Understanding Test Skipping

When a test is skipped due to a disabled database, you'll see output like:

```
tests/unit/test_postgres.py::TestGetDb::test_get_db_yields_session SKIPPED
  [PostgreSQL is disabled (ENABLE_POSTGRES=false)]
```

This is expected behavior and indicates the test infrastructure is working correctly.

## Coverage Considerations

When running tests with disabled databases:

1. **Coverage will be lower**: Tests for disabled databases are skipped, so their code paths won't be covered
2. **This is expected**: Each service only needs coverage for the databases it uses
3. **Adjust coverage threshold**: You may need to adjust `--cov-fail-under` for service-specific testing

### Disabling Coverage Threshold for Service-Specific Testing

```bash
# Run tests without coverage threshold
pytest --cov-fail-under=0

# Or remove coverage reporting entirely
pytest --no-cov
```

## Continuous Integration (CI)

### Testing All Database Combinations

For comprehensive CI testing, test all relevant combinations:

```yaml
# Example GitHub Actions matrix
strategy:
  matrix:
    database-config:
      - name: "All Databases"
        ENABLE_POSTGRES: "true"
        ENABLE_MONGODB: "true"
        ENABLE_REDIS: "true"
      
      - name: "Relational Only"
        ENABLE_POSTGRES: "true"
        ENABLE_MONGODB: "false"
        ENABLE_REDIS: "false"
      
      - name: "Document with Cache"
        ENABLE_POSTGRES: "false"
        ENABLE_MONGODB: "true"
        ENABLE_REDIS: "true"
```

### Service-Specific CI

For service-specific repositories, only test the required databases:

```yaml
# Relational-only service CI - only PostgreSQL
env:
  ENABLE_POSTGRES: "true"
  ENABLE_MONGODB: "false"
  ENABLE_REDIS: "false"

steps:
  - name: Start PostgreSQL
    run: docker-compose up -d postgres
  
  - name: Run tests
    run: pytest
```

## Docker Compose for Testing

Use Docker Compose to run only required databases for testing:

```bash
# Relational-only service - only PostgreSQL
docker-compose up -d postgres
ENABLE_POSTGRES=true ENABLE_MONGODB=false ENABLE_REDIS=false pytest

# Document-based service - MongoDB + Redis
docker-compose up -d mongodb redis
ENABLE_POSTGRES=false ENABLE_MONGODB=true ENABLE_REDIS=true pytest
```

## Troubleshooting

### Tests Running When They Should Be Skipped

**Problem**: Tests with database markers are running even though the database is disabled.

**Solution**: Ensure the markers are properly applied:

```python
# Correct - module-level marker (applies to all tests in file)
import pytest
pytestmark = pytest.mark.postgres

# Also correct - class-level marker
@pytest.mark.postgres
class TestMyFeature:
    pass

# Also correct - function-level marker
@pytest.mark.postgres
def test_my_feature():
    pass
```

### Connection Errors Despite Disabled Database

**Problem**: Tests are failing with connection errors even though database is disabled.

**Solution**: Check if the test fixture is trying to connect before checking the flag:

```python
# Incorrect - connects before checking flag
@pytest.fixture
async def db_session(test_engine):
    # This will try to use test_engine even if disabled
    async with _test_session_factory() as session:
        yield session

# Correct - checks flag first
@pytest.fixture
async def db_session(test_engine, postgres_enabled):
    if not postgres_enabled:
        pytest.skip("PostgreSQL is disabled")
    
    async with _test_session_factory() as session:
        yield session
```

### Coverage Failing on Service-Specific Testing

**Problem**: Coverage fails when testing service-specific configurations.

**Solution**: Use `--cov-fail-under=0` or configure service-specific coverage thresholds:

```bash
# Option 1: Disable coverage threshold
pytest --cov-fail-under=0

# Option 2: Service-specific pytest.ini
[pytest]
addopts = --cov-fail-under=80  # Lower threshold for partial testing
```

## Best Practices

1. **Always mark database-dependent tests**: Use `@pytest.mark.postgres`, `@pytest.mark.mongodb`, or `@pytest.mark.redis`

2. **Use module-level markers for database modules**: If all tests in a file require the same database, use `pytestmark`:
   ```python
   pytestmark = pytest.mark.postgres
   ```

3. **Document database dependencies**: Add notes to test docstrings about database requirements

4. **Test with disabled databases locally**: Before committing, test that your service works with only required databases

5. **Keep test fixtures flexible**: Use the `*_enabled` fixtures to conditionally skip tests

## Example Test File Structure

```python
"""
Unit tests for user service.

Note: All tests in this file require PostgreSQL to be enabled (ENABLE_POSTGRES=true).
Tests will be automatically skipped if PostgreSQL is disabled.
"""
import pytest
from app.db.postgres import get_db
from app.models.user import User

# Mark all tests in this module as requiring PostgreSQL
pytestmark = pytest.mark.postgres


@pytest.mark.unit
class TestUserRepository:
    """Test user repository operations."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test user creation."""
        # This test will be skipped if ENABLE_POSTGRES=false
        user = User(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        assert user.id is not None
```

## Summary

The modular database configuration allows you to:

- ✅ Run tests with any combination of databases
- ✅ Automatically skip tests for disabled databases
- ✅ Test service-specific configurations locally and in CI
- ✅ Reduce test execution time for services that don't need all databases
- ✅ Ensure tests match production database configuration

For more information on the modular database configuration, see [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md).
