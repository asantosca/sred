# app/core/config.py - Simple configuration for BC Legal Tech

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Simple settings class"""
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bc_legal_db"
    )
    
    # Basic app settings
    PROJECT_NAME: str = "BC Legal Tech"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # JWT settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days for refresh tokens
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://localhost:8000"
        ).split(",")
        if origin.strip()
    ]
    # Production domains (always included when ENVIRONMENT != development)
    CORS_PRODUCTION_ORIGINS: List[str] = [
        "https://app.bclegaltech.ca",
        "https://bclegaltech.ca",
        "https://www.bclegaltech.ca",
    ]

    # Frontend URL (for email links, redirects, etc.)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # AWS/S3 settings
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "test")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    AWS_ENDPOINT_URL: Optional[str] = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")  # LocalStack
    AWS_REGION: str = os.getenv("AWS_REGION", "ca-central-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "bc-legal-documents")

    # Email settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))  # MailHog port
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "false").lower() == "true"
    SMTP_SSL: bool = os.getenv("SMTP_SSL", "false").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@bclegaltech.com")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "BC Legal Tech")

    # OpenAI settings (for embeddings)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_EMBEDDING_DIMENSIONS: int = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536"))

    # Anthropic/Claude settings (for chat)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")
    ANTHROPIC_MAX_TOKENS: int = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))

    # Valkey settings (Redis-compatible, for Celery broker and result backend)
    # Note: Using Valkey instead of Redis for 20-33% cost savings on AWS ElastiCache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "America/Vancouver"  # BC timezone
    CELERY_ENABLE_UTC: bool = True

    # Sentry settings (error tracking)
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))  # 10% of transactions
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", ENVIRONMENT)

    # Platform admin settings (comma-separated list of admin email addresses)
    PLATFORM_ADMIN_EMAILS: List[str] = [
        email.strip().lower()
        for email in os.getenv("PLATFORM_ADMIN_EMAILS", "").split(",")
        if email.strip()
    ]

# Create global settings instance
settings = Settings()
