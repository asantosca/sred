# app/services/event_extraction.py - Extract timeline events from documents using LLM

import json
import logging
import re
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from anthropic import AsyncAnthropic
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Document, DocumentChunk, DocumentEvent, Claim
from app.schemas.timeline import ExtractedEvent, EventExtractionResult

logger = logging.getLogger(__name__)


# Extraction prompt for Claude
EVENT_EXTRACTION_PROMPT = """You are an SR&ED project document analyst. Extract project milestones and dated events from the following text.

For each event, provide:
1. event_date: The date in ISO format (YYYY-MM-DD). If only month/year is known, use the first day (e.g., "October 2020" → "2020-10-01")
2. event_description: A concise description of what happened (1-2 sentences max)
3. event_type: One of:
   - "project_start" = Project initiation or kickoff
   - "milestone" = Technical milestone achieved
   - "uncertainty_identified" = Technical challenge or uncertainty discovered
   - "experiment" = Test, experiment, or prototype iteration
   - "breakthrough" = Technological advancement achieved
   - "project_end" = Project completion or phase end
   - "other" = Other significant dated event
4. date_precision: How precise is the date?
   - "day" = exact date known (e.g., "December 30, 2020")
   - "month" = only month and year known (e.g., "October 2020")
   - "year" = only year known (e.g., "sometime in 2020")
   - "unknown" = date is inferred or very uncertain
5. confidence: How confident are you in this extraction?
   - "high" = date and event are clearly stated
   - "medium" = date is relative but can be resolved, or event is somewhat unclear
   - "low" = significant uncertainty about date or event
6. raw_date_text: The exact text from the document that indicates the date

IMPORTANT: Focus on events that demonstrate:
- Systematic investigation and iterative work
- Technological advancement attempts
- Technical challenges and how they were addressed
- Project phases and milestones

Respond with a JSON array of events. If no events found, return an empty array [].

Example output:
[
  {{
    "event_date": "2020-12-30",
    "event_description": "Prototype v2 testing began with new algorithm implementation",
    "event_type": "experiment",
    "date_precision": "day",
    "confidence": "high",
    "raw_date_text": "December 30, 2020"
  }},
  {{
    "event_date": "2020-10-01",
    "event_description": "Identified performance bottleneck in data processing module requiring novel approach",
    "event_type": "uncertainty_identified",
    "date_precision": "month",
    "confidence": "medium",
    "raw_date_text": "early October 2020"
  }}
]

Document text to analyze:
---
{text}
---

Extract all R&D project events with dates from the above text. Respond ONLY with the JSON array, no other text."""


def _repair_json(text: str) -> str:
    """
    Attempt to repair common JSON issues from LLM responses.

    Args:
        text: Potentially malformed JSON string

    Returns:
        Repaired JSON string
    """
    # Remove any text before the first [ or after the last ]
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    # Fix trailing commas before ] or }
    text = re.sub(r',(\s*[}\]])', r'\1', text)

    # Fix single quotes to double quotes (but not within strings)
    # This is tricky, so we do a simple replacement for property names
    text = re.sub(r"'(\w+)'(\s*:)", r'"\1"\2', text)

    # Fix unquoted property names
    text = re.sub(r'(\{|\,)\s*(\w+)\s*:', r'\1"\2":', text)

    return text


