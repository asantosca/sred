# app/services/usage_logging.py - Track API usage for cost monitoring

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.models import ApiUsageLog

logger = logging.getLogger(__name__)

# Cost per 1M tokens (in USD cents) - Update these as pricing changes
# Prices as of Dec 2024
PRICING = {
    # Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
    "claude-3-5-sonnet-20241022": {"input": 300, "output": 1500},  # $3/$15 per 1M
    "claude-3-7-sonnet-20250219": {"input": 300, "output": 1500},  # Assuming same as 3.5
    # OpenAI text-embedding-3-small
    "text-embedding-3-small": {"input": 2, "output": 0},  # $0.02 per 1M
    # AWS Textract
    "textract": {"per_page": 1.5},  # ~$0.015 per page for text detection
}


def estimate_cost_cents(
    service: str,
    model_name: Optional[str],
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    pages_processed: Optional[int] = None,
    chunks_processed: Optional[int] = None
) -> Optional[int]:
    """
    Estimate cost in USD cents based on usage.

    Returns None if pricing info not available.
    """
    if service == "textract_ocr" and pages_processed:
        return int(pages_processed * PRICING["textract"]["per_page"])

    if model_name and model_name in PRICING:
        pricing = PRICING[model_name]
        cost = 0
        if input_tokens and "input" in pricing:
            cost += (input_tokens / 1_000_000) * pricing["input"]
        if output_tokens and "output" in pricing:
            cost += (output_tokens / 1_000_000) * pricing["output"]
        return int(cost * 100)  # Convert to cents

    # For embeddings, estimate tokens from chunks
    if service == "openai_embeddings" and chunks_processed:
        # Rough estimate: avg 500 tokens per chunk
        estimated_tokens = chunks_processed * 500
        return int((estimated_tokens / 1_000_000) * PRICING["text-embedding-3-small"]["input"] * 100)

    return None


class UsageLoggingService:
    """Service for logging API usage to track costs"""

    async def log_usage(
        self,
        service: str,
        operation: Optional[str] = None,
        company_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        pages_processed: Optional[int] = None,
        chunks_processed: Optional[int] = None,
        model_name: Optional[str] = None,
        document_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> None:
        """
        Log API usage for cost tracking.

        Args:
            service: Service identifier (claude_chat, claude_summary, openai_embeddings, textract_ocr)
            operation: Specific operation (send_message, generate_summary, etc.)
            company_id: Company ID for tenant tracking
            user_id: User ID who initiated the request
            input_tokens: Input tokens used (for LLMs)
            output_tokens: Output tokens used (for LLMs)
            pages_processed: Pages processed (for OCR)
            chunks_processed: Chunks processed (for embeddings)
            model_name: Model used (for LLMs)
            document_id: Associated document ID
            conversation_id: Associated conversation ID
            db: Database session (if None, creates new session)
        """
        # Estimate cost
        estimated_cost = estimate_cost_cents(
            service=service,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            pages_processed=pages_processed,
            chunks_processed=chunks_processed
        )

        log_entry = {
            "service": service,
            "operation": operation,
            "company_id": company_id,
            "user_id": user_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "pages_processed": pages_processed,
            "chunks_processed": chunks_processed,
            "model_name": model_name,
            "estimated_cost_cents": estimated_cost,
            "document_id": document_id,
            "conversation_id": conversation_id
        }

        try:
            if db:
                stmt = insert(ApiUsageLog).values(**log_entry)
                await db.execute(stmt)
                # Don't commit - let the caller manage the transaction
            else:
                # Create new session for background tasks
                async with async_session_factory() as session:
                    stmt = insert(ApiUsageLog).values(**log_entry)
                    await session.execute(stmt)
                    await session.commit()

            logger.debug(
                f"Logged API usage: service={service}, operation={operation}, "
                f"input_tokens={input_tokens}, output_tokens={output_tokens}, "
                f"estimated_cost_cents={estimated_cost}"
            )
        except Exception as e:
            # Don't let logging failures affect main operations
            logger.error(f"Failed to log API usage: {e}", exc_info=True)


# Singleton instance
usage_logging_service = UsageLoggingService()
