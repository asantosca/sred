# app/services/billable_service.py - Service for billable hours tracking

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from anthropic import AsyncAnthropic
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import (
    BillableSession, Conversation, Message, Matter, User
)
from app.schemas.billable import (
    BillableSessionCreate, BillableSessionUpdate, BillableSessionResponse,
    BillableSessionListResponse
)

logger = logging.getLogger(__name__)


class BillableService:
    """Service for billable hours tracking and AI description generation"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def create_session_from_conversation(
        self,
        conversation_id: UUID,
        current_user: User,
        generate_description: bool = True
    ) -> BillableSession:
        """
        Create a billable session from a conversation.

        Calculates duration from message timestamps and optionally
        generates an AI description of the work performed.
        """
        # Get the conversation with tenant isolation
        conv_result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.user_id == current_user.id,
                    Conversation.company_id == current_user.company_id  # Tenant isolation
                )
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise ValueError("Conversation not found")

        # Get messages to calculate timing
        msg_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()

        if not messages:
            raise ValueError("Conversation has no messages")

        # Calculate timing from messages
        started_at = messages[0].created_at
        ended_at = messages[-1].created_at

        # Calculate duration (minimum 1 minute)
        duration_seconds = (ended_at - started_at).total_seconds()
        duration_minutes = max(1, int(duration_seconds / 60))

        # Generate AI description if requested
        ai_description = None
        if generate_description:
            ai_description = await self._generate_description(messages)

        # Create the billable session
        session = BillableSession(
            company_id=current_user.company_id,
            user_id=current_user.id,
            conversation_id=conversation_id,
            matter_id=conversation.matter_id,
            started_at=started_at,
            ended_at=ended_at,
            duration_minutes=duration_minutes,
            ai_description=ai_description,
            is_billable=True,
            is_exported=False,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def _generate_description(self, messages: List[Message]) -> str:
        """Generate a professional billing description from conversation messages."""
        # Build conversation summary for the AI
        conversation_text = "\n".join([
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content[:500]}"
            for m in messages[:20]  # Limit to first 20 messages
        ])

        prompt = f"""Based on the following legal research conversation, generate a concise, professional billing description suitable for a legal invoice. The description should:

1. Be written in past tense, third person (e.g., "Conducted legal research...")
2. Summarize the key legal work performed
3. Be 1-2 sentences, typically 50-100 words
4. Sound professional and appropriate for client billing
5. Focus on the legal task, not the AI interaction

Conversation:
{conversation_text}

