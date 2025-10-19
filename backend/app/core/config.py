# app/core/config.py - Simple configuration for BC Legal Tech

import os
from typing import List, Optional

class Settings:
    """Simple settings class"""
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/bc_legal_db"
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
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # AWS/S3 settings (should already be there)
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_ENDPOINT_URL: Optional[str] = "http://localhost:4566"  # LocalStack
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "bc-legal-documents"

# Create global settings instance
settings = Settings()
