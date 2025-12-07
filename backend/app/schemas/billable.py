# app/schemas/billable.py - Schemas for billable hours/sessions

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class BillableSessionBase(BaseModel):
    """Base billable session schema"""
    matter_id: Optional[UUID] = Field(None, description="Matter this session is billed to")
    activity_code: Optional[str] = Field(None, max_length=50, description="Activity/billing code")
    is_billable: bool = Field(True, description="Whether this time is billable")


class BillableSessionCreate(BaseModel):
    """Schema for creating a billable session from a conversation"""
    conversation_id: UUID = Field(..., description="Conversation to generate billing from")
    generate_description: bool = Field(True, description="Generate AI description of work")


class BillableSessionUpdate(BaseModel):
    """Schema for updating a billable session"""
    description: Optional[str] = Field(None, description="User-edited description")
    duration_minutes: Optional[int] = Field(None, ge=1, description="Adjusted duration in minutes")
    activity_code: Optional[str] = Field(None, max_length=50)
    is_billable: Optional[bool] = None
    matter_id: Optional[UUID] = None


class BillableSessionResponse(BillableSessionBase):
    """Schema for billable session response"""
    id: UUID
    user_id: UUID
    company_id: UUID
    conversation_id: UUID
    conversation_title: Optional[str] = None

    # Timing
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[int]

    # Descriptions
    ai_description: Optional[str] = Field(None, description="AI-generated description")
    description: Optional[str] = Field(None, description="User-edited description (if changed)")

    # Status
    is_exported: bool = False
    exported_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Related info
    matter_name: Optional[str] = None

    class Config:
        from_attributes = True


class BillableSessionListResponse(BaseModel):
    """Paginated list of billable sessions"""
    sessions: List[BillableSessionResponse]
    total: int
    page: int
    page_size: int
    total_minutes: int = Field(0, description="Total billable minutes in result set")


class GenerateDescriptionRequest(BaseModel):
    """Request to regenerate AI description for a session"""
    session_id: UUID


class GenerateDescriptionResponse(BaseModel):
    """Response with generated description"""
    session_id: UUID
    ai_description: str


class ExportSessionsRequest(BaseModel):
    """Request to mark sessions as exported"""
    session_ids: List[UUID] = Field(..., min_length=1, description="Sessions to mark as exported")


class ExportSessionsResponse(BaseModel):
    """Response from export operation"""
    exported_count: int
    sessions: List[BillableSessionResponse]
