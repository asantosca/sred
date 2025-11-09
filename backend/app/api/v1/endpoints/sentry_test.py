# Test endpoint for Sentry error tracking
# This endpoint intentionally throws errors to test Sentry integration

from fastapi import APIRouter, HTTPException
import sentry_sdk
from app.core.config import settings

router = APIRouter()

@router.get("/test-error")
async def test_error():
    """
    Test endpoint that throws an error to verify Sentry is working.
    Visit: http://localhost:8000/api/v1/sentry/test-error

    This should:
    1. Throw an error
    2. Send it to Sentry
    3. Show up in your Sentry dashboard within seconds
    """
    if not settings.SENTRY_DSN:
        return {
            "error": "Sentry is not configured",
            "message": "Please add SENTRY_DSN to your .env file",
            "instructions": "See SENTRY_SETUP.md for details"
        }

    # This will trigger a Sentry error
    raise HTTPException(
        status_code=500,
        detail="This is a test error to verify Sentry integration is working!"
    )

@router.get("/test-message")
async def test_message():
    """
    Test endpoint that sends a message to Sentry without throwing an error.
    Visit: http://localhost:8000/api/v1/sentry/test-message
    """
    if not settings.SENTRY_DSN:
        return {
            "error": "Sentry is not configured",
            "message": "Please add SENTRY_DSN to your .env file"
        }

    # Send a test message to Sentry
    sentry_sdk.capture_message("Test message from BC Legal Tech backend", level="info")

    return {
        "success": True,
        "message": "Test message sent to Sentry! Check your Sentry dashboard.",
        "sentry_configured": True,
        "environment": settings.SENTRY_ENVIRONMENT
    }

@router.get("/test-exception")
async def test_exception():
    """
    Test endpoint that throws a Python exception (not HTTP error).
    This tests different error types in Sentry.
    """
    if not settings.SENTRY_DSN:
        return {
            "error": "Sentry is not configured",
            "message": "Please add SENTRY_DSN to your .env file"
        }

    # This will trigger an unhandled exception
    raise ValueError("Test exception: Testing Sentry error tracking with Python exception")

@router.get("/status")
async def sentry_status():
    """Check if Sentry is configured"""
    return {
        "sentry_configured": settings.SENTRY_DSN is not None,
        "environment": settings.SENTRY_ENVIRONMENT,
        "traces_sample_rate": settings.SENTRY_TRACES_SAMPLE_RATE,
        "instructions": "Visit /api/v1/sentry/test-error to trigger a test error" if settings.SENTRY_DSN else "Add SENTRY_DSN to .env file"
    }
