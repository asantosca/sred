# app/services/briefing_service.py - Daily briefing generation service

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from anthropic import AsyncAnthropic
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import (
    DailyBriefing, User, Claim, Document, Conversation,
    Message, BillableSession
)

logger = logging.getLogger(__name__)


class BriefingService:
    """Service for generating and retrieving daily AI briefings"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def get_or_generate_briefing(
        self,
        user: User,
        briefing_date: Optional[date] = None
    ) -> Optional[DailyBriefing]:
        """
        Get today's briefing, generating if needed.

        Args:
            user: Current user
            briefing_date: Date for briefing (defaults to today)

        Returns:
            DailyBriefing or None if generation fails
        """
        if briefing_date is None:
            briefing_date = date.today()

        # Check for existing briefing
        existing = await self._get_existing_briefing(user.id, briefing_date)
        if existing:
            return existing

        # Generate new briefing
        return await self.generate_briefing(user, briefing_date)

    async def _get_existing_briefing(
        self,
        user_id: UUID,
        briefing_date: date
    ) -> Optional[DailyBriefing]:
        """Get existing briefing for user and date."""
        query = select(DailyBriefing).where(
            and_(
                DailyBriefing.user_id == user_id,
                DailyBriefing.briefing_date == briefing_date
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def generate_briefing(
        self,
        user: User,
        briefing_date: date
    ) -> Optional[DailyBriefing]:
        """
        Generate a new daily briefing for the user.

        Args:
            user: User to generate briefing for
            briefing_date: Date for the briefing

        Returns:
            Generated DailyBriefing or None on failure
        """
        try:
            # Gather context data
            context = await self._gather_context(user, briefing_date)

            # Generate briefing content
            content, token_count = await self._generate_content(user, context)

            # Save briefing
            briefing = DailyBriefing(
                company_id=user.company_id,
                user_id=user.id,
                briefing_date=briefing_date,
                content=content,
                model_name=settings.ANTHROPIC_MODEL,
                token_count=token_count,
                context_summary=context
            )

            self.db.add(briefing)
            await self.db.commit()
            await self.db.refresh(briefing)

            return briefing

        except Exception as e:
            logger.error(f"Failed to generate briefing for user {user.id}: {e}", exc_info=True)
            await self.db.rollback()
            return None

    async def _gather_context(self, user: User, briefing_date: date) -> Dict[str, Any]:
        """Gather all context needed for briefing generation."""
        # Look back 7 days for activity
        week_ago = briefing_date - timedelta(days=7)

        context = {
            "user_first_name": user.first_name or user.email.split("@")[0],
            "briefing_date": briefing_date.isoformat(),
            "claims": await self._get_claim_summary(user, week_ago),
            "recent_documents": await self._get_recent_documents(user, week_ago),
            "recent_conversations": await self._get_recent_conversations(user, week_ago),
            "unbilled_sessions": await self._get_unbilled_sessions(user),
            "usage_stats": await self._get_usage_stats(user)
        }

        return context

    async def _get_claim_summary(self, user: User, since: date) -> list:
        """Get summary of claims with recent activity."""
        query = select(
            Claim.id,
            Claim.company_name,
            Claim.claim_number,
            Claim.project_type,
            func.count(Document.id).label("doc_count"),
            func.max(Document.created_at).label("last_doc_upload")
        ).outerjoin(
            Document, Document.claim_id == Claim.id
        ).where(
            Claim.company_id == user.company_id,
            Claim.claim_status == "in_progress"
        ).group_by(
            Claim.id
        ).order_by(
            desc(func.max(Document.created_at))
        ).limit(10)

        result = await self.db.execute(query)
        rows = result.all()

        claims = []
        for row in rows:
            claims.append({
                "id": str(row.id),
                "company_name": row.company_name,
                "claim_number": row.claim_number,
                "project_type": row.project_type,
                "document_count": row.doc_count or 0,
                "last_activity": row.last_doc_upload.isoformat() if row.last_doc_upload else None
            })

        return claims

    async def _get_recent_documents(self, user: User, since: date) -> list:
        """Get documents uploaded in the last week."""
        query = select(
            Document.id,
            Document.document_title,
            Document.document_type,
            Document.created_at,
            Claim.company_name
        ).join(
            Claim, Document.claim_id == Claim.id
        ).where(
            Claim.company_id == user.company_id,
            Document.created_at >= since
        ).order_by(
            desc(Document.created_at)
        ).limit(10)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "title": row.document_title,
                "type": row.document_type,
                "uploaded": row.created_at.isoformat(),
                "claim": row.company_name
            }
            for row in rows
        ]

    async def _get_recent_conversations(self, user: User, since: date) -> list:
        """Get recent conversation activity."""
        query = select(
            Conversation.id,
            Conversation.title,
            Conversation.updated_at,
            func.count(Message.id).label("message_count"),
            Claim.company_name
        ).outerjoin(
            Claim, Conversation.claim_id == Claim.id
        ).join(
            Message, Message.conversation_id == Conversation.id
        ).where(
            Conversation.user_id == user.id,
            Conversation.updated_at >= since
        ).group_by(
            Conversation.id,
            Claim.company_name
        ).order_by(
            desc(Conversation.updated_at)
        ).limit(5)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "title": row.title or "Untitled conversation",
                "last_activity": row.updated_at.isoformat() if row.updated_at else None,
                "message_count": row.message_count,
                "claim": row.company_name
            }
            for row in rows
        ]

    async def _get_unbilled_sessions(self, user: User) -> list:
        """Get sessions not yet exported for billing."""
        query = select(
            BillableSession.id,
            BillableSession.duration_minutes,
            BillableSession.ai_description,
            BillableSession.started_at,
            Claim.company_name
        ).outerjoin(
            Claim, BillableSession.claim_id == Claim.id
        ).where(
            BillableSession.user_id == user.id,
            BillableSession.is_exported == False,
            BillableSession.is_billable == True
        ).order_by(
            desc(BillableSession.started_at)
        ).limit(10)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "duration_minutes": row.duration_minutes,
                "description": row.ai_description[:100] if row.ai_description else "No description",
                "date": row.started_at.date().isoformat() if row.started_at else None,
                "claim": row.company_name
            }
            for row in rows
        ]

    async def _get_usage_stats(self, user: User) -> dict:
        """Get usage statistics for the company."""
        from app.services.usage_tracker import UsageTracker
        tracker = UsageTracker(self.db)
        stats = await tracker.get_usage_stats(user.company_id)
        return {
            "documents": stats.get("documents", {}).get("current", 0),
            "ai_queries": stats.get("ai_queries", {}).get("current", 0)
        }

    async def _generate_content(self, user: User, context: Dict[str, Any]) -> tuple[str, int]:
        """Generate briefing content using Claude."""

        system_prompt = f"""You are an AI assistant for an SR&ED tax credit consulting platform.
