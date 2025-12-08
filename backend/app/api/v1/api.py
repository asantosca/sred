# app/api/v1/api.py - Main API router

from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints import auth, users, matters, documents, usage, search, chat, billable, briefing, sentry_test, public

# Create main API router
api_router = APIRouter()

# Health check for API
@api_router.get("/health")
async def api_health():
    """API health check"""
    return {"status": "healthy", "api_version": "v1"}

# Include endpoint routers
api_router.include_router(public.router, prefix="/public", tags=["public"])  # No auth required
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["user-management"])
api_router.include_router(matters.router, prefix="/matters", tags=["matter-management"])
api_router.include_router(documents.router, prefix="/documents", tags=["document-management"])
api_router.include_router(search.router, prefix="/search", tags=["semantic-search"])
api_router.include_router(usage.router, prefix="/usage", tags=["usage-tracking"])
api_router.include_router(chat.router, prefix="/chat", tags=["ai-chat"])
api_router.include_router(billable.router, prefix="/billable", tags=["billable-hours"])
api_router.include_router(briefing.router, prefix="/briefing", tags=["daily-briefing"])
api_router.include_router(sentry_test.router, prefix="/sentry", tags=["sentry-testing"])