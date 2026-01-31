"""
Unit tests for configuration module.
Tests all Settings properties and validators.
"""
import os
import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettingsDefaults:
    """Test default settings values."""

    def test_default_app_settings(self):
        """Test default application settings."""
        settings = Settings()
        assert settings.APP_NAME == "microservice-api"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.APP_ENV == "development"
        assert settings.DEBUG is False
        assert settings.API_V1_PREFIX == "/api/v1"

    def test_default_server_settings(self):
        """Test default server settings."""
        settings = Settings()
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8080
        assert settings.WORKERS == 4

    def test_default_postgres_settings(self):
        """Test default PostgreSQL settings."""
        settings = Settings()
        assert settings.POSTGRES_HOST == "localhost"
        assert settings.POSTGRES_PORT == 5432
        assert settings.POSTGRES_DB == "microservice_db"
        assert settings.POSTGRES_USER == "postgres"
        assert settings.POSTGRES_PASSWORD == "postgres"
        assert settings.POSTGRES_POOL_SIZE == 20
        assert settings.POSTGRES_MAX_OVERFLOW == 10
        assert settings.POSTGRES_POOL_TIMEOUT == 30

    def test_default_mongodb_settings(self):
        """Test default MongoDB settings."""
        settings = Settings()
        assert settings.MONGODB_HOST == "localhost"
        assert settings.MONGODB_PORT == 27017
        assert settings.MONGODB_DB == "microservice_db"
        assert settings.MONGODB_USER is None
        assert settings.MONGODB_PASSWORD is None

    def test_default_redis_settings(self):
        """Test default Redis settings."""
        settings = Settings()
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379
        assert settings.REDIS_DB == 0
        assert settings.REDIS_PASSWORD is None
        assert settings.REDIS_MAX_CONNECTIONS == 50
        assert settings.REDIS_TTL == 3600

    def test_default_jwt_settings(self):
        """Test default JWT settings."""
        settings = Settings()
        assert settings.JWT_SECRET_KEY == "your-super-secret-jwt-key"
        assert settings.JWT_ALGORITHM == "RS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_default_cors_settings(self):
        """Test default CORS settings."""
        settings = Settings()
        assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://localhost:8080"]
        assert settings.CORS_ALLOW_CREDENTIALS is True
        assert settings.CORS_ALLOW_METHODS == ["*"]
        assert settings.CORS_ALLOW_HEADERS == ["*"]

    def test_default_security_settings(self):
        """Test default security settings."""
        settings = Settings()
        assert settings.SECURITY_BCRYPT_ROUNDS == 12
        assert settings.SECURITY_OTP_LENGTH == 6
        assert settings.SECURITY_OTP_EXPIRE_MINUTES == 5

    def test_default_logging_settings(self):
        """Test default logging settings."""
        settings = Settings()
        assert settings.LOG_LEVEL == "INFO"
        assert settings.LOG_FORMAT == "json"
        assert settings.LOG_FILE_PATH == "./logs/app.log"

    def test_default_feature_flags(self):
        """Test default feature flags."""
        settings = Settings()
        assert settings.FEATURE_REGISTRATION_ENABLED is True
        assert settings.FEATURE_SOCIAL_LOGIN_ENABLED is True
        assert settings.FEATURE_2FA_ENABLED is True
        assert settings.FEATURE_API_DOCS_ENABLED is True
        assert settings.FEATURE_METRICS_ENABLED is True

    def test_default_external_service_urls(self):
        """Test default external service URLs."""
        settings = Settings()
        assert settings.SERVICE_A_URL == "http://service-a:8080"
        assert settings.SERVICE_B_URL == "http://service-b:8080"
        assert settings.SERVICE_C_URL == "http://service-c:8080"

    def test_default_cdn_settings(self):
        """Test default CDN settings."""
        settings = Settings()
        assert settings.CDN_BASE_URL == "https://cdn.example.com"
        assert settings.CDN_CACHE_TTL == 300

    def test_default_drm_settings(self):
        """Test default DRM settings."""
        settings = Settings()
        assert settings.DRM_WIDEVINE_URL == "https://drm.example.com/widevine"
        assert settings.DRM_FAIRPLAY_URL == "https://drm.example.com/fairplay"
        assert settings.DRM_PLAYREADY_URL == "https://drm.example.com/playready"

    def test_default_email_settings(self):
        """Test default email settings."""
        settings = Settings()
        assert settings.SENDGRID_API_KEY is None
        assert settings.SENDGRID_FROM_EMAIL == "noreply@example.com"
        assert settings.SENDGRID_FROM_NAME == "My Service"

    def test_default_sms_settings(self):
        """Test default SMS settings."""
        settings = Settings()
        assert settings.TWILIO_ACCOUNT_SID is None
        assert settings.TWILIO_AUTH_TOKEN is None
        assert settings.TWILIO_PHONE_NUMBER is None

    def test_default_monitoring_settings(self):
        """Test default monitoring settings."""
        settings = Settings()
        assert settings.PROMETHEUS_ENABLED is True
        assert settings.PROMETHEUS_PORT == 9090
        assert settings.TRACING_ENABLED is False
        assert settings.JAEGER_AGENT_HOST == "localhost"
        assert settings.JAEGER_AGENT_PORT == 6831

    def test_default_rate_limiting_settings(self):
        """Test default rate limiting settings."""
        settings = Settings()
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_REQUESTS_PER_MINUTE == 100
        assert settings.RATE_LIMIT_REQUESTS_PER_HOUR == 1000

    def test_default_health_check_settings(self):
        """Test default health check settings."""
        settings = Settings()
        assert settings.HEALTH_CHECK_INTERVAL == 30
        assert settings.HEALTH_CHECK_TIMEOUT == 5