class EventExtractionService:
    """Service for extracting timeline events from documents using LLM"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def extract_events_from_document(
        self,
        document_id: UUID,
        company_id: UUID
    ) -> EventExtractionResult:
        """
        Extract timeline events from a document's chunks.

        Args:
            document_id: UUID of the document
            company_id: Company ID for tenant isolation

        Returns:
            EventExtractionResult with extracted events
        """
        logger.info(f"Starting event extraction for document {document_id}, company {company_id}")

        # Get document with tenant isolation
        doc_query = select(Document).join(Claim).where(
            Document.id == document_id,
            Claim.company_id == company_id
        )
        doc_result = await self.db.execute(doc_query)
        document = doc_result.scalar()

        if not document:
            logger.error(f"Document {document_id} not found or access denied for company {company_id}")
            return EventExtractionResult(
                document_id=document_id,
                events_extracted=0,
                events=[],
                extraction_errors=["Document not found or access denied"]
            )

        logger.info(f"Found document: {document.document_title}, claim_id: {document.claim_id}")

        # Get document chunks
        chunks_query = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index)

        chunks_result = await self.db.execute(chunks_query)
        chunks = chunks_result.scalars().all()

        logger.info(f"Found {len(chunks)} chunks for document {document_id}")

        if not chunks:
            logger.warning(f"No chunks found for document {document_id}")
            return EventExtractionResult(
                document_id=document_id,
                events_extracted=0,
                events=[],
                extraction_errors=["No text chunks found in document"]
            )

        # Mark old AI-extracted events as superseded (keep user-created/modified)
        await self._supersede_old_events(document_id)

        # Extract events from each chunk
        all_events: List[Tuple[ExtractedEvent, UUID]] = []
        extraction_errors: List[str] = []

        for chunk in chunks:
            try:
                logger.info(f"Extracting events from chunk {chunk.chunk_index}, content length: {len(chunk.content)}")
                chunk_events = await self._extract_events_from_text(chunk.content)
                logger.info(f"Extracted {len(chunk_events)} events from chunk {chunk.chunk_index}")
                for event in chunk_events:
                    all_events.append((event, chunk.id))
            except Exception as e:
                error_msg = f"Error extracting from chunk {chunk.chunk_index}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                extraction_errors.append(error_msg)

        logger.info(f"Total events extracted before dedup: {len(all_events)}")

        # Deduplicate events (same date + similar description)
        deduped_events = self._deduplicate_events(all_events)
        logger.info(f"Events after dedup: {len(deduped_events)}")

        # Save events to database
        saved_count = await self._save_events(
            events=deduped_events,
            document=document,
            company_id=company_id
        )

        logger.info(f"Saved {saved_count} events from document {document_id}")

        return EventExtractionResult(
            document_id=document_id,
            events_extracted=saved_count,
            events=[e for e, _ in deduped_events],
            extraction_errors=extraction_errors if extraction_errors else None
        )

    async def _extract_events_from_text(self, text: str) -> List[ExtractedEvent]:
        """
        Call Claude to extract events from a text chunk.

        Args:
            text: Text content to analyze

        Returns:
            List of extracted events
        """
        if not text or len(text.strip()) < 50:
            return []

        prompt = EVENT_EXTRACTION_PROMPT.format(text=text)

        try:
            response = await self.anthropic.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Parse JSON response
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            # Try to parse JSON, with repair on failure
            try:
                events_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to repair common JSON issues
                repaired = _repair_json(response_text)
                events_data = json.loads(repaired)

            if not isinstance(events_data, list):
                logger.warning(f"Expected list, got {type(events_data)}")
                return []

            # Validate and parse events
            events = []
            for event_dict in events_data:
                try:
                    event = ExtractedEvent(**event_dict)
                    # Validate date format
                    datetime.strptime(event.event_date, "%Y-%m-%d")
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Skipping invalid event: {event_dict}, error: {e}")
                    continue

            return events

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error calling LLM for event extraction: {e}", exc_info=True)
            raise

    def _deduplicate_events(
        self,
        events: List[Tuple[ExtractedEvent, UUID]]
    ) -> List[Tuple[ExtractedEvent, UUID]]:
        """
        Deduplicate events with the same date and similar descriptions.
        Keeps the event with higher confidence.

        Args:
            events: List of (event, chunk_id) tuples

        Returns:
            Deduplicated list
        """
        if not events:
            return []

        # Group by date
        by_date: Dict[str, List[Tuple[ExtractedEvent, UUID]]] = {}
        for event, chunk_id in events:
            if event.event_date not in by_date:
                by_date[event.event_date] = []
            by_date[event.event_date].append((event, chunk_id))

        # For each date, dedupe similar descriptions
        result = []
        confidence_order = {"high": 3, "medium": 2, "low": 1}

        for date_str, date_events in by_date.items():
            seen_descriptions = []

            for event, chunk_id in date_events:
                # Check if we've seen a similar description
                is_duplicate = False
                desc_lower = event.event_description.lower()

                for seen_desc in seen_descriptions:
                    # Simple similarity check - if one contains most of the other
                    if (desc_lower in seen_desc or seen_desc in desc_lower or
                        self._word_overlap(desc_lower, seen_desc) > 0.7):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    result.append((event, chunk_id))
                    seen_descriptions.append(desc_lower)

        return result

    def _word_overlap(self, s1: str, s2: str) -> float:
        """Calculate word overlap ratio between two strings."""
        words1 = set(s1.split())
        words2 = set(s2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        return len(intersection) / min(len(words1), len(words2))

    async def _supersede_old_events(self, document_id: UUID) -> None:
        """
        Mark old AI-extracted events as superseded.
        Preserves user-created and user-modified events.

        Args:
            document_id: Document being re-processed
        """
        stmt = (
            update(DocumentEvent)
            .where(
                DocumentEvent.document_id == document_id,
                DocumentEvent.superseded_at.is_(None),
                DocumentEvent.is_user_created == False,
                DocumentEvent.is_user_modified == False
            )
            .values(superseded_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def _save_events(
        self,
        events: List[Tuple[ExtractedEvent, UUID]],
        document: Document,
        company_id: UUID
    ) -> int:
        """
        Save extracted events to the database.

        Args:
            events: List of (event, chunk_id) tuples
            document: Source document
            company_id: Company ID

        Returns:
            Number of events saved
        """
        saved = 0

        for event, chunk_id in events:
            try:
                event_date = datetime.strptime(event.event_date, "%Y-%m-%d").date()

                db_event = DocumentEvent(
                    company_id=company_id,
                    claim_id=document.claim_id,
                    document_id=document.id,
                    chunk_id=chunk_id,
                    event_date=event_date,
                    event_description=event.event_description,
                    date_precision=event.date_precision,
                    confidence=event.confidence,
                    raw_date_text=event.raw_date_text,
                    document_version=document.version_number,
                    is_user_created=False,
                    is_user_modified=False
                )

                self.db.add(db_event)
                saved += 1

            except Exception as e:
                logger.error(f"Failed to save event: {e}", exc_info=True)
                continue

        await self.db.commit()
        return saved
