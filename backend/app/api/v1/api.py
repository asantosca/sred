# app/api/v1/api.py - Main API router

from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints import auth, users, matters, documents, usage, search, chat, billable, briefing, timeline, sentry_test, public, admin, eligibility, t661, projects, workspace

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
api_router.include_router(timeline.router, prefix="/timeline", tags=["document-timeline"])
api_router.include_router(sentry_test.router, prefix="/sentry", tags=["sentry-testing"])
api_router.include_router(admin.router, prefix="/admin", tags=["platform-admin"])
api_router.include_router(eligibility.router, prefix="/claims", tags=["sred-eligibility"])
api_router.include_router(t661.router, prefix="/claims", tags=["sred-t661"])
api_router.include_router(projects.router, prefix="/projects", tags=["project-discovery"])
api_router.include_router(workspace.router, tags=["project-workspace"])