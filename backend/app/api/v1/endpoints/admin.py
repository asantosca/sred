# app/api/v1/endpoints/admin.py - Platform admin API endpoints

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.api.deps import get_platform_admin_user
from app.models.models import User, Company, ApiUsageLog
from app.services.feedback_analytics import FeedbackAnalyticsService
from app.schemas.feedback import (
    FeedbackStatsResponse, FeedbackAlertResponse, FlaggedMessageResponse
)

router = APIRouter()


class UsageSummary(BaseModel):
    """Summary of API usage for a company or overall"""
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_chunks_processed: int
    total_pages_ocr: int
    estimated_cost_cents: int

    class Config:
        from_attributes = True


class CompanyUsage(BaseModel):
    """Usage summary for a specific company"""
    company_id: UUID
    company_name: str
    usage: UsageSummary


class ServiceBreakdown(BaseModel):
    """Usage breakdown by service"""
    service: str
    request_count: int
    input_tokens: int
    output_tokens: int
    chunks_processed: int
    pages_ocr: int
    estimated_cost_cents: int


class UsageResponse(BaseModel):
    """Response for usage endpoints"""
    period_start: datetime
    period_end: datetime
    overall: UsageSummary
    by_company: List[CompanyUsage]
    by_service: List[ServiceBreakdown]


class DailyUsage(BaseModel):
    """Daily usage data point"""
    date: str
    request_count: int
    estimated_cost_cents: int


@router.get("/usage", response_model=UsageResponse)
async def get_usage_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    company_id: Optional[UUID] = Query(default=None, description="Filter by company ID"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_platform_admin_user)
):
    """
    Get API usage summary for cost tracking.

    Requires platform admin privileges.
    """
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    # Base filter
    base_filter = ApiUsageLog.created_at >= period_start
    if company_id:
        base_filter = and_(base_filter, ApiUsageLog.company_id == company_id)

    # Overall summary
    overall_query = select(
        func.count(ApiUsageLog.id).label('total_requests'),
        func.coalesce(func.sum(ApiUsageLog.input_tokens), 0).label('total_input_tokens'),
        func.coalesce(func.sum(ApiUsageLog.output_tokens), 0).label('total_output_tokens'),
        func.coalesce(func.sum(ApiUsageLog.chunks_processed), 0).label('total_chunks_processed'),
        func.coalesce(func.sum(ApiUsageLog.pages_processed), 0).label('total_pages_ocr'),
        func.coalesce(func.sum(ApiUsageLog.estimated_cost_cents), 0).label('estimated_cost_cents')
    ).where(base_filter)

    overall_result = await db.execute(overall_query)
    overall_row = overall_result.one()

    overall = UsageSummary(
        total_requests=overall_row.total_requests,
        total_input_tokens=overall_row.total_input_tokens,
        total_output_tokens=overall_row.total_output_tokens,
        total_chunks_processed=overall_row.total_chunks_processed,
        total_pages_ocr=overall_row.total_pages_ocr,
        estimated_cost_cents=overall_row.estimated_cost_cents
    )

    # By company (only if not filtering by specific company)
    by_company = []
    if not company_id:
        company_query = select(
            ApiUsageLog.company_id,
            Company.name.label('company_name'),
            func.count(ApiUsageLog.id).label('total_requests'),
            func.coalesce(func.sum(ApiUsageLog.input_tokens), 0).label('total_input_tokens'),
            func.coalesce(func.sum(ApiUsageLog.output_tokens), 0).label('total_output_tokens'),
            func.coalesce(func.sum(ApiUsageLog.chunks_processed), 0).label('total_chunks_processed'),
            func.coalesce(func.sum(ApiUsageLog.pages_processed), 0).label('total_pages_ocr'),
            func.coalesce(func.sum(ApiUsageLog.estimated_cost_cents), 0).label('estimated_cost_cents')
        ).join(
            Company, ApiUsageLog.company_id == Company.id, isouter=True
        ).where(
            and_(base_filter, ApiUsageLog.company_id.isnot(None))
        ).group_by(
            ApiUsageLog.company_id, Company.name
        ).order_by(
            func.sum(ApiUsageLog.estimated_cost_cents).desc()
        )

        company_result = await db.execute(company_query)
        for row in company_result:
            by_company.append(CompanyUsage(
                company_id=row.company_id,
                company_name=row.company_name or "Unknown",
                usage=UsageSummary(
                    total_requests=row.total_requests,
                    total_input_tokens=row.total_input_tokens,
                    total_output_tokens=row.total_output_tokens,
                    total_chunks_processed=row.total_chunks_processed,
                    total_pages_ocr=row.total_pages_ocr,
                    estimated_cost_cents=row.estimated_cost_cents
                )
            ))

    # By service
    service_query = select(
        ApiUsageLog.service,
        func.count(ApiUsageLog.id).label('request_count'),
        func.coalesce(func.sum(ApiUsageLog.input_tokens), 0).label('input_tokens'),
        func.coalesce(func.sum(ApiUsageLog.output_tokens), 0).label('output_tokens'),
        func.coalesce(func.sum(ApiUsageLog.chunks_processed), 0).label('chunks_processed'),
        func.coalesce(func.sum(ApiUsageLog.pages_processed), 0).label('pages_ocr'),
        func.coalesce(func.sum(ApiUsageLog.estimated_cost_cents), 0).label('estimated_cost_cents')
    ).where(base_filter).group_by(ApiUsageLog.service).order_by(
        func.sum(ApiUsageLog.estimated_cost_cents).desc()
    )

    service_result = await db.execute(service_query)
    by_service = [
        ServiceBreakdown(
            service=row.service,
            request_count=row.request_count,
            input_tokens=row.input_tokens,
            output_tokens=row.output_tokens,
            chunks_processed=row.chunks_processed,
            pages_ocr=row.pages_ocr,
            estimated_cost_cents=row.estimated_cost_cents
        )
        for row in service_result
    ]

    return UsageResponse(
        period_start=period_start,
        period_end=period_end,
        overall=overall,
        by_company=by_company,
        by_service=by_service
    )