Generate a brief, friendly daily briefing in Markdown format for a PwC consultant named {context['user_first_name']}.

Keep it concise and actionable. Focus on:
1. A warm greeting with their name
2. Active claims with recent document uploads (if any)
3. Recent project documentation added (if any)
4. Unbilled consulting time that needs attention (if any)

Use these formatting guidelines:
- Use ## for the greeting header
- Use **bold** for emphasis on important items (deadlines, large claims)
- Use bullet points for lists
- Keep the total length under 300 words
- Be professional but warm
- If there's no activity, encourage them to upload project documentation or start analyzing a claim.

Do NOT include fictional data. Only reference what's in the context provided."""

        # Build the user prompt with context
        user_prompt = f"""Generate a daily briefing for today ({context['briefing_date']}).

Consultant: {context['user_first_name']}

Context data:
- Active claims: {len(context['claims'])}
- Documents uploaded this week: {len(context['recent_documents'])}
- Recent conversations: {len(context['recent_conversations'])}
- Unbilled sessions pending: {len(context['unbilled_sessions'])}

Claims with activity:
{self._format_claims(context['claims'][:5])}

Recent documents:
{self._format_documents(context['recent_documents'][:5])}

Unbilled consulting time:
{self._format_unbilled(context['unbilled_sessions'][:5])}

Generate the briefing now."""

        response = await self.anthropic.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            system=system_prompt
        )

        content = response.content[0].text
        token_count = response.usage.input_tokens + response.usage.output_tokens

        return content, token_count

    def _format_claims(self, claims: list) -> str:
        if not claims:
            return "No active claims"
        lines = []
        for c in claims:
            lines.append(f"- {c['company_name']} ({c['claim_number']}): {c['document_count']} documents")
        return "\n".join(lines)

    def _format_documents(self, documents: list) -> str:
        if not documents:
            return "No documents uploaded this week"
        lines = []
        for d in documents:
            lines.append(f"- {d['title']} ({d['type']}) for {d['claim']}")
        return "\n".join(lines)

    def _format_unbilled(self, sessions: list) -> str:
        if not sessions:
            return "No unbilled sessions"
        total_minutes = sum(s.get('duration_minutes', 0) or 0 for s in sessions)
        hours = total_minutes / 60
        return f"{len(sessions)} sessions, approximately {hours:.1f} hours total"
