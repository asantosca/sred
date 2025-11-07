# app/schemas/chat.py - Chat/Conversation Pydantic models

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime


# Message schemas
class MessageBase(BaseModel):
    """Base message model"""
    role: str = Field(..., pattern="^(user|assistant)$", description="Message role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    pass


class MessageSource(BaseModel):
    """Source citation for assistant message"""
    document_id: UUID
    document_title: str
    chunk_id: UUID
    content: str = Field(..., description="Chunk content")
    page_number: Optional[int] = None
    similarity_score: float
    matter_id: UUID
    matter_name: str


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: UUID
    conversation_id: UUID
    sources: Optional[List[MessageSource]] = Field(None, description="Citations for assistant messages")
    token_count: Optional[int] = None
    model_name: Optional[str] = None
    rating: Optional[int] = Field(None, ge=-1, le=5, description="User rating: -1/1 for thumbs, 1-5 for stars")
    feedback_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageFeedback(BaseModel):
    """Schema for submitting message feedback"""
    rating: int = Field(..., ge=-1, le=5, description="-1 (thumbs down), 1 (thumbs up), or 1-5 stars")
    feedback_text: Optional[str] = Field(None, max_length=1000)


# Conversation schemas
class ConversationBase(BaseModel):
    """Base conversation model"""
    matter_id: Optional[UUID] = Field(None, description="Optional matter to scope the conversation to")
    title: Optional[str] = Field(None, max_length=500, description="Conversation title (auto-generated if not provided)")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""
    title: Optional[str] = Field(None, max_length=500)
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    id: UUID
    user_id: UUID
    company_id: UUID
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime]
    message_count: Optional[int] = Field(None, description="Total messages in conversation")
    last_message_preview: Optional[str] = Field(None, description="Preview of last message")

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Conversation with full message history"""
    messages: List[MessageResponse] = []


class ConversationListResponse(BaseModel):
    """Paginated list of conversations"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int


# Chat request/response schemas
class ChatRequest(BaseModel):
    """Request to send a message and get a response"""
    conversation_id: Optional[UUID] = Field(None, description="Existing conversation ID, or None to create new")
    message: str = Field(..., min_length=1, max_length=10000, description="User's message")
    matter_id: Optional[UUID] = Field(None, description="Matter to scope search to (for new conversations)")
    include_sources: bool = Field(True, description="Whether to include source citations")
    max_context_chunks: int = Field(5, ge=1, le=20, description="Max document chunks to use for context")
    similarity_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity for context retrieval")
    stream: bool = Field(False, description="Whether to stream the response (SSE)")


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    conversation_id: UUID
    message: MessageResponse
    is_new_conversation: bool = Field(False, description="Whether a new conversation was created")


class ChatStreamChunk(BaseModel):
    """Single chunk of streamed chat response"""
    type: str = Field(..., pattern="^(content|source|done|error)$", description="Chunk type")
    content: Optional[str] = Field(None, description="Text content (for type='content')")
    source: Optional[MessageSource] = Field(None, description="Source citation (for type='source')")
    message_id: Optional[UUID] = Field(None, description="Final message ID (for type='done')")
    error: Optional[str] = Field(None, description="Error message (for type='error')")
