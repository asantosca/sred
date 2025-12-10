# app/api/v1/endpoints/billable.py - Billable hours API endpoints

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.tenant import require_tenant_context
from app.core.rate_limit import limiter, get_rate_limit
from app.services.billable_service import BillableService
from app.schemas.billable import (
    BillableSessionCreate, BillableSessionUpdate, BillableSessionResponse,
    BillableSessionListResponse, GenerateDescriptionRequest,
    GenerateDescriptionResponse, ExportSessionsRequest, ExportSessionsResponse
)
from app.models.models import User
from sqlalchemy import select

router = APIRouter()


async def get_current_user(request: Request, db: AsyncSession) -> User:
    """Helper to get current user from tenant context"""
    tenant = require_tenant_context(request)
    result = await db.execute(
        select(User).where(User.id == tenant.user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("", response_model=BillableSessionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("default"))
async def create_billable_session(
    request: Request,
    session_data: BillableSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a billable session from a conversation.

    Calculates duration from message timestamps and generates an AI description
    of the legal work performed.
    """
    current_user = await get_current_user(request, db)
    service = BillableService(db)

    try:
        session = await service.create_session_from_conversation(
            conversation_id=session_data.conversation_id,
            current_user=current_user,
            generate_description=session_data.generate_description
        )
        return await service.get_session(session.id, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=BillableSessionListResponse)
@limiter.limit(get_rate_limit("default"))
async def list_billable_sessions(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    matter_id: Optional[UUID] = Query(None, description="Filter by matter"),
    include_exported: bool = Query(False, description="Include already exported sessions"),
    start_date: Optional[datetime] = Query(None, description="Filter sessions starting after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter sessions starting before this date"),
    db: AsyncSession = Depends(get_db)
):
    """
    List billable sessions for the current user.

    By default, only shows unexported sessions. Use include_exported=true to see all.
    """
    current_user = await get_current_user(request, db)
    service = BillableService(db)

    return await service.list_sessions(
        current_user=current_user,
        page=page,
        page_size=page_size,
        matter_id=matter_id,
        include_exported=include_exported,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{session_id}", response_model=BillableSessionResponse)
@limiter.limit(get_rate_limit("default"))
async def get_billable_session(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a single billable session by ID."""
    current_user = await get_current_user(request, db)
    service = BillableService(db)

    try:
        return await service.get_session(session_id, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{session_id}", response_model=BillableSessionResponse)
@limiter.limit(get_rate_limit("default"))
async def update_billable_session(
    request: Request,
    session_id: UUID,
    updates: BillableSessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a billable session.

    Allows editing description, duration, activity code, billable status, and matter.
    Cannot update exported sessions.
    """
    current_user = await get_current_user(request, db)
    service = BillableService(db)

    try:
        await service.update_session(session_id, updates, current_user)
        return await service.get_session(session_id, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(get_rate_limit("default"))
async def delete_billable_session(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a billable session.

    Cannot delete exported sessions.
    """
    current_user = await get_current_user(request, db)
    service = BillableService(db)

    try:
        await service.delete_session(session_id, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{session_id}/regenerate-description", response_model=GenerateDescriptionResponse)
@limiter.limit(get_rate_limit("ai_chat"))
async def regenerate_description(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate the AI description for a billable session.

    Uses Claude to analyze the conversation and generate a professional
    billing description.
    """
    current_user = await get_current_user(request, db)
    service = BillableService(db)

    try:
        description = await service.regenerate_description(session_id, current_user)
        return GenerateDescriptionResponse(
            session_id=session_id,
            ai_description=description
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/unbilled/conversations")
@limiter.limit(get_rate_limit("default"))
async def get_unbilled_conversations(
    request: Request,
    matter_id: Optional[UUID] = Query(None, description="Filter by matter"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversations that have a matter assigned but no billable session created.

    These represent potential unbilled work that the user may want to track.
    Returns a summary count and list of unbilled conversations.
    """
    current_user = await get_current_user(request, db)
    service = BillableService(db)

    return await service.get_unbilled_conversations(
        current_user=current_user,
        matter_id=matter_id
    )


@router.post("/export", response_model=ExportSessionsResponse)
@limiter.limit(get_rate_limit("default"))
async def export_sessions(
    request: Request,
    export_request: ExportSessionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark sessions as exported.

    This is typically called after exporting to a billing system like Clio.
    Exported sessions cannot be modified or deleted.
    """
    current_user = await get_current_user(request, db)
    service = BillableService(db)

    sessions = await service.mark_sessions_exported(
        session_ids=export_request.session_ids,
        current_user=current_user
    )

    # Get full session responses
    session_responses = []
    for session in sessions:
        session_responses.append(
            await service.get_session(session.id, current_user)
        )

    return ExportSessionsResponse(
        exported_count=len(sessions),
        sessions=session_responses
    )
