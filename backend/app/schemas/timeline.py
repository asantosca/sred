# app/schemas/timeline.py - Pydantic schemas for document timeline events

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import date, datetime
from uuid import UUID


# Enums as Literals for validation
DatePrecision = Literal["day", "month", "year", "unknown"]
ConfidenceLevel = Literal["high", "medium", "low"]


class DocumentEventBase(BaseModel):
    """Base schema for document events"""
    event_date: date = Field(..., description="Date of the event")
    event_description: str = Field(..., min_length=1, max_length=2000, description="Description of the event")
    date_precision: DatePrecision = Field(default="day", description="Precision of the date: day, month, year, unknown")
    confidence: ConfidenceLevel = Field(default="high", description="Confidence level: high, medium, low")
    raw_date_text: Optional[str] = Field(None, max_length=255, description="Original date text from document")
    user_notes: Optional[str] = Field(None, max_length=2000, description="User notes about this event")


class DocumentEventCreate(DocumentEventBase):
    """Schema for creating a new event (user-created)"""
    document_id: UUID = Field(..., description="Document this event is from")
    matter_id: Optional[UUID] = Field(None, description="Matter this event belongs to (optional, derived from document if not provided)")


class DocumentEventUpdate(BaseModel):
    """Schema for updating an existing event"""
    event_date: Optional[date] = Field(None, description="Date of the event")
    event_description: Optional[str] = Field(None, min_length=1, max_length=2000, description="Description of the event")
    date_precision: Optional[DatePrecision] = Field(None, description="Precision of the date")
    confidence: Optional[ConfidenceLevel] = Field(None, description="Confidence level")
    user_notes: Optional[str] = Field(None, max_length=2000, description="User notes about this event")


class DocumentEventResponse(DocumentEventBase):
    """Response schema for document events"""
    id: UUID
    company_id: UUID
    matter_id: Optional[UUID]
    document_id: UUID
    chunk_id: Optional[UUID]

    # User override flags
    is_user_created: bool = Field(default=False, description="Whether this event was created by a user")
    is_user_modified: bool = Field(default=False, description="Whether this event was modified by a user")

    # Versioning
    document_version: Optional[int] = Field(None, description="Document version this was extracted from")
    superseded_at: Optional[datetime] = Field(None, description="When this event was superseded by newer extraction")

    # Audit
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]

    model_config = ConfigDict(from_attributes=True)


class DocumentEventWithContext(DocumentEventResponse):
    """Event response with document and matter context for display"""
    document_title: Optional[str] = Field(None, description="Title of the source document")
    document_filename: Optional[str] = Field(None, description="Filename of the source document")
    matter_name: Optional[str] = Field(None, description="Name of the matter")
    matter_number: Optional[str] = Field(None, description="Matter number")
    chunk_content: Optional[str] = Field(None, description="Content of the source chunk (for reference)")


class TimelineQuery(BaseModel):
    """Query parameters for timeline listing"""
    matter_id: Optional[UUID] = Field(None, description="Filter by matter")
    document_id: Optional[UUID] = Field(None, description="Filter by document")
    date_from: Optional[date] = Field(None, description="Filter events from this date")
    date_to: Optional[date] = Field(None, description="Filter events up to this date")
    confidence: Optional[ConfidenceLevel] = Field(None, description="Filter by confidence level")
    include_superseded: bool = Field(default=False, description="Include superseded events")
    user_created_only: bool = Field(default=False, description="Only show user-created events")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=200, description="Items per page")


class TimelineListResponse(BaseModel):
    """Paginated timeline response"""
    events: List[DocumentEventWithContext]
    total: int
    page: int
    page_size: int
    has_more: bool


class ExtractedEvent(BaseModel):
    """Schema for LLM-extracted events (internal use)"""
    event_date: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    event_description: str = Field(..., description="Description of what happened")
    date_precision: DatePrecision = Field(..., description="How precise is the date")
    confidence: ConfidenceLevel = Field(..., description="How confident is the extraction")
    raw_date_text: str = Field(..., description="Original date text from document")


class EventExtractionResult(BaseModel):
    """Result of event extraction from a document"""
    document_id: UUID
    events_extracted: int
    events: List[ExtractedEvent]
    extraction_errors: Optional[List[str]] = None