class TestPostgresURL:
    """Test PostgreSQL URL property."""

    def test_postgres_url_property(self):
        """Test POSTGRES_URL property generation."""
        settings = Settings()
        url = settings.POSTGRES_URL
        assert url == "postgresql+asyncpg://postgres:postgres@localhost:5432/microservice_db"

    def test_postgres_url_with_special_characters(self):
        """Test POSTGRES_URL with special characters in password."""
        os.environ["POSTGRES_PASSWORD"] = "p@ss:word123"
        settings = Settings()
        url = settings.POSTGRES_URL
        assert "p@ss:word123" in url

    def test_postgres_url_sync_property(self):
        """Test POSTGRES_URL_SYNC property generation."""
        settings = Settings()
        url = settings.POSTGRES_URL_SYNC
        assert url == "postgresql://postgres:postgres@localhost:5432/microservice_db"


class TestMongoDBURL:
    """Test MongoDB URL property."""

    def test_mongodb_url_without_credentials(self, monkeypatch):
        """Test MONGODB_URL without credentials."""
        # Set MongoDB credentials to None to test path without credentials
        monkeypatch.setenv("MONGODB_USER", "")
        monkeypatch.setenv("MONGODB_PASSWORD", "")
        
        settings = Settings()
        url = settings.MONGODB_URL
        assert url == "mongodb://localhost:27017/microservice_db"

    def test_mongodb_url_with_credentials(self):
        """Test MONGODB_URL with credentials."""
        os.environ["MONGODB_USER"] = "mongo_user"
        os.environ["MONGODB_PASSWORD"] = "mongo_pass"
        settings = Settings()
        url = settings.MONGODB_URL
        assert url == "mongodb://mongo_user:mongo_pass@localhost:27017/microservice_db"

    def test_mongodb_url_default(self):
        """Test MONGODB_URL default (no credentials)."""
        settings = Settings()
        url = settings.MONGODB_URL
        assert url == "mongodb://localhost:27017/microservice_db"


class TestRedisURL:
    """Test Redis URL property."""

    def test_redis_url_without_password(self):
        """Test REDIS_URL without password."""
        settings = Settings()
        url = settings.REDIS_URL
        assert url == "redis://localhost:6379/0"

    def test_redis_url_with_password(self):
        """Test REDIS_URL with password."""
        os.environ["REDIS_PASSWORD"] = "redis_pass"
        settings = Settings()
        url = settings.REDIS_URL
        assert url == "redis://:redis_pass@localhost:6379/0"


class TestLogLevelValidator:
    """Test log level validator."""

    def test_log_level_valid(self):
        """Test valid log levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            os.environ["LOG_LEVEL"] = level
            settings = Settings()
            assert settings.LOG_LEVEL == level

    def test_log_level_invalid(self):
        """Test invalid log level raises ValidationError."""
        os.environ["LOG_LEVEL"] = "INVALID"
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "LOG_LEVEL must be one of" in str(exc_info.value)


class TestKafkaSettings:
    """Test Kafka settings."""

    def test_kafka_topics_default(self):
        """Test default Kafka topics."""
        settings = Settings()
        assert settings.KAFKA_BROKERS == "localhost:9092"
        assert settings.KAFKA_CONSUMER_GROUP == "microservice-group"
        assert settings.KAFKA_TOPICS == ["events", "notifications", "tasks"]


class TestEnvironmentVariables:
    """Test environment variable loading."""

    def test_settings_from_environment(self):
        """Test settings loaded from environment variables."""
        os.environ["APP_NAME"] = "test-service"
        os.environ["DEBUG"] = "true"
        settings = Settings()
        assert settings.APP_NAME == "test-service"
        assert settings.DEBUG is True

    def test_case_sensitive_environment_variables(self):
        """Test case sensitivity of environment variables."""
        os.environ["APP_NAME"] = "test-service"
        settings = Settings()
        assert settings.APP_NAME == "test-service"
        # lowercase should not work
        os.environ["app_name"] = "lowercase-service"
        settings2 = Settings()
        assert settings2.APP_NAME != "lowercase-service"


class TestGlobalSettingsInstance:
    """Test global settings instance."""

    def test_global_settings_instance_exists(self):
        """Test global settings instance is properly created."""
        from app.core.config import settings
        
        # Verify global settings instance exists and has correct values
        assert settings is not None
        assert settings.APP_NAME == "microservice-api"
        assert settings.APP_VERSION == "1.0.0"
