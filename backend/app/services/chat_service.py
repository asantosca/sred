# app/services/chat_service.py - Chat service with Claude integration

import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
from uuid import UUID
from datetime import datetime

from anthropic import Anthropic, AsyncAnthropic
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Conversation, Message, User, Matter
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

        # 2. Get conversation history BEFORE saving new message
        history = await self._get_conversation_history(conversation.id, limit=10)

        # 3. Save user message
        user_message = await self._save_message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )

        # 4. Retrieve relevant context using RAG
        context_chunks, sources = await self._retrieve_context(
            query=request.message,
            matter_id=conversation.matter_id,
            max_chunks=request.max_context_chunks,
            similarity_threshold=request.similarity_threshold,
            user=current_user
        )

        # 5. Build prompt with context
        is_discovery_mode = conversation.matter_id is None
        system_prompt = self._build_system_prompt(context_chunks, is_discovery_mode)

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

        # 2. Get conversation history BEFORE saving new message
        history = await self._get_conversation_history(conversation.id, limit=10)
        logger.info(f"[stream] Fetched {len(history)} messages from history for conversation {conversation.id}")

        # 3. Save user message
        user_message = await self._save_message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )

        # 4. Retrieve context
        context_chunks, sources = await self._retrieve_context(
            query=request.message,
            matter_id=conversation.matter_id,
            max_chunks=request.max_context_chunks,
            similarity_threshold=request.similarity_threshold,
            user=current_user
        )

        # 5. Build prompt
        is_discovery_mode = conversation.matter_id is None
        system_prompt = self._build_system_prompt(context_chunks, is_discovery_mode)

        # 6. Stream Claude response
        full_content = ""
        formatted_messages = self._format_history_for_claude(history) + [
            {"role": "user", "content": request.message}
        ]
        logger.info(f"Sending {len(formatted_messages)} messages to Claude:")
        for i, msg in enumerate(formatted_messages):
            logger.info(f"  [{i}] {msg['role']}: {msg['content'][:100]}...")

        try:
            async with self.anthropic.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                system=system_prompt,
                messages=formatted_messages
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

        # 8. In Discovery mode, check if query relates to any matter
        if is_discovery_mode:
            suggested_matter = await self._detect_related_matter(
                query=request.message,
                user=current_user,
                threshold=0.7
            )
            if suggested_matter:
                yield f"data: {self._format_sse_chunk('matter_suggestion', suggested_matter)}\n\n"

        # 9. Send done signal with message ID and conversation ID
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

        # Get matter name if matter_id exists
        matter_name = None
        if conversation.matter_id:
            matter_query = select(Matter.client_name).where(Matter.id == conversation.matter_id)
            matter_result = await self.db.execute(matter_query)
            matter_name = matter_result.scalar()

        return ConversationWithMessages(
            **conversation.__dict__,
            messages=[MessageResponse.model_validate(m) for m in messages],
            matter_name=matter_name
        )

    async def list_conversations(
        self,
        user_id: UUID,
        company_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_archived: bool = False,
        matter_id: Optional[UUID] = None
    ) -> ConversationListResponse:
        """List user's conversations with pagination and tenant isolation"""
        # Build query with tenant isolation
        query = select(Conversation).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.company_id == company_id  # Tenant isolation
            )
        )

        if not include_archived:
            query = query.where(Conversation.is_archived == False)

        # Filter by matter if specified
        if matter_id:
            query = query.where(Conversation.matter_id == matter_id)

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

        # Enrich with message count, preview, and matter name
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

            # Get matter name if matter_id exists
            matter_name = None
            if conv.matter_id:
                matter_query = select(Matter.client_name).where(Matter.id == conv.matter_id)
                matter_result = await self.db.execute(matter_query)
                matter_name = matter_result.scalar()

            enriched.append(ConversationResponse(
                **conv.__dict__,
                message_count=message_count,
                last_message_preview=preview,
                matter_name=matter_name
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

    async def search_conversations(
        self,
        user_id: UUID,
        company_id: UUID,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> ConversationListResponse:
        """
        Search conversations using full-text search on summaries and titles.
        Generates summaries lazily for conversations that don't have them.
        """
        from sqlalchemy import text

        # First, generate summaries for conversations without them (up to 5 at a time)
        await self._generate_missing_summaries(user_id, company_id, limit=5)

        # Full-text search query with tenant isolation
        search_query = select(Conversation).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.company_id == company_id,  # Tenant isolation
                text("""
                    to_tsvector('english', COALESCE(summary, '') || ' ' || COALESCE(title, ''))
                    @@ plainto_tsquery('english', :query)
                """)
            )
        ).params(query=query).order_by(Conversation.updated_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(search_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        search_query = search_query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(search_query)
        conversations = result.scalars().all()

        # Enrich with message count and preview (reuse existing logic)
        enriched = []
        for conv in conversations:
            msg_count_query = select(func.count()).where(Message.conversation_id == conv.id)
            msg_count_result = await self.db.execute(msg_count_query)
            message_count = msg_count_result.scalar() or 0

            last_msg_query = select(Message).where(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at.desc()).limit(1)
            last_msg_result = await self.db.execute(last_msg_query)
            last_msg = last_msg_result.scalar()

            preview = None
            if last_msg:
                preview = last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content

            matter_name = None
            if conv.matter_id:
                matter_query = select(Matter.client_name).where(Matter.id == conv.matter_id)
                matter_result = await self.db.execute(matter_query)
                matter_name = matter_result.scalar()

            enriched.append(ConversationResponse(
                **conv.__dict__,
                message_count=message_count,
                last_message_preview=preview,
                matter_name=matter_name
            ))

        return ConversationListResponse(
            conversations=enriched,
            total=total,
            page=page,
            page_size=page_size
        )

    async def _generate_missing_summaries(self, user_id: UUID, company_id: UUID, limit: int = 5) -> None:
        """Generate summaries for conversations that don't have them (lazy generation)."""
        # Find conversations without summaries that have messages (with tenant isolation)
        query = select(Conversation).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.company_id == company_id,  # Tenant isolation
                Conversation.summary.is_(None)
            )
        ).order_by(Conversation.updated_at.desc()).limit(limit)

        result = await self.db.execute(query)
        conversations = result.scalars().all()

        for conv in conversations:
            await self._generate_summary(conv)

    async def _generate_summary(self, conversation: Conversation) -> str:
        """Generate AI summary for a conversation."""
        from datetime import datetime, timezone

        # Get messages for this conversation
        msg_query = select(Message).where(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at).limit(20)  # Limit to first 20 messages
        msg_result = await self.db.execute(msg_query)
        messages = msg_result.scalars().all()

        if not messages:
            return ""

        # Build conversation text for summarization
        conversation_text = "\n".join([
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content[:500]}"
            for m in messages
        ])

        prompt = f"""Summarize this legal research conversation in 2-3 sentences. Focus on:
1. The main legal question or topic discussed
2. Key documents or cases referenced
3. The conclusion or outcome (if any)

Keep it concise and searchable - use specific legal terms and names mentioned.

Conversation:
{conversation_text}

Summary:"""

        try:
            response = await self.anthropic.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            summary = response.content[0].text.strip()

            # Save summary to conversation
            conversation.summary = summary
            conversation.summary_generated_at = datetime.now(timezone.utc)
            await self.db.commit()

            return summary
        except Exception as e:
            logger.error(f"Failed to generate summary for conversation {conversation.id}: {e}")
            return ""

    async def submit_feedback(
        self,
        message_id: UUID,
        feedback: MessageFeedback,
        current_user: User
    ) -> Message:
        """Submit rating/feedback for a message with tenant isolation"""
        # Get message and verify access with tenant isolation
        message_query = select(Message).join(Conversation).where(
            and_(
                Message.id == message_id,
                Conversation.user_id == current_user.id,
                Conversation.company_id == current_user.company_id  # Tenant isolation
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

    async def _detect_related_matter(
        self,
        query: str,
        user: User,
        threshold: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        Check if the user's query semantically matches documents in any matter.
        Used in Discovery mode to suggest linking the conversation to a matter.

        Returns:
            Dict with matter_id, matter_name, similarity, matched_document if found,
            None otherwise.
        """
        # Generate query embedding
        query_embedding = embedding_service.generate_embedding(query)
        if not query_embedding:
            return None

        # Search across ALL user's matters (no matter_id filter)
        try:
            results = await vector_storage_service.similarity_search(
                query_embedding=query_embedding,
                company_id=user.company_id,
                matter_id=None,  # Search all matters
                limit=3,
                similarity_threshold=threshold
            )
        except Exception as e:
            logger.warning(f"Matter detection search failed: {e}")
            return None

        if not results:
            return None

        # Get the matter with highest similarity
        top_result = results[0]

        # Fetch document and matter info
        from app.models.models import Document
        doc_query = select(Document, Matter).join(Matter).where(
            and_(
                Document.id == top_result["document_id"],
                Matter.company_id == user.company_id
            )
        )
        doc_result = await self.db.execute(doc_query)
        doc_matter = doc_result.first()

        if doc_matter:
            doc, matter = doc_matter
            return {
                "matter_id": str(matter.id),
                "matter_name": f"{matter.matter_number} - {matter.client_name}",
                "similarity": top_result["similarity"],
                "matched_document": doc.document_title or doc.filename
            }

        return None

    async def link_to_matter(
        self,
        conversation_id: UUID,
        matter_id: UUID,
        current_user: User
    ) -> Conversation:
        """Link a Discovery mode conversation to a matter."""
        conversation = await self._get_conversation(conversation_id, current_user)

        # Verify user has access to the matter
        matter_query = select(Matter).where(
            and_(
                Matter.id == matter_id,
                Matter.company_id == current_user.company_id
            )
        )
        matter_result = await self.db.execute(matter_query)
        matter = matter_result.scalar()

        if not matter:
            raise ValueError("Matter not found or access denied")

        # Update conversation
        conversation.matter_id = matter_id

        # Update title to include matter name if not already
        if not conversation.title.startswith("["):
            conversation.title = f"[{matter.client_name}] {conversation.title}"

        conversation.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def _get_conversation(self, conversation_id: UUID, user: User) -> Conversation:
        """Get conversation and verify access with tenant isolation"""
        query = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
                Conversation.company_id == user.company_id  # Tenant isolation
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
        message_title = first_message[:50] + "..." if len(first_message) > 50 else first_message

        # Prepend matter name if available
        title = message_title
        if matter_id:
            matter_query = select(Matter).where(Matter.id == matter_id)
            matter_result = await self.db.execute(matter_query)
            matter = matter_result.scalar()
            if matter:
                title = f"[{matter.client_name}] {message_title}"

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

        # Invalidate summary when new messages are added (will be regenerated lazily)
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if conversation and conversation.summary is not None:
            conversation.summary = None
            conversation.summary_generated_at = None

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

        In Discovery mode (matter_id is None), no RAG context is retrieved.

        Returns:
            (context_chunks, message_sources)
        """
        # Discovery mode - no RAG, just general AI assistance
        if matter_id is None:
            logger.info("Discovery mode: skipping RAG retrieval")
            return [], []

        # Generate query embedding
        query_embedding = embedding_service.generate_embedding(query)

        if not query_embedding:
            logger.warning("Failed to generate query embedding, proceeding without context")
            return [], []

        # Perform vector similarity search (filtered by company_id at database level)
        search_results = await vector_storage_service.similarity_search(
            query_embedding=query_embedding,
            company_id=user.company_id,
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
                    Matter.company_id == user.company_id  # Belt-and-suspenders check
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

    def _build_system_prompt(self, context_chunks: List[Dict], is_discovery_mode: bool = False) -> str:
        """Build system prompt with document context"""
        if is_discovery_mode:
            return """You are a legal AI assistant for BC Legal Tech, operating in Discovery mode.

In Discovery mode, you answer general legal questions using your knowledge - you do NOT have access to the user's documents.

Guidelines:
- Answer general legal questions, especially about BC (British Columbia) law
- Help with legal procedures, terminology, concepts, and general guidance
- If the user asks about specific documents, contracts, or cases they're working on, suggest they select a matter to search their documents
- Be concise and professional
- Always remind users to verify with qualified legal counsel for specific legal advice
- You can discuss general legal principles without needing document context"""

        if not context_chunks:
            return """You are a legal AI assistant for BC Legal Tech, helping lawyers analyze their documents.

Important guidelines:
- Always cite your sources when referencing specific document information
- You may reference information the user has shared directly in the conversation
- If asked about something not in any documents or the conversation, say "I don't have information about that"
- Be concise and professional
- For legal advice, remind users to verify with qualified counsel"""

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
- Always cite your sources using [Source X] notation when referencing document information
- For document-related questions, use information from the provided context
- You may also reference information the user has shared directly in the conversation
- If asked about something not in the documents or conversation, say "I don't have information about that"
- Be concise and professional
- For legal advice, remind users to verify with qualified counsel"""

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
