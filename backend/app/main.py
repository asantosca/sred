# app/main.py - BC Legal Tech FastAPI Application

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

from app.api.v1.api import api_router
from app.middleware.auth import JWTAuthMiddleware
from app.middleware.validation import InputValidationMiddleware
from app.core.rate_limit import limiter
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        integrations=[
            FastApiIntegration(),
            AsyncioIntegration(),
        ],
        # Send user context (company_id, user_id) with errors
        send_default_pii=False,  # Don't send PII by default
        # Filter out health check endpoints from error tracking
        before_send=lambda event, hint: None if "/health" in event.get("request", {}).get("url", "") else event,
    )
    logger.info(f"Sentry initialized for environment: {settings.SENTRY_ENVIRONMENT}")

# Create FastAPI application
app = FastAPI(
    title="BC Legal Tech API",
    description="AI-powered legal document intelligence platform for law firms in British Columbia.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter state
app.state.limiter = limiter

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware (must be first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Main React app
        "http://localhost:3001",  # Marketing site
        "http://localhost:8000"   # Backend (for docs)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Input Validation middleware (before auth to catch malicious requests early)
app.add_middleware(InputValidationMiddleware)

# Add JWT Authentication middleware
app.add_middleware(JWTAuthMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "BC Legal Tech API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": "development",
        "database": "connected"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting BC Legal Tech API...")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down BC Legal Tech API...")