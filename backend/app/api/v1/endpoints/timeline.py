# app/api/v1/endpoints/timeline.py - Timeline events API endpoints

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.tenant import require_tenant_context
from app.core.rate_limit import limiter, get_rate_limit
from app.models.models import User, Document, DocumentEvent, DocumentChunk, Claim as Matter
from app.schemas.timeline import (
    DocumentEventCreate, DocumentEventUpdate, DocumentEventResponse,
    DocumentEventWithContext, TimelineListResponse
)

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


@router.get("", response_model=TimelineListResponse)
@limiter.limit(get_rate_limit("default"))
async def list_events(
    request: Request,
    matter_id: Optional[UUID] = Query(None, description="Filter by matter"),
    document_id: Optional[UUID] = Query(None, description="Filter by document"),
    date_from: Optional[date] = Query(None, description="Filter events from this date"),
    date_to: Optional[date] = Query(None, description="Filter events up to this date"),
    confidence: Optional[str] = Query(None, description="Filter by confidence level (high, medium, low)"),
    include_superseded: bool = Query(False, description="Include superseded events"),
    user_created_only: bool = Query(False, description="Only show user-created events"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List timeline events with filters.

    Events are returned in chronological order by event_date.
    By default, only active (non-superseded) events are returned.
    """
    current_user = await get_current_user(request, db)

    # Build base query with tenant isolation
    query = select(DocumentEvent).where(
        DocumentEvent.company_id == current_user.company_id
    )

    # Apply filters
    if matter_id:
        query = query.where(DocumentEvent.claim_id == matter_id)

    if document_id:
        query = query.where(DocumentEvent.document_id == document_id)

    if date_from:
        query = query.where(DocumentEvent.event_date >= date_from)

    if date_to:
        query = query.where(DocumentEvent.event_date <= date_to)

    if confidence:
        query = query.where(DocumentEvent.confidence == confidence)

    if not include_superseded:
        query = query.where(DocumentEvent.superseded_at.is_(None))

    if user_created_only:
        query = query.where(DocumentEvent.is_user_created == True)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    query = query.order_by(DocumentEvent.event_date.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    events = result.scalars().all()

    # Enrich with context
    enriched_events = []
    for event in events:
        # Get document info
        doc_query = select(Document).where(Document.id == event.document_id)
        doc_result = await db.execute(doc_query)
        doc = doc_result.scalar()

        # Get matter info
        matter_name = None
        matter_number = None
        if event.claim_id:
            matter_query = select(Matter).where(Matter.id == event.claim_id)
            matter_result = await db.execute(matter_query)
            matter = matter_result.scalar()
            if matter:
                matter_name = matter.company_name
                matter_number = matter.claim_number

        # Get chunk content if available
        chunk_content = None
        if event.chunk_id:
            chunk_query = select(DocumentChunk.content).where(DocumentChunk.id == event.chunk_id)
            chunk_result = await db.execute(chunk_query)
            chunk_content = chunk_result.scalar()
            # Truncate for display
            if chunk_content and len(chunk_content) > 500:
                chunk_content = chunk_content[:500] + "..."

        enriched_events.append(DocumentEventWithContext(
            id=event.id,
            company_id=event.company_id,
            matter_id=event.claim_id,
            document_id=event.document_id,
            chunk_id=event.chunk_id,
            event_date=event.event_date,
            event_description=event.event_description,
            date_precision=event.date_precision,
            confidence=event.confidence,
            raw_date_text=event.raw_date_text,
            is_user_created=event.is_user_created,
            is_user_modified=event.is_user_modified,
            user_notes=event.user_notes,
            document_version=event.document_version,
            superseded_at=event.superseded_at,
            created_at=event.created_at,
            updated_at=event.updated_at,
            created_by=event.created_by,
            document_title=doc.document_title if doc else None,
            document_filename=doc.filename if doc else None,
            matter_name=matter_name,
            matter_number=matter_number,
            chunk_content=chunk_content
        ))

    return TimelineListResponse(
        events=enriched_events,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total
    )


@router.get("/matter/{matter_id}", response_model=TimelineListResponse)
@limiter.limit(get_rate_limit("default"))
async def list_matter_events(
    request: Request,
    matter_id: UUID,
    date_from: Optional[date] = Query(None, description="Filter events from this date"),
    date_to: Optional[date] = Query(None, description="Filter events up to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List timeline events for a specific matter.

    Convenience endpoint for matter-scoped views.
    """
    return await list_events(
        request=request,
        matter_id=matter_id,
        document_id=None,
        date_from=date_from,
        date_to=date_to,
        confidence=None,
        include_superseded=False,
        user_created_only=False,
        page=page,
        page_size=page_size,
        db=db
    )


@router.get("/document/{document_id}", response_model=TimelineListResponse)
@limiter.limit(get_rate_limit("default"))
async def list_document_events(
    request: Request,
    document_id: UUID,
    include_superseded: bool = Query(False, description="Include superseded events"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List timeline events from a specific document.

    Convenience endpoint for document-scoped views.
    """
    return await list_events(
        request=request,
        matter_id=None,
        document_id=document_id,
        date_from=None,
        date_to=None,
        confidence=None,
        include_superseded=include_superseded,
        user_created_only=False,
        page=page,
        page_size=page_size,
        db=db
    )


@router.post("", response_model=DocumentEventResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("default"))
async def create_event(
    request: Request,
    event_data: DocumentEventCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new timeline event (user-created).

    Users can manually add events that weren't automatically extracted.
    """
    current_user = await get_current_user(request, db)

    # Verify document access with tenant isolation
    doc_query = select(Document).join(Matter).where(
        Document.id == event_data.document_id,
        Matter.company_id == current_user.company_id
    )
    doc_result = await db.execute(doc_query)
    document = doc_result.scalar()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )

    # Use matter_id from document if not provided
    matter_id = event_data.matter_id or document.claim_id

    event = DocumentEvent(
        company_id=current_user.company_id,
        matter_id=matter_id,
        document_id=event_data.document_id,
        event_date=event_data.event_date,
        event_description=event_data.event_description,
        date_precision=event_data.date_precision,
        confidence=event_data.confidence,
        raw_date_text=event_data.raw_date_text,
        user_notes=event_data.user_notes,
        is_user_created=True,
        is_user_modified=False,
        created_by=current_user.id
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    return DocumentEventResponse.model_validate(event)


@router.get("/{event_id}", response_model=DocumentEventWithContext)
@limiter.limit(get_rate_limit("default"))
async def get_event(
    request: Request,
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a single event by ID."""
    current_user = await get_current_user(request, db)

    query = select(DocumentEvent).where(
        DocumentEvent.id == event_id,
        DocumentEvent.company_id == current_user.company_id
    )
    result = await db.execute(query)
    event = result.scalar()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Get document info
    doc_query = select(Document).where(Document.id == event.document_id)
    doc_result = await db.execute(doc_query)
    doc = doc_result.scalar()

    # Get matter info
    matter_name = None
    matter_number = None
    if event.claim_id:
        matter_query = select(Matter).where(Matter.id == event.claim_id)
        matter_result = await db.execute(matter_query)
        matter = matter_result.scalar()
        if matter:
            matter_name = matter.company_name
            matter_number = matter.claim_number

    # Get chunk content
    chunk_content = None
    if event.chunk_id:
        chunk_query = select(DocumentChunk.content).where(DocumentChunk.id == event.chunk_id)
        chunk_result = await db.execute(chunk_query)
        chunk_content = chunk_result.scalar()

    return DocumentEventWithContext(
        id=event.id,
        company_id=event.company_id,
        matter_id=event.claim_id,
        document_id=event.document_id,
        chunk_id=event.chunk_id,
        event_date=event.event_date,
        event_description=event.event_description,
        date_precision=event.date_precision,
        confidence=event.confidence,
        raw_date_text=event.raw_date_text,
        is_user_created=event.is_user_created,
        is_user_modified=event.is_user_modified,
        user_notes=event.user_notes,
        document_version=event.document_version,
        superseded_at=event.superseded_at,
        created_at=event.created_at,
        updated_at=event.updated_at,
        created_by=event.created_by,
        document_title=doc.document_title if doc else None,
        document_filename=doc.filename if doc else None,
        matter_name=matter_name,
        matter_number=matter_number,
        chunk_content=chunk_content
    )


@router.patch("/{event_id}", response_model=DocumentEventResponse)
@limiter.limit(get_rate_limit("default"))
async def update_event(
    request: Request,
    event_id: UUID,
    updates: DocumentEventUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a timeline event.

    Marking an AI-extracted event as modified preserves it during re-extraction.
    """
    current_user = await get_current_user(request, db)

    query = select(DocumentEvent).where(
        DocumentEvent.id == event_id,
        DocumentEvent.company_id == current_user.company_id
    )
    result = await db.execute(query)
    event = result.scalar()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Apply updates
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    # Mark as user-modified if it was AI-extracted
    if not event.is_user_created:
        event.is_user_modified = True

    await db.commit()
    await db.refresh(event)

    return DocumentEventResponse.model_validate(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(get_rate_limit("default"))
async def delete_event(
    request: Request,
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a timeline event.

    This is a hard delete. Use with caution.
    """
    current_user = await get_current_user(request, db)

    query = select(DocumentEvent).where(
        DocumentEvent.id == event_id,
        DocumentEvent.company_id == current_user.company_id
    )
    result = await db.execute(query)
    event = result.scalar()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    await db.delete(event)
    await db.commit()
