# app/services/chat_service.py - Chat service with Claude integration

import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
from uuid import UUID
from datetime import datetime

from anthropic import Anthropic, AsyncAnthropic
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Conversation, Message, User
from app.schemas.chat import (
    ChatRequest, ChatResponse, MessageResponse, MessageSource,
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationWithMessages, ConversationListResponse, MessageFeedback
)
from app.services.embeddings import embedding_service
from app.services.vector_storage import vector_storage_service

logger = logging.getLogger(__name__)


class ChatService:
    """Service for AI chat with RAG context"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def send_message(
        self,
        request: ChatRequest,
        current_user: User
    ) -> ChatResponse:
        """
        Send a message and get AI response with RAG context.

        Args:
            request: Chat request with message and settings
            current_user: Current authenticated user

        Returns:
            Chat response with assistant message and citations
        """
        # 1. Get or create conversation
        if request.conversation_id:
            conversation = await self._get_conversation(request.conversation_id, current_user)
            is_new_conversation = False
        else:
            conversation = await self._create_conversation(
                user=current_user,
                matter_id=request.matter_id,
                first_message=request.message
            )
            is_new_conversation = True

        # 2. Save user message
        user_message = await self._save_message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )

        # 3. Retrieve relevant context using RAG
        context_chunks, sources = await self._retrieve_context(
            query=request.message,
            matter_id=conversation.matter_id,
            max_chunks=request.max_context_chunks,
            similarity_threshold=request.similarity_threshold,
            user=current_user
        )

        # 4. Build prompt with context
        system_prompt = self._build_system_prompt(context_chunks)

        # 5. Get conversation history
        history = await self._get_conversation_history(conversation.id, limit=10)

        # 6. Call Claude API
        try:
            assistant_content, usage = await self._call_claude(
                system_prompt=system_prompt,
                user_message=request.message,
                conversation_history=history
            )
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate response: {str(e)}")

        # 7. Save assistant message with sources
        assistant_message = await self._save_message(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_content,
            sources=sources if request.include_sources else None,
            model_name=settings.ANTHROPIC_MODEL,
            token_count=usage.get("output_tokens"),
            context_chunks=[{
                "chunk_id": str(chunk["chunk_id"]),
                "similarity": chunk["similarity"]
            } for chunk in context_chunks]
        )

        # 8. Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        await self.db.commit()

        # 9. Return response
        return ChatResponse(
            conversation_id=conversation.id,
            message=MessageResponse.model_validate(assistant_message),
            is_new_conversation=is_new_conversation
        )

    async def send_message_stream(
        self,
        request: ChatRequest,
        current_user: User
    ) -> AsyncGenerator[str, None]:
        """
        Send message and stream response using Server-Sent Events.

        Yields SSE-formatted chunks.
        """
        # 1. Get or create conversation
        if request.conversation_id:
            conversation = await self._get_conversation(request.conversation_id, current_user)
        else:
            conversation = await self._create_conversation(
                user=current_user,
                matter_id=request.matter_id,
                first_message=request.message
            )

        # 2. Save user message
        user_message = await self._save_message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )

        # 3. Retrieve context
        context_chunks, sources = await self._retrieve_context(
            query=request.message,
            matter_id=conversation.matter_id,
            max_chunks=request.max_context_chunks,
            similarity_threshold=request.similarity_threshold,
            user=current_user
        )

        # 4. Build prompt and get history
        system_prompt = self._build_system_prompt(context_chunks)
        history = await self._get_conversation_history(conversation.id, limit=10)

        # 5. Stream Claude response
        full_content = ""
        try:
            async with self.anthropic.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                system=system_prompt,
                messages=self._format_history_for_claude(history) + [
                    {"role": "user", "content": request.message}
                ]
            ) as stream:
                async for text in stream.text_stream:
                    full_content += text
                    # Yield SSE-formatted content chunk
                    yield f"data: {self._format_sse_chunk('content', text)}\n\n"

            # Get final message with usage
            final_message = await stream.get_final_message()
            usage = {
                "input_tokens": final_message.usage.input_tokens,
                "output_tokens": final_message.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}", exc_info=True)
            yield f"data: {self._format_sse_chunk('error', str(e))}\n\n"
            return

        # 6. Save assistant message
        assistant_message = await self._save_message(
            conversation_id=conversation.id,
            role="assistant",
            content=full_content,
            sources=sources if request.include_sources else None,
            model_name=settings.ANTHROPIC_MODEL,
            token_count=usage.get("output_tokens"),
            context_chunks=[{
                "chunk_id": str(chunk["chunk_id"]),
                "similarity": chunk["similarity"]
            } for chunk in context_chunks]
        )

        # 7. Send sources
        if request.include_sources and sources:
            for source in sources:
                yield f"data: {self._format_sse_chunk('source', source.model_dump(mode='json'))}\n\n"

        # 8. Send done signal with message ID and conversation ID
        yield f"data: {self._format_sse_chunk('done', {'message_id': str(assistant_message.id), 'conversation_id': str(conversation.id)})}\n\n"

    async def get_conversation_with_messages(
        self,
        conversation_id: UUID,
        current_user: User
    ) -> ConversationWithMessages:
        """Get conversation with full message history"""
        conversation = await self._get_conversation(conversation_id, current_user)

        # Load messages
        messages_query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)

        result = await self.db.execute(messages_query)
        messages = result.scalars().all()

        return ConversationWithMessages(
            **conversation.__dict__,
            messages=[MessageResponse.model_validate(m) for m in messages]
        )

    async def list_conversations(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_archived: bool = False
    ) -> ConversationListResponse:
        """List user's conversations with pagination"""
        # Build query
        query = select(Conversation).where(Conversation.user_id == user_id)

        if not include_archived:
            query = query.where(Conversation.is_archived == False)

        query = query.order_by(
            Conversation.is_pinned.desc(),
            Conversation.updated_at.desc()
        )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        conversations = result.scalars().all()

        # Enrich with message count and preview
        enriched = []
        for conv in conversations:
            # Get message count
            msg_count_query = select(func.count()).where(Message.conversation_id == conv.id)
            msg_count_result = await self.db.execute(msg_count_query)
            message_count = msg_count_result.scalar() or 0

            # Get last message preview
            last_msg_query = select(Message).where(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at.desc()).limit(1)
            last_msg_result = await self.db.execute(last_msg_query)
            last_msg = last_msg_result.scalar()

            preview = None
            if last_msg:
                preview = last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content

            enriched.append(ConversationResponse(
                **conv.__dict__,
                message_count=message_count,
                last_message_preview=preview
            ))

        return ConversationListResponse(
            conversations=enriched,
            total=total,
            page=page,
            page_size=page_size
        )

    async def update_conversation(
        self,
        conversation_id: UUID,
        updates: ConversationUpdate,
        current_user: User
    ) -> Conversation:
        """Update conversation (title, pin, archive)"""
        conversation = await self._get_conversation(conversation_id, current_user)

        if updates.title is not None:
            conversation.title = updates.title
        if updates.is_pinned is not None:
            conversation.is_pinned = updates.is_pinned
        if updates.is_archived is not None:
            conversation.is_archived = updates.is_archived

        conversation.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def delete_conversation(
        self,
        conversation_id: UUID,
        current_user: User
    ) -> None:
        """Delete conversation and all messages"""
        conversation = await self._get_conversation(conversation_id, current_user)
        await self.db.delete(conversation)
        await self.db.commit()

    async def submit_feedback(
        self,
        message_id: UUID,
        feedback: MessageFeedback,
        current_user: User
    ) -> Message:
        """Submit rating/feedback for a message"""
        # Get message and verify access
        message_query = select(Message).join(Conversation).where(
            and_(
                Message.id == message_id,
                Conversation.user_id == current_user.id
            )
        )
        result = await self.db.execute(message_query)
        message = result.scalar()

        if not message:
            raise ValueError("Message not found or access denied")

        message.rating = feedback.rating
        message.feedback_text = feedback.feedback_text

        await self.db.commit()
        await self.db.refresh(message)

        return message

    # Helper methods

    async def _get_conversation(self, conversation_id: UUID, user: User) -> Conversation:
        """Get conversation and verify access"""
        query = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            )
        )
        result = await self.db.execute(query)
        conversation = result.scalar()

        if not conversation:
            raise ValueError("Conversation not found or access denied")

        return conversation

    async def _create_conversation(
        self,
        user: User,
        matter_id: Optional[UUID],
        first_message: str
    ) -> Conversation:
        """Create new conversation with auto-generated title"""
        # Generate title from first message (first 50 chars)
        title = first_message[:50] + "..." if len(first_message) > 50 else first_message

        conversation = Conversation(
            company_id=user.company_id,
            user_id=user.id,
            matter_id=matter_id,
            title=title
        )

        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def _save_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        sources: Optional[List[MessageSource]] = None,
        model_name: Optional[str] = None,
        token_count: Optional[int] = None,
        context_chunks: Optional[List[Dict]] = None
    ) -> Message:
        """Save message to database"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=[s.model_dump(mode='json') for s in sources] if sources else None,
            model_name=model_name,
            token_count=token_count,
            context_chunks=context_chunks
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def _retrieve_context(
        self,
        query: str,
        matter_id: Optional[UUID],
        max_chunks: int,
        similarity_threshold: float,
        user: User
    ) -> tuple[List[Dict], List[MessageSource]]:
        """
        Retrieve relevant document chunks using semantic search.

        Returns:
            (context_chunks, message_sources)
        """
        # Generate query embedding
        query_embedding = embedding_service.generate_embedding(query)

        if not query_embedding:
            logger.warning("Failed to generate query embedding, proceeding without context")
            return [], []

        # Perform vector similarity search
        search_results = await vector_storage_service.similarity_search(
            query_embedding=query_embedding,
            matter_id=matter_id,
            limit=max_chunks,
            similarity_threshold=similarity_threshold
        )

        # Convert to message sources
        sources = []
        for result in search_results:
            # Get document metadata (already filtered by company_id in vector_storage)
            from app.models.models import Document, Matter
            doc_query = select(Document, Matter).join(Matter).where(
                and_(
                    Document.id == result["document_id"],
                    Matter.company_id == user.company_id
                )
            )
            doc_result = await self.db.execute(doc_query)
            doc_matter = doc_result.first()

            if doc_matter:
                doc, matter = doc_matter
                sources.append(MessageSource(
                    document_id=result["document_id"],
                    document_title=doc.document_title or doc.filename,
                    chunk_id=result["chunk_id"],
                    content=result["content"],
                    page_number=result.get("page_number"),
                    similarity_score=result["similarity"],
                    matter_id=matter.id,
                    matter_name=f"{matter.matter_number} - {matter.client_name}"
                ))

        return search_results, sources

    def _build_system_prompt(self, context_chunks: List[Dict]) -> str:
        """Build system prompt with document context"""
        if not context_chunks:
            return """You are a legal AI assistant for BC Legal Tech, helping lawyers analyze their documents.

