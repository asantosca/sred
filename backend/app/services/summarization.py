# app/services/summarization.py - Generate AI summaries for documents

import logging
from typing import Optional
from uuid import UUID

from anthropic import AsyncAnthropic

from app.core.config import settings
from app.services.usage_logging import usage_logging_service

logger = logging.getLogger(__name__)

# Token limit for direct summarization (leaving room for prompt and response)
# Claude has 200k context, we'll use 150k for the document text
MAX_DIRECT_TOKENS = 150000
# Approximate characters per token for estimation
CHARS_PER_TOKEN = 4
MAX_DIRECT_CHARS = MAX_DIRECT_TOKENS * CHARS_PER_TOKEN

# Chunk size for hierarchical summarization
CHUNK_TOKENS = 50000
CHUNK_CHARS = CHUNK_TOKENS * CHARS_PER_TOKEN


SUMMARY_PROMPT = """You are an SR&ED project document analyst. Summarize this document concisely, focusing on:
- Document type (technical report, timesheet, project plan, lab notebook, etc.)
- Project name and fiscal period if mentioned
- Key R&D activities described
- Technological uncertainties or challenges mentioned
- Methodologies or systematic approaches used
- Results, conclusions, or advancements achieved
- Personnel or contractors mentioned

Document Title: {document_title}

Document Text:
{text}

Provide a clear, factual summary in 2-4 paragraphs focusing on SR&ED eligibility relevance. Do not include information not present in the document."""


SECTION_SUMMARY_PROMPT = """You are an SR&ED project document analyst. Summarize this section of a document concisely, preserving key details about:
- R&D activities and experiments described
- Technical challenges or uncertainties
- Methodologies or approaches used
- Results or findings
- Personnel involved and time spent

Section Text:
{text}

Provide a factual summary in 1-2 paragraphs focusing on SR&ED eligibility relevance."""


COMBINE_SUMMARIES_PROMPT = """You are an SR&ED project document analyst. Below are summaries of different sections of a single document.
Combine them into a coherent overall summary focusing on:
- Document type (technical report, timesheet, project plan, lab notebook, etc.)
- Project name and fiscal period
- Key R&D activities and experiments
- Technological uncertainties addressed
- Methodologies and systematic approaches
- Results, conclusions, or advancements achieved
- Personnel and time tracking information

Document Title: {document_title}

Section Summaries:
{summaries}

Provide a unified, clear summary in 2-4 paragraphs focusing on SR&ED eligibility relevance. Do not include information not present in the summaries."""


class SummarizationService:
    """Service for generating AI summaries of documents using Claude."""

    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_summary(
        self,
        text: str,
        document_title: str,
        company_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None
    ) -> Optional[str]:
        """
        Generate an AI summary of a document.

        For documents that fit within context limits, summarizes directly.
        For longer documents, uses hierarchical summarization.

        Args:
            text: The full extracted text of the document
            document_title: Title of the document for context
            company_id: Company ID for usage tracking
            document_id: Document ID for usage tracking

        Returns:
            Generated summary string, or None if generation fails
        """
        if not text or len(text.strip()) < 100:
            logger.warning("Text too short for meaningful summary")
            return None

        text_length = len(text)
        logger.info(
            f"Generating summary for '{document_title}', "
            f"text length: {text_length} chars"
        )

        # Store context for usage logging
        self._current_company_id = company_id
        self._current_document_id = document_id

        try:
            if text_length <= MAX_DIRECT_CHARS:
                # Document fits in context - summarize directly
                return await self._summarize_direct(text, document_title)
            else:
                # Document too long - use hierarchical summarization
                return await self._summarize_hierarchical(text, document_title)
        except Exception as e:
            logger.error(f"Summary generation failed: {e}", exc_info=True)
            raise
        finally:
            self._current_company_id = None
            self._current_document_id = None

    async def _summarize_direct(
        self,
        text: str,
        document_title: str
    ) -> str:
        """
        Summarize a document that fits within context limits.

        Args:
            text: Document text
            document_title: Title for context

        Returns:
            Generated summary
        """
        prompt = SUMMARY_PROMPT.format(
            document_title=document_title,
            text=text
        )

        response = await self.anthropic.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        # Log API usage
        await usage_logging_service.log_usage(
            service="claude_summary",
            operation="summarize_direct",
            company_id=getattr(self, '_current_company_id', None),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model_name=settings.ANTHROPIC_MODEL,
            document_id=getattr(self, '_current_document_id', None)
        )

        summary = response.content[0].text.strip()
        logger.info(f"Generated direct summary: {len(summary)} chars")
        return summary

    async def _summarize_hierarchical(
        self,
        text: str,
        document_title: str
    ) -> str:
        """
        Summarize a long document using hierarchical approach:
        1. Split into chunks
        2. Summarize each chunk
        3. Combine chunk summaries into final summary

        Args:
            text: Document text
            document_title: Title for context

        Returns:
            Generated summary
        """
        logger.info(f"Using hierarchical summarization for long document")

        # Split text into chunks
        chunks = self._split_into_chunks(text)
        logger.info(f"Split document into {len(chunks)} chunks")

        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i + 1}/{len(chunks)}")
            chunk_summary = await self._summarize_chunk(chunk)
            chunk_summaries.append(f"[Section {i + 1}]\n{chunk_summary}")

        # Combine summaries
        combined_summaries = "\n\n".join(chunk_summaries)

        # If combined summaries are still too long, recursively summarize
        if len(combined_summaries) > MAX_DIRECT_CHARS:
            logger.info("Combined summaries still too long, recursing")
            return await self._summarize_hierarchical(
                combined_summaries,
                document_title
            )

        # Generate final combined summary
        return await self._combine_summaries(combined_summaries, document_title)

    async def _summarize_chunk(self, text: str) -> str:
        """
        Summarize a single chunk of text.

        Args:
            text: Chunk text

        Returns:
            Chunk summary
        """
        prompt = SECTION_SUMMARY_PROMPT.format(text=text)

        response = await self.anthropic.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        # Log API usage
        await usage_logging_service.log_usage(
            service="claude_summary",
            operation="summarize_chunk",
            company_id=getattr(self, '_current_company_id', None),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model_name=settings.ANTHROPIC_MODEL,
            document_id=getattr(self, '_current_document_id', None)
        )

        return response.content[0].text.strip()

    async def _combine_summaries(
        self,
        summaries: str,
        document_title: str
    ) -> str:
        """
        Combine section summaries into a final document summary.

        Args:
            summaries: Combined section summaries
            document_title: Document title

        Returns:
            Final summary
        """
        prompt = COMBINE_SUMMARIES_PROMPT.format(
            document_title=document_title,
            summaries=summaries
        )

        response = await self.anthropic.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        # Log API usage
        await usage_logging_service.log_usage(
            service="claude_summary",
            operation="combine_summaries",
            company_id=getattr(self, '_current_company_id', None),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model_name=settings.ANTHROPIC_MODEL,
            document_id=getattr(self, '_current_document_id', None)
        )

        summary = response.content[0].text.strip()
        logger.info(f"Generated combined summary: {len(summary)} chars")
        return summary

    def _split_into_chunks(self, text: str) -> list[str]:
        """
        Split text into chunks suitable for summarization.
        Tries to split on paragraph boundaries.

        Args:
            text: Full text to split

        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = ""

        # Split on double newlines (paragraphs)
        paragraphs = text.split("\n\n")

        for para in paragraphs:
            # If adding this paragraph exceeds chunk size, save current and start new
            if len(current_chunk) + len(para) > CHUNK_CHARS and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks


# Singleton instance for easy import
summarization_service = SummarizationService()
