# app/core/rate_limit.py - Rate limiting configuration

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Create rate limiter instance
# Uses IP address as the identifier for rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"],  # Global default: 1000 requests per hour per IP
    storage_uri=settings.REDIS_URL,  # Use Redis for distributed rate limiting
    strategy="fixed-window",  # Simple fixed window strategy
)

# Rate limit tiers for different endpoint types
RATE_LIMITS = {
    # Authentication endpoints (prevent brute force)
    "auth_login": "5/minute",  # 5 login attempts per minute
    "auth_register": "3/minute",  # 3 registration attempts per minute
    "auth_password_reset": "3/hour",  # 3 password reset requests per hour

    # Document upload endpoints (prevent abuse)
    "document_upload": "20/minute",  # 20 uploads per minute
    "document_analyze": "30/minute",  # 30 pre-upload analyses per minute

    # Search endpoints (prevent excessive API usage)
    "search_semantic": "60/minute",  # 60 searches per minute

    # General API endpoints
    "api_read": "300/minute",  # 300 read operations per minute
    "api_write": "100/minute",  # 100 write operations per minute

    # Admin endpoints (stricter limits)
    "admin": "30/minute",  # 30 admin operations per minute
}


def get_rate_limit(limit_type: str) -> str:
    """
    Get rate limit string for a specific endpoint type.

    Args:
        limit_type: Type of rate limit (from RATE_LIMITS keys)

    Returns:
        Rate limit string (e.g., "5/minute")
    """
    return RATE_LIMITS.get(limit_type, "100/minute")
