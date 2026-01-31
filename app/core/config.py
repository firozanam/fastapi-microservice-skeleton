"""
Core configuration module for the application.
Handles all environment variables and application settings.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Application Settings
    APP_NAME: str = Field(default="microservice-api", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    APP_ENV: str = Field(
        default="development",
        description="Environment (development/staging/production)",
    )
    DEBUG: bool = Field(default=False, description="Debug mode")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")

    # Server Settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8080, description="Server port")
    WORKERS: int = Field(default=4, description="Number of worker processes")

    # Database - PostgreSQL
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(
        default="microservice_db", description="PostgreSQL database name"
    )
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(
        default="postgres", description="PostgreSQL password"
    )
    POSTGRES_POOL_SIZE: int = Field(
        default=20, description="PostgreSQL connection pool size"
    )
    POSTGRES_MAX_OVERFLOW: int = Field(
        default=10, description="PostgreSQL max overflow connections"
    )
    POSTGRES_POOL_TIMEOUT: int = Field(
        default=30, description="PostgreSQL pool timeout"
    )

    @property
    def POSTGRES_URL(self) -> str:
        """Generate PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def POSTGRES_URL_SYNC(self) -> str:
        """Generate synchronous PostgreSQL connection URL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Database - MongoDB
    MONGODB_HOST: str = Field(default="localhost", description="MongoDB host")
    MONGODB_PORT: int = Field(default=27017, description="MongoDB port")
    MONGODB_DB: str = Field(
        default="microservice_db", description="MongoDB database name"
    )
    MONGODB_USER: Optional[str] = Field(default=None, description="MongoDB user")
    MONGODB_PASSWORD: Optional[str] = Field(
        default=None, description="MongoDB password"
    )

    @property
    def MONGODB_URL(self) -> str:
        """Generate MongoDB connection URL."""
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            return (
                f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}"
                f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}"
            )
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}"

    # Cache - Redis
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Redis max connections")
    REDIS_TTL: int = Field(default=3600, description="Redis default TTL in seconds")

    @property
    def REDIS_URL(self) -> str:
        """Generate Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Message Queue - Kafka
    KAFKA_BROKERS: str = Field(default="localhost:9092", description="Kafka brokers")
    KAFKA_CONSUMER_GROUP: str = Field(
        default="microservice-group", description="Kafka consumer group"
    )
    KAFKA_TOPICS: List[str] = Field(
        default=["events", "notifications", "tasks"],
        description="Kafka topics",
    )

    # JWT Settings
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-jwt-key", description="JWT secret key"
    )
    JWT_ALGORITHM: str = Field(default="RS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, description="JWT access token expiry"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="JWT refresh token expiry"
    )

    # CORS Settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True, description="CORS allow credentials"
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["*"], description="CORS allow methods"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["*"], description="CORS allow headers"
    )

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=100, description="Rate limit per minute"
    )
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(
        default=1000, description="Rate limit per hour"
    )

    # Security
    SECURITY_BCRYPT_ROUNDS: int = Field(default=12, description="BCrypt rounds")
    SECURITY_OTP_LENGTH: int = Field(default=6, description="OTP length")
    SECURITY_OTP_EXPIRE_MINUTES: int = Field(
        default=5, description="OTP expiry minutes"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json/text)")
    LOG_FILE_PATH: str = Field(default="./logs/app.log", description="Log file path")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    # Monitoring & Observability
    PROMETHEUS_ENABLED: bool = Field(
        default=True, description="Enable Prometheus metrics"
    )
    PROMETHEUS_PORT: int = Field(default=9090, description="Prometheus metrics port")
    TRACING_ENABLED: bool = Field(
        default=False, description="Enable distributed tracing"
    )
    JAEGER_AGENT_HOST: str = Field(default="localhost", description="Jaeger agent host")
    JAEGER_AGENT_PORT: int = Field(default=6831, description="Jaeger agent port")

    # External Services (Example placeholders - replace with your actual service URLs)
    # These are examples showing how to configure inter-service communication
    SERVICE_A_URL: str = Field(
        default="http://service-a:8080", description="External service A URL"
    )
    SERVICE_B_URL: str = Field(
        default="http://service-b:8080",
        description="External service B URL",
    )
    SERVICE_C_URL: str = Field(
        default="http://service-c:8080", description="External service C URL"
    )

    # CDN Settings
    CDN_BASE_URL: str = Field(
        default="https://cdn.example.com", description="CDN base URL"
    )
    CDN_CACHE_TTL: int = Field(default=300, description="CDN cache TTL")

    # DRM Settings
    DRM_WIDEVINE_URL: str = Field(
        default="https://drm.example.com/widevine", description="Widevine DRM URL"
    )
    DRM_FAIRPLAY_URL: str = Field(
        default="https://drm.example.com/fairplay", description="FairPlay DRM URL"
    )
    DRM_PLAYREADY_URL: str = Field(
        default="https://drm.example.com/playready", description="PlayReady DRM URL"
    )

    # Email Settings
    SENDGRID_API_KEY: Optional[str] = Field(
        default=None, description="SendGrid API key"
    )
    SENDGRID_FROM_EMAIL: str = Field(
        default="noreply@example.com", description="SendGrid from email"
    )
    SENDGRID_FROM_NAME: str = Field(
        default="My Service", description="SendGrid from name"
    )

    # SMS Settings
    TWILIO_ACCOUNT_SID: Optional[str] = Field(
        default=None, description="Twilio account SID"
    )
    TWILIO_AUTH_TOKEN: Optional[str] = Field(
        default=None, description="Twilio auth token"
    )
    TWILIO_PHONE_NUMBER: Optional[str] = Field(
        default=None, description="Twilio phone number"
    )

    # Feature Flags (Example flags - customize for your service)
    FEATURE_REGISTRATION_ENABLED: bool = Field(
        default=True, description="Enable registration"
    )
    FEATURE_SOCIAL_LOGIN_ENABLED: bool = Field(
        default=True, description="Enable social login"
    )
    FEATURE_2FA_ENABLED: bool = Field(default=True, description="Enable 2FA")
    FEATURE_API_DOCS_ENABLED: bool = Field(
        default=True, description="Enable API documentation"
    )
    FEATURE_METRICS_ENABLED: bool = Field(
        default=True, description="Enable metrics endpoint"
    )

    # Health Check
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval")
    HEALTH_CHECK_TIMEOUT: int = Field(default=5, description="Health check timeout")

    # Database Enable Flags (Modular Database Configuration)
    ENABLE_POSTGRES: bool = Field(
        default=True,
        description="Enable PostgreSQL database connection. Set to False if service doesn't need PostgreSQL.",
    )
    ENABLE_MONGODB: bool = Field(
        default=True,
        description="Enable MongoDB database connection. Set to False if service doesn't need MongoDB.",
    )
    ENABLE_REDIS: bool = Field(
        default=True,
        description="Enable Redis cache connection. Set to False if service doesn't need Redis.",
    )

    @field_validator("ENABLE_POSTGRES", "ENABLE_MONGODB", "ENABLE_REDIS")
    @classmethod
    def validate_at_least_one_database(cls, v: bool, info) -> bool:
        """Validate that at least one database is enabled."""
        # This runs per field, so we check in model_validator below
        return v

    @property
    def has_postgres(self) -> bool:
        """Check if PostgreSQL is enabled."""
        return self.ENABLE_POSTGRES

    @property
    def has_mongodb(self) -> bool:
        """Check if MongoDB is enabled."""
        return self.ENABLE_MONGODB

    @property
    def has_redis(self) -> bool:
        """Check if Redis is enabled."""
        return self.ENABLE_REDIS

    @property
    def enabled_databases(self) -> List[str]:
        """Get list of enabled databases."""
        databases = []
        if self.ENABLE_POSTGRES:
            databases.append("PostgreSQL")
        if self.ENABLE_MONGODB:
            databases.append("MongoDB")
        if self.ENABLE_REDIS:
            databases.append("Redis")
        return databases


# Global settings instance
settings = Settings()
