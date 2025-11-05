# app/api/v1/endpoints/usage.py - Usage tracking and statistics endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.models import User
from app.services.usage_tracker import UsageTracker

router = APIRouter()


@router.get("/stats", response_model=dict)
async def get_usage_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current usage statistics for the user's company.

    Returns usage details including:
    - Document count vs limit
    - Storage usage vs limit
    - AI query usage vs limit
    - Embeddings count
    - Warnings if approaching limits
    """
    usage_tracker = UsageTracker(db)
    stats = await usage_tracker.get_usage_stats(current_user.company_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company usage statistics not found"
        )

    # Generate warnings for items approaching limits
    warnings = []

    # Check documents
    if isinstance(stats['documents']['limit'], int):
        doc_percentage = stats['documents']['percentage']
        if doc_percentage >= 90:
            warnings.append({
                "level": "critical",
                "type": "documents",
                "message": f"Document usage at {doc_percentage:.0f}%. {stats['documents']['current']}/{stats['documents']['limit']} documents used."
            })
        elif doc_percentage >= 80:
            warnings.append({
                "level": "warning",
                "type": "documents",
                "message": f"Document usage at {doc_percentage:.0f}%. Consider upgrading your plan."
            })

    # Check storage
    if isinstance(stats['storage']['limit_gb'], int):
        storage_percentage = stats['storage']['percentage']
        if storage_percentage >= 90:
            warnings.append({
                "level": "critical",
                "type": "storage",
                "message": f"Storage usage at {storage_percentage:.0f}%. {stats['storage']['current_gb']}/{stats['storage']['limit_gb']} GB used."
            })
        elif storage_percentage >= 80:
            warnings.append({
                "level": "warning",
                "type": "storage",
                "message": f"Storage usage at {storage_percentage:.0f}%. Consider archiving old documents."
            })

    # Check AI queries
    if isinstance(stats['ai_queries']['limit'], int):
        query_percentage = stats['ai_queries']['percentage']
        if query_percentage >= 90:
            warnings.append({
                "level": "critical",
                "type": "ai_queries",
                "message": f"AI query usage at {query_percentage:.0f}%. {stats['ai_queries']['current']}/{stats['ai_queries']['limit']} queries this month."
            })
        elif query_percentage >= 80:
            warnings.append({
                "level": "warning",
                "type": "ai_queries",
                "message": f"AI query usage at {query_percentage:.0f}%. Resets at month start."
            })

    return {
        "company_id": str(current_user.company_id),
        "plan_tier": stats['plan_tier'],
        "usage": {
            "documents": stats['documents'],
            "storage": stats['storage'],
            "ai_queries": stats['ai_queries'],
            "embeddings": stats['embeddings']
        },
        "limits": stats['limits'],
        "warnings": warnings,
        "has_warnings": len(warnings) > 0
    }


@router.get("/limits", response_model=dict)
async def get_plan_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the plan limits for the user's company.

    Returns all limits defined by the company's plan tier.
    """
    usage_tracker = UsageTracker(db)
    limits = await usage_tracker.get_plan_limits(current_user.company_id)

    if not limits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan limits not found"
        )

    return limits


@router.get("/summary", response_model=dict)
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a quick usage summary with health indicators.

    Useful for dashboard widgets showing account health.
    """
    usage_tracker = UsageTracker(db)
    stats = await usage_tracker.get_usage_stats(current_user.company_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company usage statistics not found"
        )

    # Determine overall health status
    def get_health_status(percentage: float) -> str:
        """Convert percentage to health status."""
        if percentage >= 90:
            return "critical"
        elif percentage >= 75:
            return "warning"
        elif percentage >= 50:
            return "caution"
        else:
            return "healthy"

    # Calculate health for each resource
    doc_health = "healthy"
    if isinstance(stats['documents']['limit'], int):
        doc_health = get_health_status(stats['documents']['percentage'])

    storage_health = "healthy"
    if isinstance(stats['storage']['limit_gb'], int):
        storage_health = get_health_status(stats['storage']['percentage'])

    query_health = "healthy"
    if isinstance(stats['ai_queries']['limit'], int):
        query_health = get_health_status(stats['ai_queries']['percentage'])

    # Overall health is the worst of all categories
    health_priority = {"healthy": 0, "caution": 1, "warning": 2, "critical": 3}
    overall_health_score = max(
        health_priority[doc_health],
        health_priority[storage_health],
        health_priority[query_health]
    )
    overall_health = [k for k, v in health_priority.items() if v == overall_health_score][0]

    return {
        "company_id": str(current_user.company_id),
        "plan_tier": stats['plan_tier'],
        "overall_health": overall_health,
        "health_details": {
            "documents": {
                "status": doc_health,
                "current": stats['documents']['current'],
                "limit": stats['documents']['limit'],
                "percentage": round(stats['documents']['percentage'], 1)
            },
            "storage": {
                "status": storage_health,
                "current_gb": stats['storage']['current_gb'],
                "limit_gb": stats['storage']['limit_gb'],
                "percentage": round(stats['storage']['percentage'], 1)
            },
            "ai_queries": {
                "status": query_health,
                "current": stats['ai_queries']['current'],
                "limit": stats['ai_queries']['limit'],
                "percentage": round(stats['ai_queries']['percentage'], 1)
            }
        },
        "recommendations": _generate_recommendations(
            doc_health, storage_health, query_health, stats
        )
    }


def _generate_recommendations(
    doc_health: str,
    storage_health: str,
    query_health: str,
    stats: Dict
) -> list:
    """Generate actionable recommendations based on usage health."""
    recommendations = []

    if doc_health in ["warning", "critical"]:
        recommendations.append({
            "type": "documents",
            "priority": "high" if doc_health == "critical" else "medium",
            "message": "Document limit approaching. Consider archiving old documents or upgrading your plan.",
            "action": "review_documents"
        })

    if storage_health in ["warning", "critical"]:
        recommendations.append({
            "type": "storage",
            "priority": "high" if storage_health == "critical" else "medium",
            "message": "Storage limit approaching. Delete unused documents or contact administrator.",
            "action": "clean_storage"
        })

    if query_health in ["warning", "critical"]:
        recommendations.append({
            "type": "ai_queries",
            "priority": "high" if query_health == "critical" else "medium",
            "message": "AI query limit approaching. Usage resets at the start of next month.",
            "action": "monitor_queries"
        })

    # Add positive message if everything is healthy
    if not recommendations:
        recommendations.append({
            "type": "general",
            "priority": "info",
            "message": "All usage metrics are healthy. Keep up the good work!",
            "action": "none"
        })

    return recommendations
