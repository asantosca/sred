# app/core/config.py - Configuration settings for BC Legal Tech

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app settings
    PROJECT_NAME: str = "BC Legal Tech"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/bc_legal_db"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # AWS/S3 settings
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_ENDPOINT_URL: Optional[str] = "http://localhost:4566"  # LocalStack
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "bc-legal-documents"
    
    # JWT settings
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    
    # Email settings (for future use)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # File upload limits
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_FILE_TYPES: List[str] = [
        ".pdf", ".docx", ".doc", ".txt", ".rtf"
    ]
    
    # Security settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Validation on startup
def validate_settings():
    """Validate critical settings on application startup"""
    errors = []
    
    if settings.JWT_SECRET_KEY == "your-secret-key-change-in-production":
        if settings.ENVIRONMENT == "production":
            errors.append("JWT_SECRET_KEY must be changed in production")
    
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

# Run validation
validate_settings()