Important guidelines:
- Always cite your sources when referencing specific information
- If you don't have relevant information, say "I don't have information about that in the provided documents"
- Be concise and professional
- For legal advice, remind users to verify with qualified counsel
- Stick to the facts in the documents"""

        # Build context section
        context_text = ""
        for i, chunk in enumerate(context_chunks, 1):
            context_text += f"\n[Source {i}]\n{chunk['content']}\n"

        return f"""You are a legal AI assistant for BC Legal Tech, helping lawyers analyze their documents.

You have access to the following relevant document excerpts:

<context>
{context_text}
</context>

Important guidelines:
- Always cite your sources using [Source X] notation when referencing information
- Only use information from the provided context
- If the context doesn't contain relevant information, say "I don't have information about that in the provided documents"
- Be concise and professional
- For legal advice, remind users to verify with qualified counsel
- Stick to the facts in the documents"""

    async def _get_conversation_history(
        self,
        conversation_id: UUID,
        limit: int = 10
    ) -> List[Message]:
        """Get recent conversation history"""
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        return list(reversed(messages))  # Return in chronological order

    def _format_history_for_claude(self, history: List[Message]) -> List[Dict]:
        """Format message history for Claude API"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in history
            if msg.role in ("user", "assistant")
        ]

    async def _call_claude(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Message]
    ) -> tuple[str, Dict]:
        """
        Call Claude API.

        Returns:
            (response_content, usage_dict)
        """
        messages = self._format_history_for_claude(conversation_history) + [
            {"role": "user", "content": user_message}
        ]

        response = await self.anthropic.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            system=system_prompt,
            messages=messages
        )

        content = response.content[0].text
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }

        return content, usage

    def _format_sse_chunk(self, chunk_type: str, data: Any) -> str:
        """Format chunk as JSON for SSE"""
        import json
        # Merge data into the top level along with type
        if isinstance(data, dict):
            return json.dumps({"type": chunk_type, **data})
        else:
            return json.dumps({"type": chunk_type, chunk_type: data})
