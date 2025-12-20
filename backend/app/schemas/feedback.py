# app/schemas/feedback.py - Feedback Analytics Pydantic models

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class FeedbackCategory(str, Enum):
    """Categories for negative feedback"""
    INCORRECT = "incorrect"
    IRRELEVANT = "irrelevant"
    WRONG_QUESTION = "wrong_question"
    NOT_DETAILED = "not_detailed"
    NO_DOCUMENTS = "no_documents"


class SignalType(str, Enum):
    """Types of interaction signals"""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    COPY = "copy"
    SOURCE_CLICK = "source_click"


# Request Schemas

class EnhancedMessageFeedback(BaseModel):
    """Enhanced feedback with category support"""
    rating: int = Field(..., ge=-1, le=1, description="Thumbs: -1 (down), 1 (up)")
    feedback_category: Optional[FeedbackCategory] = Field(
        None,
        description="Category for negative feedback: incorrect, irrelevant, wrong_question, not_detailed, no_documents"
    )
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Optional free-text feedback")


class InteractionSignal(BaseModel):
    """Frontend interaction signal for behavioral tracking"""
    signal_type: SignalType = Field(..., description="Type of interaction signal")
    conversation_id: UUID = Field(..., description="Conversation where signal occurred")
    message_id: Optional[UUID] = Field(None, description="Specific message (for copy, source_click)")
    document_id: Optional[UUID] = Field(None, description="Document clicked (for source_click)")
    timestamp: Optional[datetime] = Field(None, description="Client-side timestamp")


# Response Schemas

class FeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    message_id: UUID
    rating: int
    feedback_category: Optional[str]
    feedback_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SignalTrackingResponse(BaseModel):
    """Response from signal tracking endpoint"""
    status: str = "accepted"
    signal_type: str


class FeedbackTotals(BaseModel):
    """Aggregate counts for feedback"""
    total_messages: int
    total_feedback: int
    positive_count: int
    negative_count: int


class FeedbackRates(BaseModel):
    """Calculated rates for feedback metrics"""
    positive_rate: Optional[float] = Field(None, description="Rate of positive feedback (0.0-1.0)")
    rephrase_rate: Optional[float] = Field(None, description="Rate of message rephrases (0.0-1.0)")
    abandonment_rate: Optional[float] = Field(None, description="Rate of session abandonment (0.0-1.0)")
    engagement_rate: Optional[float] = Field(None, description="Rate of engagement (copy + clicks) (0.0-1.0)")


class FeedbackTimeSeriesPoint(BaseModel):
    """Single point in feedback time series"""
    period_start: datetime
    period_end: datetime
    total_messages: int
    positive_count: int
    negative_count: int
    positive_rate: Optional[float]
    rephrase_rate: Optional[float]
    abandonment_rate: Optional[float]
    engagement_rate: Optional[float]


class FeedbackStatsResponse(BaseModel):
    """Comprehensive feedback statistics response"""
    period_start: datetime
    period_end: datetime
    granularity: str = Field(..., description="hourly, daily, or weekly")

    totals: FeedbackTotals
    rates: FeedbackRates
    by_category: Dict[str, int] = Field(default_factory=dict, description="Count by feedback category")

    time_series: List[FeedbackTimeSeriesPoint] = Field(default_factory=list)

    avg_question_quality: Optional[float] = Field(None, description="Average question quality score (0.0-1.0)")
    avg_response_confidence: Optional[float] = Field(None, description="Average response confidence (0.0-1.0)")


class FeedbackAlertResponse(BaseModel):
    """Feedback alert for quality issues"""
    id: UUID
    company_id: Optional[UUID]
    company_name: Optional[str]

    alert_type: str = Field(..., description="Type: high_negative_rate, abandonment_spike, rephrase_spike")
    severity: str = Field(..., description="warning or critical")
    threshold_value: float
    current_value: float

    time_window_minutes: int
    triggered_at: datetime
    resolved_at: Optional[datetime]
    is_active: bool

    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class FlaggedMessageResponse(BaseModel):
    """Message flagged for review due to quality issues"""
    message_id: UUID
    conversation_id: UUID
    company_id: UUID
    company_name: Optional[str]

    user_query: str = Field(..., description="The user's original question")
    ai_response: str = Field(..., description="The AI response that was flagged")
    created_at: datetime

    # Feedback info
    rating: Optional[int]
    feedback_category: Optional[str]
    feedback_text: Optional[str]

    # Scores
    confidence_score: Optional[float]
    question_quality_score: Optional[float]

    flag_reason: str = Field(..., description="Why flagged: negative_feedback, low_confidence, high_rephrase")


class ConversationSignalsResponse(BaseModel):
    """Behavioral signals for a conversation session"""
    id: UUID
    conversation_id: UUID
    session_started_at: datetime
    session_ended_at: Optional[datetime]

    rephrase_count: int
    copy_events: int
    source_clicks: int
    is_abandoned: bool
    conversation_continued: bool
    billable_created: bool

    class Config:
        from_attributes = True


class MessageQualityScoreResponse(BaseModel):
    """Quality/confidence scores for a message"""
    message_id: UUID
    question_quality_score: Optional[float]
    overall_confidence_score: Optional[float]
    has_matter_context: bool
    has_document_context: bool
    is_follow_up_to_rephrase: bool
    score_version: str

    class Config:
        from_attributes = True
