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
    ConversationListResponse, MessageFeedback
)
from app.services.chat_service import ChatService
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
            page=page,
            page_size=page_size,
            include_archived=include_archived
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


@router.post("/messages/{message_id}/feedback", response_model=None)
@limiter.limit(get_rate_limit("chat_feedback"))
async def submit_message_feedback(
    request: Request,
    message_id: UUID,
    feedback: MessageFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit rating and feedback for a message.

    **Rating values**:
    - `-1`: Thumbs down
    - `1`: Thumbs up
    - `1-5`: Star rating (1 = poor, 5 = excellent)

    **Rate limit**: 120 requests per minute
    """
    try:
        chat_service = ChatService(db)
        await chat_service.submit_feedback(
            message_id=message_id,
            feedback=feedback,
            current_user=current_user
        )
        return {"status": "success", "message": "Feedback submitted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")