@router.get("/usage/daily", response_model=List[DailyUsage])
async def get_daily_usage(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    service: Optional[str] = Query(default=None, description="Filter by service"),
    company_id: Optional[UUID] = Query(default=None, description="Filter by company ID"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_platform_admin_user)
):
    """
    Get daily API usage for cost trending.

    Requires platform admin privileges.
    """
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    # Build filter
    filters = [ApiUsageLog.created_at >= period_start]
    if service:
        filters.append(ApiUsageLog.service == service)
    if company_id:
        filters.append(ApiUsageLog.company_id == company_id)

    # Daily aggregation
    daily_query = select(
        func.date(ApiUsageLog.created_at).label('date'),
        func.count(ApiUsageLog.id).label('request_count'),
        func.coalesce(func.sum(ApiUsageLog.estimated_cost_cents), 0).label('estimated_cost_cents')
    ).where(and_(*filters)).group_by(
        func.date(ApiUsageLog.created_at)
    ).order_by(
        func.date(ApiUsageLog.created_at)
    )

    result = await db.execute(daily_query)

    return [
        DailyUsage(
            date=str(row.date),
            request_count=row.request_count,
            estimated_cost_cents=row.estimated_cost_cents
        )
        for row in result
    ]


class CompanySummary(BaseModel):
    """Summary of a company for admin view"""
    id: UUID
    name: str
    plan_tier: str
    user_count: int
    is_active: bool
    created_at: datetime


@router.get("/companies", response_model=List[CompanySummary])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_platform_admin_user)
):
    """
    List all companies with summary info.

    Requires platform admin privileges.
    """
    query = select(
        Company.id,
        Company.name,
        Company.plan_tier,
        Company.is_active,
        Company.created_at,
        func.count(User.id).label('user_count')
    ).outerjoin(
        User, Company.id == User.company_id
    ).group_by(
        Company.id, Company.name, Company.plan_tier, Company.is_active, Company.created_at
    ).order_by(Company.created_at.desc())

    result = await db.execute(query)

    return [
        CompanySummary(
            id=row.id,
            name=row.name,
            plan_tier=row.plan_tier or "starter",
            user_count=row.user_count,
            is_active=row.is_active,
            created_at=row.created_at
        )
        for row in result
    ]


# =====================
# Feedback Analytics Endpoints
# =====================

@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
async def get_feedback_statistics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    company_id: Optional[UUID] = Query(default=None, description="Filter by company ID"),
    granularity: str = Query(default="daily", pattern="^(hourly|daily|weekly)$"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_platform_admin_user)
):
    """
    Get feedback statistics for AI response quality monitoring.

    Provides:
    - Total counts (messages, feedback, positive, negative)
    - Rates (positive, rephrase, abandonment, engagement)
    - Category breakdown
    - Average quality scores

    Requires platform admin privileges.
    """
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    feedback_service = FeedbackAnalyticsService(db)
    return await feedback_service.get_feedback_stats(
        company_id=company_id,
        start_date=period_start,
        end_date=period_end,
        granularity=granularity
    )


@router.get("/feedback/alerts", response_model=List[FeedbackAlertResponse])
async def get_feedback_alerts(
    company_id: Optional[UUID] = Query(default=None, description="Filter by company ID"),
    include_resolved: bool = Query(default=False, description="Include resolved alerts"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_platform_admin_user)
):
    """
    Get active (or all) feedback quality alerts.

    Alert types:
    - `high_negative_rate`: Too many negative feedback in short time
    - `abandonment_spike`: High session abandonment rate
    - `rephrase_spike`: Users frequently rephrasing questions

    Requires platform admin privileges.
    """
    feedback_service = FeedbackAnalyticsService(db)
    return await feedback_service.get_active_alerts(
        company_id=company_id,
        include_resolved=include_resolved
    )


@router.get("/feedback/flagged", response_model=List[FlaggedMessageResponse])
async def get_flagged_messages(
    company_id: Optional[UUID] = Query(default=None, description="Filter by company ID"),
    limit: int = Query(default=50, ge=1, le=200, description="Max messages to return"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_platform_admin_user)
):
    """
    Get messages flagged for review due to quality issues.

    Includes messages with:
    - Negative feedback (-1 rating)
    - Low confidence scores (< 0.3)
    - High rephrase patterns

    Each flagged message includes the user's question, AI response,
    feedback details, and confidence scores.

    Requires platform admin privileges.
    """
    feedback_service = FeedbackAnalyticsService(db)
    return await feedback_service.get_flagged_messages(
        company_id=company_id,
        limit=limit
    )


@router.post("/feedback/check-alerts")
async def check_feedback_alerts(
    company_id: Optional[UUID] = Query(default=None, description="Check for specific company"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_platform_admin_user)
):
    """
    Manually trigger alert threshold checking.

    Normally this runs automatically via Celery, but this endpoint
    allows manual triggering for testing or immediate checks.

    Requires platform admin privileges.
    """
    feedback_service = FeedbackAnalyticsService(db)
    new_alerts = await feedback_service.check_alert_thresholds(company_id=company_id)

    return {
        "alerts_created": len(new_alerts),
        "alert_ids": [str(a.id) for a in new_alerts]
    }
