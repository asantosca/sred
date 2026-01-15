# app/services/feedback_analytics.py - Feedback Analytics Service

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    Message, Conversation, User, Company,
    MessageFeedbackDetails, ConversationSignals, MessageQualityScore,
    FeedbackAggregate, FeedbackAlert
)
from app.schemas.feedback import (
    EnhancedMessageFeedback, FeedbackResponse, FeedbackCategory,
    FeedbackStatsResponse, FeedbackTotals, FeedbackRates,
    FeedbackTimeSeriesPoint, FeedbackAlertResponse, FlaggedMessageResponse,
    ConversationSignalsResponse
)

logger = logging.getLogger(__name__)


# Alert thresholds
ALERT_THRESHOLDS = {
    "high_negative_rate": {
        "warning": 3,   # 3+ negatives/hour
        "critical": 5,  # 5+ negatives/hour
    },
    "abandonment_spike": {
        "warning": 0.30,   # 30% abandonment
        "critical": 0.50,  # 50% abandonment
    },
    "rephrase_spike": {
        "warning": 0.40,  # 40% rephrase rate
        "critical": 0.60, # 60% rephrase rate
    }
}


class FeedbackAnalyticsService:
    """Service for AI response feedback analytics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================
    # Explicit Feedback
    # ==================

    async def submit_feedback(
        self,
        message_id: UUID,
        feedback: EnhancedMessageFeedback,
        current_user: User
    ) -> FeedbackResponse:
        """
        Submit explicit feedback for a message with optional category.

        Args:
            message_id: The message to provide feedback for
            feedback: Rating, category, and optional text
            current_user: The user submitting feedback

        Returns:
            FeedbackResponse with saved feedback details
        """
        # Get the message and verify access
        query = (
            select(Message)
            .join(Conversation)
            .where(
                and_(
                    Message.id == message_id,
                    Conversation.company_id == current_user.company_id
                )
            )
        )
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            raise ValueError(f"Message {message_id} not found or access denied")

        # Only allow feedback on assistant messages
        if message.role != "assistant":
            raise ValueError("Feedback can only be submitted for assistant messages")

        # Update the message with feedback
        message.rating = feedback.rating
        message.feedback_text = feedback.feedback_text
        message.feedback_category = feedback.feedback_category.value if feedback.feedback_category else None

        # Create or update detailed feedback record
        existing = await self.db.execute(
            select(MessageFeedbackDetails).where(MessageFeedbackDetails.message_id == message_id)
        )
        feedback_details = existing.scalar_one_or_none()

        if feedback_details:
            feedback_details.rating = feedback.rating
            feedback_details.feedback_category = feedback.feedback_category.value if feedback.feedback_category else None
            feedback_details.feedback_text = feedback.feedback_text
        else:
            feedback_details = MessageFeedbackDetails(
                message_id=message_id,
                company_id=current_user.company_id,
                user_id=current_user.id,
                rating=feedback.rating,
                feedback_category=feedback.feedback_category.value if feedback.feedback_category else None,
                feedback_text=feedback.feedback_text
            )
            self.db.add(feedback_details)

        await self.db.commit()
        await self.db.refresh(feedback_details)

        # Update confidence scores
        await self._update_confidence_score(message_id, feedback.rating, current_user.company_id)

        logger.info(
            f"Feedback submitted for message {message_id}: rating={feedback.rating}, "
            f"category={feedback.feedback_category}"
        )

        return FeedbackResponse(
            message_id=message_id,
            rating=feedback.rating,
            feedback_category=feedback.feedback_category.value if feedback.feedback_category else None,
            feedback_text=feedback.feedback_text,
            created_at=feedback_details.created_at
        )

    # ==================
    # Implicit Signals
    # ==================

    async def track_session_start(
        self,
        conversation_id: UUID,
        current_user: User
    ) -> ConversationSignals:
        """Start tracking a conversation session"""
        # Check if session already exists
        existing = await self.db.execute(
            select(ConversationSignals).where(
                and_(
                    ConversationSignals.conversation_id == conversation_id,
                    ConversationSignals.user_id == current_user.id,
                    ConversationSignals.session_ended_at.is_(None)
                )
            )
        )
        signals = existing.scalar_one_or_none()

        if signals:
            return signals

        signals = ConversationSignals(
            conversation_id=conversation_id,
            company_id=current_user.company_id,
            user_id=current_user.id,
            session_started_at=datetime.now(timezone.utc)
        )
        self.db.add(signals)
        await self.db.commit()
        await self.db.refresh(signals)

        return signals

    async def track_session_end(
        self,
        conversation_id: UUID,
        current_user: User
    ) -> Optional[ConversationSignals]:
        """
        End session and calculate abandonment.

        A session is considered abandoned if it ended within 30 seconds
        of the last AI response with no follow-up.
        """
        result = await self.db.execute(
            select(ConversationSignals).where(
                and_(
                    ConversationSignals.conversation_id == conversation_id,
                    ConversationSignals.user_id == current_user.id,
                    ConversationSignals.session_ended_at.is_(None)
                )
            )
        )
        signals = result.scalar_one_or_none()

        if not signals:
            return None

        now = datetime.now(timezone.utc)
        signals.session_ended_at = now

        # Check for abandonment
        if signals.last_ai_response_at and not signals.conversation_continued:
            time_since_response = (now - signals.last_ai_response_at).total_seconds()
            if time_since_response <= 30:
                signals.is_abandoned = True

        await self.db.commit()
        return signals

    async def track_copy_event(
        self,
        conversation_id: UUID,
        message_id: UUID,
        current_user: User
    ) -> None:
        """Record that user copied response text"""
        signals = await self._get_or_create_signals(conversation_id, current_user)
        signals.copy_events = (signals.copy_events or 0) + 1
        await self.db.commit()

        # Update implicit signal score
        await self._update_implicit_score(message_id, current_user.company_id, copy_event=True)

    async def track_source_click(
        self,
        conversation_id: UUID,
        message_id: UUID,
        document_id: UUID,
        current_user: User
    ) -> None:
        """Record that user clicked on a cited source"""
        signals = await self._get_or_create_signals(conversation_id, current_user)
        signals.source_clicks = (signals.source_clicks or 0) + 1
        await self.db.commit()

        # Update implicit signal score
        await self._update_implicit_score(message_id, current_user.company_id, source_click=True)

    async def track_rephrase(
        self,
        conversation_id: UUID,
        message_content: str,
        current_user: User
    ) -> bool:
        """
        Detect and record if message is a rephrase of recent query.

        Returns True if detected as rephrase.
        """
        is_rephrase = await self._detect_rephrase(message_content, conversation_id, current_user)

        if is_rephrase:
            signals = await self._get_or_create_signals(conversation_id, current_user)
            signals.rephrase_count = (signals.rephrase_count or 0) + 1
            await self.db.commit()

        return is_rephrase

    async def update_message_timestamps(
        self,
        conversation_id: UUID,
        role: str,
        current_user: User
    ) -> None:
        """Update last message timestamps for abandonment detection"""
        signals = await self._get_or_create_signals(conversation_id, current_user)
        now = datetime.now(timezone.utc)

        if role == "user":
            signals.last_user_message_at = now
            signals.conversation_continued = True
        elif role == "assistant":
            signals.last_ai_response_at = now

        await self.db.commit()

    async def mark_billable_created(
        self,
        conversation_id: UUID,
        current_user: User
    ) -> None:
        """Mark that a billable entry was created from this conversation"""
        signals = await self._get_or_create_signals(conversation_id, current_user)
        signals.billable_created = True
        await self.db.commit()

        # This is a strong positive signal - update scores for all assistant messages
        await self._boost_conversation_confidence(conversation_id, current_user.company_id)

    # ==================
    # Quality Scoring
    # ==================

    async def calculate_question_quality(
        self,
        message: Message,
        conversation: Conversation
    ) -> float:
        """
        Calculate question quality score (0.0 - 1.0) for a user message.

        Higher score = better formed question = more reliable response evaluation.
        """
        content = message.content
        score = 0.0

        # Length bonus
        if len(content) >= 20:
            score += 0.15
        if len(content) >= 50:
            score += 0.10

        # Word count bonus
        words = content.split()
        if len(words) >= 5:
            score += 0.10
        if len(words) >= 10:
            score += 0.10

        # Specificity indicators
        if any(char.isdigit() for char in content):
            score += 0.05
        legal_terms = ['section', 'clause', 'paragraph', 'article', 'subsection', 'exhibit']
        if any(term in content.lower() for term in legal_terms):
            score += 0.10

        # Context bonuses
        has_matter = conversation.claim_id is not None
        if has_matter:
            score += 0.20

        # Check for document context in message
        doc_refs = ['document', 'file', 'page', 'contract', 'agreement']
        has_doc_context = any(ref in content.lower() for ref in doc_refs)
        if has_doc_context:
            score += 0.10

        # Check if this is a rephrase
        signals = await self.db.execute(
            select(ConversationSignals).where(
                ConversationSignals.conversation_id == conversation.id
            ).order_by(ConversationSignals.created_at.desc()).limit(1)
        )
        session_signals = signals.scalar_one_or_none()
        is_rephrase = session_signals and session_signals.rephrase_count and session_signals.rephrase_count > 0
        if is_rephrase:
            score -= 0.20

        return max(0.0, min(1.0, score))

    async def save_question_quality_score(
        self,
        message_id: UUID,
        conversation: Conversation,
        content: str,
        company_id: UUID
    ) -> MessageQualityScore:
        """Save question quality score for a user message"""
        has_matter = conversation.claim_id is not None
        words = content.split()
        doc_refs = ['document', 'file', 'page', 'contract', 'agreement']
        has_doc_context = any(ref in content.lower() for ref in doc_refs)

        # Calculate score
        score = 0.0
        if len(content) >= 20:
            score += 0.15
        if len(content) >= 50:
            score += 0.10
        if len(words) >= 5:
            score += 0.10
        if len(words) >= 10:
            score += 0.10
        if any(char.isdigit() for char in content):
            score += 0.05
        legal_terms = ['section', 'clause', 'paragraph', 'article', 'subsection', 'exhibit']
        if any(term in content.lower() for term in legal_terms):
            score += 0.10
        if has_matter:
            score += 0.20
        if has_doc_context:
            score += 0.10

        quality_score = MessageQualityScore(
            message_id=message_id,
            company_id=company_id,
            query_length=len(content),
            query_word_count=len(words),
            has_matter_context=has_matter,
            has_document_context=has_doc_context,
            is_follow_up_to_rephrase=False,
            question_quality_score=max(0.0, min(1.0, score))
        )
        self.db.add(quality_score)
        await self.db.commit()
        return quality_score

    async def update_context_relevance_score(
        self,
        message_id: UUID,
        context_relevance_score: float
    ) -> bool:
        """
        Update the context_relevance_score for a message after RAG retrieval.

        Args:
            message_id: The user message ID
            context_relevance_score: Average similarity from retrieved context (0.0-1.0)

        Returns:
            True if updated successfully, False if score not found
        """
        query = select(MessageQualityScore).where(
            MessageQualityScore.message_id == message_id
        )
        result = await self.db.execute(query)
        quality_score = result.scalar_one_or_none()

        if quality_score:
            quality_score.context_relevance_score = max(0.0, min(1.0, context_relevance_score))
            await self.db.commit()
            return True
        return False

    # ==================
    # Aggregation & Reporting
    # ==================

    async def get_feedback_stats(
        self,
        company_id: Optional[UUID],
        start_date: datetime,
        end_date: datetime,
        granularity: str = "daily"
    ) -> FeedbackStatsResponse:
        """Get feedback statistics for a date range"""
        # Build base query for messages in range
        base_query = select(Message).join(Conversation)
        if company_id:
            base_query = base_query.where(Conversation.company_id == company_id)
        base_query = base_query.where(
            and_(
                Message.role == "assistant",
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        )

        # Get totals
        result = await self.db.execute(base_query)
        messages = result.scalars().all()

        total_messages = len(messages)
        total_feedback = sum(1 for m in messages if m.rating is not None)
        positive_count = sum(1 for m in messages if m.rating is not None and m.rating > 0)
        negative_count = sum(1 for m in messages if m.rating is not None and m.rating < 0)

        # Category breakdown
        by_category: Dict[str, int] = {}
        for m in messages:
            if m.feedback_category:
                by_category[m.feedback_category] = by_category.get(m.feedback_category, 0) + 1

        # Get signal stats
        signals_query = select(ConversationSignals)
        if company_id:
            signals_query = signals_query.where(ConversationSignals.company_id == company_id)
        signals_query = signals_query.where(
            and_(
                ConversationSignals.session_started_at >= start_date,
                ConversationSignals.session_started_at <= end_date
            )
        )
        result = await self.db.execute(signals_query)
        signals = result.scalars().all()

        total_sessions = len(signals)
        abandoned_count = sum(1 for s in signals if s.is_abandoned)
        rephrase_sessions = sum(1 for s in signals if s.rephrase_count and s.rephrase_count > 0)
        engaged_sessions = sum(1 for s in signals if (s.copy_events or 0) + (s.source_clicks or 0) > 0)

        # Calculate rates
        positive_rate = positive_count / total_feedback if total_feedback > 0 else None
        abandonment_rate = abandoned_count / total_sessions if total_sessions > 0 else None
        rephrase_rate = rephrase_sessions / total_sessions if total_sessions > 0 else None
        engagement_rate = engaged_sessions / total_sessions if total_sessions > 0 else None

        # Get average quality scores
        scores_query = select(func.avg(MessageQualityScore.question_quality_score), func.avg(MessageQualityScore.overall_confidence_score))
        if company_id:
            scores_query = scores_query.where(MessageQualityScore.company_id == company_id)
        scores_query = scores_query.where(MessageQualityScore.scored_at >= start_date)
        result = await self.db.execute(scores_query)
        avg_question, avg_confidence = result.one()

        return FeedbackStatsResponse(
            period_start=start_date,
            period_end=end_date,
            granularity=granularity,
            totals=FeedbackTotals(
                total_messages=total_messages,
                total_feedback=total_feedback,
                positive_count=positive_count,
                negative_count=negative_count
            ),
            rates=FeedbackRates(
                positive_rate=positive_rate,
                rephrase_rate=rephrase_rate,
                abandonment_rate=abandonment_rate,
                engagement_rate=engagement_rate
            ),
            by_category=by_category,
            time_series=[],  # TODO: Implement time series breakdown
            avg_question_quality=float(avg_question) if avg_question else None,
            avg_response_confidence=float(avg_confidence) if avg_confidence else None
        )

    async def get_flagged_messages(
        self,
        company_id: Optional[UUID],
        limit: int = 50
    ) -> List[FlaggedMessageResponse]:
        """Get messages flagged for review (negative feedback or low confidence)"""
        query = (
            select(Message, Conversation, MessageQualityScore, Company)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .join(Company, Conversation.company_id == Company.id)
            .outerjoin(MessageQualityScore, MessageQualityScore.message_id == Message.id)
            .where(Message.role == "assistant")
            .where(
                or_(
                    Message.rating == -1,  # Negative feedback
                    MessageQualityScore.overall_confidence_score < 0.3  # Low confidence
                )
            )
        )

        if company_id:
            query = query.where(Conversation.company_id == company_id)

        query = query.order_by(Message.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        flagged = []
        for msg, conv, score, company in rows:
            # Get the preceding user message
            user_msg_query = (
                select(Message)
                .where(
                    and_(
                        Message.conversation_id == conv.id,
                        Message.role == "user",
                        Message.created_at < msg.created_at
                    )
                )
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            user_result = await self.db.execute(user_msg_query)
            user_msg = user_result.scalar_one_or_none()

            # Determine flag reason
            if msg.rating == -1:
                flag_reason = "negative_feedback"
            elif score and score.overall_confidence_score and score.overall_confidence_score < 0.3:
                flag_reason = "low_confidence"
            else:
                flag_reason = "unknown"

            flagged.append(FlaggedMessageResponse(
                message_id=msg.id,
                conversation_id=conv.id,
                company_id=company.id,
                company_name=company.name,
                user_query=user_msg.content if user_msg else "[No preceding question]",
                ai_response=msg.content[:500] + "..." if len(msg.content) > 500 else msg.content,
                created_at=msg.created_at,
                rating=msg.rating,
                feedback_category=msg.feedback_category,
                feedback_text=msg.feedback_text,
                confidence_score=score.overall_confidence_score if score else None,
                question_quality_score=score.question_quality_score if score else None,
                flag_reason=flag_reason
            ))

        return flagged

    async def get_active_alerts(
        self,
        company_id: Optional[UUID] = None,
        include_resolved: bool = False
    ) -> List[FeedbackAlertResponse]:
        """Get active (or all) feedback quality alerts"""
        query = select(FeedbackAlert, Company).outerjoin(Company, FeedbackAlert.company_id == Company.id)

        if not include_resolved:
            query = query.where(FeedbackAlert.is_active == True)

        if company_id:
            query = query.where(
                or_(
                    FeedbackAlert.company_id == company_id,
                    FeedbackAlert.company_id.is_(None)
                )
            )

        query = query.order_by(FeedbackAlert.triggered_at.desc())
        result = await self.db.execute(query)

        alerts = []
        for alert, company in result.all():
            alerts.append(FeedbackAlertResponse(
                id=alert.id,
                company_id=alert.company_id,
                company_name=company.name if company else None,
                alert_type=alert.alert_type,
                severity=alert.severity,
                threshold_value=alert.threshold_value,
                current_value=alert.current_value,
                time_window_minutes=alert.time_window_minutes,
                triggered_at=alert.triggered_at,
                resolved_at=alert.resolved_at,
                is_active=alert.is_active,
                details=alert.alert_details
            ))

        return alerts

    async def check_alert_thresholds(
        self,
        company_id: Optional[UUID] = None
    ) -> List[FeedbackAlert]:
        """Check and create alerts for threshold violations"""
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        new_alerts = []

        # Check negative feedback rate
        neg_query = (
            select(func.count(Message.id))
            .join(Conversation)
            .where(
                and_(
                    Message.rating == -1,
                    Message.created_at >= one_hour_ago
                )
            )
        )
        if company_id:
            neg_query = neg_query.where(Conversation.company_id == company_id)

        result = await self.db.execute(neg_query)
        negative_count = result.scalar() or 0

        if negative_count >= ALERT_THRESHOLDS["high_negative_rate"]["critical"]:
            alert = await self._create_alert(
                company_id=company_id,
                alert_type="high_negative_rate",
                severity="critical",
                threshold=ALERT_THRESHOLDS["high_negative_rate"]["critical"],
                current_value=negative_count,
                window_minutes=60
            )
            if alert:
                new_alerts.append(alert)
        elif negative_count >= ALERT_THRESHOLDS["high_negative_rate"]["warning"]:
            alert = await self._create_alert(
                company_id=company_id,
                alert_type="high_negative_rate",
                severity="warning",
                threshold=ALERT_THRESHOLDS["high_negative_rate"]["warning"],
                current_value=negative_count,
                window_minutes=60
            )
            if alert:
                new_alerts.append(alert)

        # Check abandonment rate
        signals_query = select(ConversationSignals).where(
            ConversationSignals.session_started_at >= one_hour_ago
        )
        if company_id:
            signals_query = signals_query.where(ConversationSignals.company_id == company_id)

        result = await self.db.execute(signals_query)
        signals = result.scalars().all()

        if len(signals) >= 10:  # Need minimum sample
            abandonment_rate = sum(1 for s in signals if s.is_abandoned) / len(signals)

            if abandonment_rate >= ALERT_THRESHOLDS["abandonment_spike"]["critical"]:
                alert = await self._create_alert(
                    company_id=company_id,
                    alert_type="abandonment_spike",
                    severity="critical",
                    threshold=ALERT_THRESHOLDS["abandonment_spike"]["critical"],
                    current_value=abandonment_rate,
                    window_minutes=60
                )
                if alert:
                    new_alerts.append(alert)
            elif abandonment_rate >= ALERT_THRESHOLDS["abandonment_spike"]["warning"]:
                alert = await self._create_alert(
                    company_id=company_id,
                    alert_type="abandonment_spike",
                    severity="warning",
                    threshold=ALERT_THRESHOLDS["abandonment_spike"]["warning"],
                    current_value=abandonment_rate,
                    window_minutes=60
                )
                if alert:
                    new_alerts.append(alert)

        return new_alerts

    # ==================
    # Private Helpers
    # ==================

    async def _get_or_create_signals(
        self,
        conversation_id: UUID,
        current_user: User
    ) -> ConversationSignals:
        """Get existing session signals or create new ones"""
        result = await self.db.execute(
            select(ConversationSignals).where(
                and_(
                    ConversationSignals.conversation_id == conversation_id,
                    ConversationSignals.user_id == current_user.id,
                    ConversationSignals.session_ended_at.is_(None)
                )
            )
        )
        signals = result.scalar_one_or_none()

        if not signals:
            signals = ConversationSignals(
                conversation_id=conversation_id,
                company_id=current_user.company_id,
                user_id=current_user.id,
                session_started_at=datetime.now(timezone.utc)
            )
            self.db.add(signals)
            await self.db.commit()
            await self.db.refresh(signals)

        return signals

    async def _detect_rephrase(
        self,
        new_message: str,
        conversation_id: UUID,
        current_user: User
    ) -> bool:
        """
        Detect if message is a rephrase of recent query.

        Algorithm: Check word overlap ratio (Jaccard similarity).
        If overlap > 0.6, consider it a rephrase.
        """
        recent_cutoff = datetime.now(timezone.utc) - timedelta(seconds=60)

        query = (
            select(Message)
            .join(Conversation)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.role == "user",
                    Message.created_at >= recent_cutoff,
                    Conversation.company_id == current_user.company_id
                )
            )
            .order_by(Message.created_at.desc())
            .limit(5)
        )

        result = await self.db.execute(query)
        recent_messages = result.scalars().all()

        new_words = set(new_message.lower().split())
        if not new_words:
            return False

        for msg in recent_messages:
            old_words = set(msg.content.lower().split())
            if not old_words:
                continue

            # Jaccard similarity
            intersection = len(new_words & old_words)
            union = len(new_words | old_words)
            similarity = intersection / union if union > 0 else 0

            if similarity > 0.6:
                return True

        return False

    async def _update_confidence_score(
        self,
        message_id: UUID,
        rating: int,
        company_id: UUID
    ) -> None:
        """Update confidence score based on explicit feedback"""
        result = await self.db.execute(
            select(MessageQualityScore).where(MessageQualityScore.message_id == message_id)
        )
        score = result.scalar_one_or_none()

        if not score:
            score = MessageQualityScore(
                message_id=message_id,
                company_id=company_id
            )
            self.db.add(score)

        # Convert rating to score
        if rating > 0:
            score.explicit_feedback_score = 0.85
        else:
            score.explicit_feedback_score = 0.2

        # Recalculate overall
        await self._recalculate_overall_confidence(score)
        await self.db.commit()

    async def _update_implicit_score(
        self,
        message_id: UUID,
        company_id: UUID,
        copy_event: bool = False,
        source_click: bool = False
    ) -> None:
        """Update implicit signal score"""
        result = await self.db.execute(
            select(MessageQualityScore).where(MessageQualityScore.message_id == message_id)
        )
        score = result.scalar_one_or_none()

        if not score:
            score = MessageQualityScore(
                message_id=message_id,
                company_id=company_id,
                implicit_signal_score=0.5  # Neutral baseline
            )
            self.db.add(score)

        current = score.implicit_signal_score or 0.5

        if copy_event:
            current = min(1.0, current + 0.15)
        if source_click:
            current = min(1.0, current + 0.10)

        score.implicit_signal_score = current
        await self._recalculate_overall_confidence(score)
        await self.db.commit()

    async def _recalculate_overall_confidence(self, score: MessageQualityScore) -> None:
        """Recalculate overall confidence from component scores"""
        # Weights: explicit 0.5, implicit 0.3, context 0.2
        explicit = score.explicit_feedback_score or 0.5
        implicit = score.implicit_signal_score or 0.5
        context = score.context_relevance_score or 0.5

        score.overall_confidence_score = (explicit * 0.5) + (implicit * 0.3) + (context * 0.2)

    async def _boost_conversation_confidence(
        self,
        conversation_id: UUID,
        company_id: UUID
    ) -> None:
        """Boost confidence for all assistant messages when billable created"""
        query = (
            select(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.role == "assistant"
                )
            )
        )
        result = await self.db.execute(query)
        messages = result.scalars().all()

        for msg in messages:
            score_result = await self.db.execute(
                select(MessageQualityScore).where(MessageQualityScore.message_id == msg.id)
            )
            score = score_result.scalar_one_or_none()

            if not score:
                score = MessageQualityScore(
                    message_id=msg.id,
                    company_id=company_id,
                    implicit_signal_score=0.7  # Billable creation is strong signal
                )
                self.db.add(score)
            else:
                score.implicit_signal_score = min(1.0, (score.implicit_signal_score or 0.5) + 0.20)

            await self._recalculate_overall_confidence(score)

        await self.db.commit()

    async def _create_alert(
        self,
        company_id: Optional[UUID],
        alert_type: str,
        severity: str,
        threshold: float,
        current_value: float,
        window_minutes: int
    ) -> Optional[FeedbackAlert]:
        """Create an alert if one doesn't already exist for this type"""
        # Check for existing active alert of same type
        existing = await self.db.execute(
            select(FeedbackAlert).where(
                and_(
                    FeedbackAlert.alert_type == alert_type,
                    FeedbackAlert.is_active == True,
                    or_(
                        FeedbackAlert.company_id == company_id,
                        and_(
                            FeedbackAlert.company_id.is_(None),
                            company_id is None
                        )
                    )
                )
            )
        )

        if existing.scalar_one_or_none():
            return None  # Alert already exists

        alert = FeedbackAlert(
            company_id=company_id,
            alert_type=alert_type,
            severity=severity,
            threshold_value=threshold,
            current_value=current_value,
            time_window_minutes=window_minutes
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)

        logger.warning(
            f"Feedback alert created: type={alert_type}, severity={severity}, "
            f"value={current_value}, threshold={threshold}"
        )

        return alert
