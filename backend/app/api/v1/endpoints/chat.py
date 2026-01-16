# app/api/v1/endpoints/chat.py - Chat endpoints with Claude integration

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.models import User
from app.schemas.chat import (
    ChatRequest, ChatResponse,
    ConversationResponse, ConversationUpdate, ConversationWithMessages,
    ConversationListResponse, MessageFeedback, LinkMatterRequest,
    HelpRequest, HelpResponse
)
from app.schemas.feedback import (
    EnhancedMessageFeedback, FeedbackResponse, InteractionSignal,
    SignalTrackingResponse
)
from app.services.chat_service import ChatService
from app.services.feedback_analytics import FeedbackAnalyticsService
from app.services.usage_tracker import UsageTracker
from app.core.rate_limit import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
@limiter.limit(get_rate_limit("chat_message"))
async def send_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get AI response with RAG context.

    This endpoint:
    1. Creates a new conversation or uses existing one
    2. Retrieves relevant document context using semantic search
    3. Calls Claude API with context and conversation history
    4. Returns the assistant's response with citations

    **Rate limit**: 60 messages per minute
    """
    try:
        chat_service = ChatService(db)
        response = await chat_service.send_message(chat_request, current_user)

        # Track AI query usage
        usage_tracker = UsageTracker(db)
        await usage_tracker.increment_ai_query_count(current_user.company_id)

        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.post("/stream")
@limiter.limit(get_rate_limit("chat_stream"))
async def send_message_stream(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and stream the AI response using Server-Sent Events (SSE).

    This endpoint streams the response in real-time as Claude generates it.
    The stream yields the following event types:
    - `content`: Text chunks as they're generated
    - `source`: Source citations after response is complete
    - `done`: Final event with message ID
    - `error`: If an error occurs

    **Rate limit**: 60 messages per minute

    **Example client usage**:
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'content') {
            console.log(data.content);
        } else if (data.type === 'done') {
            console.log('Message ID:', data.message_id);
            eventSource.close();
        }
    };
    ```
    """
    try:
        # Track AI query usage upfront (before streaming starts)
        # This ensures the count is incremented even if streaming is interrupted
        usage_tracker = UsageTracker(db)
        await usage_tracker.increment_ai_query_count(current_user.company_id)

        chat_service = ChatService(db)
        return StreamingResponse(
            chat_service.send_message_stream(chat_request, current_user),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in send_message_stream: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stream message: {str(e)}")


@router.get("/conversations", response_model=ConversationListResponse)
@limiter.limit(get_rate_limit("chat_list"))
async def list_conversations(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_archived: bool = Query(False, description="Include archived conversations"),
    matter_id: Optional[UUID] = Query(None, description="Filter by matter ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's conversations with pagination.

    Conversations are ordered by:
    1. Pinned conversations first
    2. Most recently updated

    **Rate limit**: 120 requests per minute
    """
    try:
        chat_service = ChatService(db)
        conversations = await chat_service.list_conversations(
            user_id=current_user.id,
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            include_archived=include_archived,
            matter_id=matter_id
        )
        return conversations
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/conversations/search", response_model=ConversationListResponse)
@limiter.limit(get_rate_limit("chat_list"))
async def search_conversations(
    request: Request,
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search conversations by title and summary using full-text search.

    This endpoint searches across conversation titles and AI-generated summaries.
    Summaries are lazily generated when conversations are first searched.

    **Rate limit**: 120 requests per minute
    """
    try:
        chat_service = ChatService(db)
        conversations = await chat_service.search_conversations(
            user_id=current_user.id,
            company_id=current_user.company_id,
            query=q,
            page=page,
            page_size=page_size
        )
        return conversations
    except Exception as e:
        logger.error(f"Error searching conversations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search conversations: {str(e)}")


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
@limiter.limit(get_rate_limit("chat_get"))
async def get_conversation(
    request: Request,
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a conversation with its full message history.

    **Rate limit**: 120 requests per minute
    """
    try:
        chat_service = ChatService(db)
        conversation = await chat_service.get_conversation_with_messages(
            conversation_id=conversation_id,
            current_user=current_user
        )
        return conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
@limiter.limit(get_rate_limit("chat_update"))
async def update_conversation(
    request: Request,
    conversation_id: UUID,
    updates: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a conversation (title, pin status, archive status).

    **Rate limit**: 120 requests per minute
    """
    try:
        chat_service = ChatService(db)
        conversation = await chat_service.update_conversation(
            conversation_id=conversation_id,
            updates=updates,
            current_user=current_user
        )
        return ConversationResponse.model_validate(conversation)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update conversation: {str(e)}")


@router.delete("/conversations/{conversation_id}", status_code=204)
@limiter.limit(get_rate_limit("chat_delete"))
async def delete_conversation(
    request: Request,
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a conversation and all its messages.

    This operation is permanent and cannot be undone.

    **Rate limit**: 120 requests per minute
    """
    try:
        chat_service = ChatService(db)
        await chat_service.delete_conversation(
            conversation_id=conversation_id,
            current_user=current_user
        )
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


@router.post("/conversations/{conversation_id}/link-matter")
@limiter.limit(get_rate_limit("chat_update"))
async def link_conversation_to_matter(
    request: Request,
    conversation_id: UUID,
    link_request: LinkMatterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Link a Discovery mode conversation to a matter.

    This allows users to associate a general conversation with a specific matter
    after the AI suggests it may be related. Future messages in this conversation
    will use RAG context from the linked matter's documents.

    **Rate limit**: 120 requests per minute
    """
    try:
        chat_service = ChatService(db)
        conversation = await chat_service.link_to_matter(
            conversation_id=conversation_id,
            matter_id=link_request.matter_id,
            current_user=current_user
        )

        # Get matter name for response
        from sqlalchemy import select
        from app.models.models import Claim as MatterModel
        matter_query = select(MatterModel.company_name, MatterModel.claim_number).where(
            MatterModel.id == link_request.matter_id
        )
        result = await db.execute(matter_query)
        matter = result.first()
        matter_name = f"{matter.claim_number} - {matter.company_name}" if matter else None

        return {
            "success": True,
            "conversation_id": str(conversation.id),
            "matter_id": str(link_request.matter_id),
            "matter_name": matter_name
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error linking conversation to matter: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to link conversation: {str(e)}")


@router.post("/messages/{message_id}/feedback", response_model=FeedbackResponse)
@limiter.limit(get_rate_limit("chat_feedback"))
async def submit_message_feedback(
    request: Request,
    message_id: UUID,
    feedback: EnhancedMessageFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit rating and feedback for a message.

    **Rating values**:
    - `-1`: Thumbs down
    - `1`: Thumbs up

    **Feedback categories** (for negative feedback):
    - `incorrect`: Answer was factually incorrect
    - `irrelevant`: Answer wasn't relevant to my question
    - `wrong_question`: I asked the wrong question
    - `not_detailed`: Not enough detail provided
    - `no_documents`: Couldn't find relevant documents

    **Rate limit**: 120 requests per minute
    """
    try:
        feedback_service = FeedbackAnalyticsService(db)
        result = await feedback_service.submit_feedback(
            message_id=message_id,
            feedback=feedback,
            current_user=current_user
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@router.post("/signals/track", response_model=SignalTrackingResponse, status_code=202)
@limiter.limit(get_rate_limit("default"))
async def track_interaction_signal(
    request: Request,
    signal: InteractionSignal,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Track implicit interaction signals from frontend for quality analytics.

    **Signal types**:
    - `session_start`: User started a chat session
    - `session_end`: User left the chat
    - `copy`: User copied response text
    - `source_click`: User clicked a cited source

    These signals help us understand response quality beyond explicit feedback.

    **Rate limit**: 120 requests per minute
    """
    try:
        feedback_service = FeedbackAnalyticsService(db)

        if signal.signal_type.value == "session_start":
            await feedback_service.track_session_start(signal.conversation_id, current_user)
        elif signal.signal_type.value == "session_end":
            await feedback_service.track_session_end(signal.conversation_id, current_user)
        elif signal.signal_type.value == "copy":
            if signal.message_id:
                await feedback_service.track_copy_event(
                    signal.conversation_id, signal.message_id, current_user
                )
        elif signal.signal_type.value == "source_click":
            if signal.message_id and signal.document_id:
                await feedback_service.track_source_click(
                    signal.conversation_id, signal.message_id, signal.document_id, current_user
                )

        return SignalTrackingResponse(status="accepted", signal_type=signal.signal_type.value)
    except Exception as e:
        logger.error(f"Error tracking signal: {str(e)}", exc_info=True)
        # Don't fail on tracking errors - just log
        return SignalTrackingResponse(status="accepted", signal_type=signal.signal_type.value)


@router.post("/help", response_model=HelpResponse)
@limiter.limit(get_rate_limit("chat_message"))
async def send_help_message(
    request: Request,
    help_request: HelpRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Platform help chat - answers questions about using SR&ED Intelligence.

    This endpoint provides quick answers about platform features and usage.
    It does NOT search documents or provide SR&ED advice.

    **Use cases**:
    - "How do I upload a document?"
    - "What is a claim?"
    - "How do I track consulting hours?"

    **Rate limit**: 60 requests per minute
    """
    from anthropic import AsyncAnthropic
    from app.core.config import settings

    try:
        anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        response = await anthropic.messages.create(
            model="claude-3-5-haiku-20241022",  # Use faster/cheaper model for help
            max_tokens=500,
            system="""You are a helpful assistant for SR&ED Intelligence, an AI-powered platform that helps PwC consultants analyze SR&ED (Scientific Research and Experimental Development) tax credit claims.

Answer questions about using the platform:
- **Documents**: Upload PDF/DOCX/TXT files, organize by claim, search content with hybrid semantic/keyword search
- **Claims**: SR&ED claims for client companies, each with fiscal year, projects, documents, and team access
- **Chat**: AI assistant that searches your documents (select a claim first for document search, or use AI Discovery for general SR&ED questions)
- **T661 Drafting**: Generate draft responses for CRA T661 form sections with word count tracking
- **Eligibility Reports**: AI-generated SR&ED eligibility assessments based on CRA's five-question test
- **Consulting Hours**: Track time spent on conversations, generate descriptions for billing
- **Timeline**: View R&D events and milestones extracted from documents chronologically
- **Daily Briefings**: AI-generated summaries of recent activity

Keep answers concise (2-3 sentences). If asked about specific SR&ED claim details (not platform usage), politely redirect them to use the main Chat feature with a claim selected.

Do NOT provide specific SR&ED tax advice. You are only here to help with platform usage.""",
            messages=[{"role": "user", "content": help_request.message}]
        )

        return HelpResponse(content=response.content[0].text)

    except Exception as e:
        logger.error(f"Help chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to process help request. Please try again."
        )