Generate ONLY the billing description, nothing else:"""

        try:
            response = await self.anthropic.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Failed to generate billing description: {e}")
            return "Legal research and analysis conducted via AI-assisted document review."

    async def regenerate_description(
        self,
        session_id: UUID,
        current_user: User
    ) -> str:
        """Regenerate the AI description for an existing session."""
        # Get the session with tenant isolation
        session_result = await self.db.execute(
            select(BillableSession).where(
                and_(
                    BillableSession.id == session_id,
                    BillableSession.user_id == current_user.id,
                    BillableSession.company_id == current_user.company_id  # Tenant isolation
                )
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        # Get conversation messages
        msg_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == session.conversation_id)
            .order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()

        # Regenerate description
        ai_description = await self._generate_description(messages)
        session.ai_description = ai_description
        await self.db.commit()

        return ai_description

    async def list_sessions(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        matter_id: Optional[UUID] = None,
        include_exported: bool = False,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> BillableSessionListResponse:
        """List billable sessions for the current user with tenant isolation."""
        # Build query with tenant isolation
        query = select(BillableSession).where(
            and_(
                BillableSession.user_id == current_user.id,
                BillableSession.company_id == current_user.company_id  # Tenant isolation
            )
        )

        if matter_id:
            query = query.where(BillableSession.matter_id == matter_id)

        if not include_exported:
            query = query.where(BillableSession.is_exported == False)

        if start_date:
            query = query.where(BillableSession.started_at >= start_date)

        if end_date:
            query = query.where(BillableSession.started_at <= end_date)

        query = query.order_by(BillableSession.started_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get total minutes
        minutes_query = select(func.sum(BillableSession.duration_minutes)).select_from(
            query.where(BillableSession.is_billable == True).subquery()
        )
        minutes_result = await self.db.execute(minutes_query)
        total_minutes = minutes_result.scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        sessions = result.scalars().all()

        # Enrich with related data
        enriched = []
        for session in sessions:
            # Get conversation title
            conv_result = await self.db.execute(
                select(Conversation.title).where(
                    Conversation.id == session.conversation_id
                )
            )
            conv_title = conv_result.scalar()

            # Get matter name if exists
            matter_name = None
            if session.matter_id:
                matter_result = await self.db.execute(
                    select(Matter.name).where(Matter.id == session.matter_id)
                )
                matter_name = matter_result.scalar()

            enriched.append(BillableSessionResponse(
                **{k: v for k, v in session.__dict__.items() if not k.startswith('_')},
                conversation_title=conv_title,
                matter_name=matter_name,
            ))

        return BillableSessionListResponse(
            sessions=enriched,
            total=total,
            page=page,
            page_size=page_size,
            total_minutes=total_minutes,
        )

    async def get_session(
        self,
        session_id: UUID,
        current_user: User
    ) -> BillableSessionResponse:
        """Get a single billable session with tenant isolation."""
        result = await self.db.execute(
            select(BillableSession).where(
                and_(
                    BillableSession.id == session_id,
                    BillableSession.user_id == current_user.id,
                    BillableSession.company_id == current_user.company_id  # Tenant isolation
                )
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        # Get conversation title
        conv_result = await self.db.execute(
            select(Conversation.title).where(
                Conversation.id == session.conversation_id
            )
        )
        conv_title = conv_result.scalar()

        # Get matter name if exists
        matter_name = None
        if session.matter_id:
            matter_result = await self.db.execute(
                select(Matter.name).where(Matter.id == session.matter_id)
            )
            matter_name = matter_result.scalar()

        return BillableSessionResponse(
            **{k: v for k, v in session.__dict__.items() if not k.startswith('_')},
            conversation_title=conv_title,
            matter_name=matter_name,
        )

    async def update_session(
        self,
        session_id: UUID,
        updates: BillableSessionUpdate,
        current_user: User
    ) -> BillableSession:
        """Update a billable session with tenant isolation."""
        result = await self.db.execute(
            select(BillableSession).where(
                and_(
                    BillableSession.id == session_id,
                    BillableSession.user_id == current_user.id,
                    BillableSession.company_id == current_user.company_id  # Tenant isolation
                )
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        if session.is_exported:
            raise ValueError("Cannot update an exported session")

        # Apply updates
        if updates.description is not None:
            session.description = updates.description
        if updates.duration_minutes is not None:
            session.duration_minutes = updates.duration_minutes
        if updates.activity_code is not None:
            session.activity_code = updates.activity_code
        if updates.is_billable is not None:
            session.is_billable = updates.is_billable
        if updates.matter_id is not None:
            session.matter_id = updates.matter_id

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete_session(
        self,
        session_id: UUID,
        current_user: User
    ) -> bool:
        """Delete a billable session with tenant isolation."""
        result = await self.db.execute(
            select(BillableSession).where(
                and_(
                    BillableSession.id == session_id,
                    BillableSession.user_id == current_user.id,
                    BillableSession.company_id == current_user.company_id  # Tenant isolation
                )
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        if session.is_exported:
            raise ValueError("Cannot delete an exported session")

        await self.db.delete(session)
        await self.db.commit()
        return True

    async def mark_sessions_exported(
        self,
        session_ids: List[UUID],
        current_user: User
    ) -> List[BillableSession]:
        """Mark multiple sessions as exported with tenant isolation."""
        result = await self.db.execute(
            select(BillableSession).where(
                and_(
                    BillableSession.id.in_(session_ids),
                    BillableSession.user_id == current_user.id,
                    BillableSession.company_id == current_user.company_id,  # Tenant isolation
                    BillableSession.is_exported == False
                )
            )
        )
        sessions = result.scalars().all()

        now = datetime.now(timezone.utc)
        for session in sessions:
            session.is_exported = True
            session.exported_at = now

        await self.db.commit()
        return sessions
