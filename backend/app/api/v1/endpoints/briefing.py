# app/api/v1/endpoints/briefing.py - Daily briefing endpoints

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.models import User
from app.services.briefing_service import BriefingService

logger = logging.getLogger(__name__)

router = APIRouter()


class BriefingResponse(BaseModel):
    """Response model for daily briefing"""
    briefing_date: date
    content: str
    generated_at: str
    is_fresh: bool  # True if just generated, False if cached


@router.get("/today", response_model=BriefingResponse)
async def get_today_briefing(
    regenerate: bool = Query(False, description="Force regeneration of briefing"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get today's AI-generated briefing.

    The briefing is generated once per day and cached.
    Use regenerate=true to force a fresh briefing (costs API tokens).
    """
    service = BriefingService(db)
    today = date.today()

    # Check for existing briefing first
    if not regenerate:
        from sqlalchemy import select, and_
        from app.models.models import DailyBriefing

        query = select(DailyBriefing).where(
            and_(
                DailyBriefing.user_id == current_user.id,
                DailyBriefing.briefing_date == today
            )
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            return BriefingResponse(
                briefing_date=existing.briefing_date,
                content=existing.content,
                generated_at=existing.generated_at.isoformat(),
                is_fresh=False
            )

    # Generate new briefing
    briefing = await service.generate_briefing(current_user, today)

    if not briefing:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate briefing. Please try again later."
        )

    return BriefingResponse(
        briefing_date=briefing.briefing_date,
        content=briefing.content,
        generated_at=briefing.generated_at.isoformat(),
        is_fresh=True
    )


@router.get("/history", response_model=list[BriefingResponse])
async def get_briefing_history(
    limit: int = Query(7, ge=1, le=30, description="Number of past briefings to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get past briefings for the user.

    Returns up to the last 30 days of briefings.
    """
    from sqlalchemy import select, desc
    from app.models.models import DailyBriefing

    query = select(DailyBriefing).where(
        DailyBriefing.user_id == current_user.id
    ).order_by(
        desc(DailyBriefing.briefing_date)
    ).limit(limit)

    result = await db.execute(query)
    briefings = result.scalars().all()

    return [
        BriefingResponse(
            briefing_date=b.briefing_date,
            content=b.content,
            generated_at=b.generated_at.isoformat(),
            is_fresh=False
        )
        for b in briefings
    ]
