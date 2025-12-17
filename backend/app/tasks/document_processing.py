# app/tasks/document_processing.py - Background tasks for document processing

import logging
from uuid import UUID
from typing import Optional

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import async_session_factory
from app.services.document_processor import DocumentProcessor
from app.models.models import Document, Matter

logger = logging.getLogger(__name__)

# Document processing status constants
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_CHUNKED = "chunked"
STATUS_EMBEDDED = "embedded"
STATUS_EVENTS_EXTRACTED = "events_extracted"
STATUS_FAILED = "failed"


@celery_app.task(name="process_document_pipeline", bind=True, max_retries=3)
def process_document_pipeline(self, document_id: str, company_id: str) -> dict:
    """
    Background task to process a document through the full RAG pipeline:
    1. Text extraction
    2. Chunking
    3. Embedding generation

    Args:
        self: Celery task instance (for retry)
        document_id: UUID of the document to process
        company_id: Company ID for tenant isolation (REQUIRED)

    Returns:
        dict: Processing result with status and details
    """
    import asyncio

    logger.info(f"Starting document processing pipeline for document {document_id} (company: {company_id})")

    try:
        # Get or create event loop for this thread
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async processing in sync context
        result = loop.run_until_complete(_process_document_async(document_id, company_id))

        logger.info(f"Document {document_id} processed successfully")
        return result

    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {str(e)}", exc_info=True)

        # Update document status to failed
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(_update_document_status(document_id, STATUS_FAILED))
        except Exception as update_error:
            logger.error(f"Failed to update document status: {str(update_error)}")

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


async def _process_document_async(document_id: str, company_id: str) -> dict:
    """
    Async helper to process document through pipeline with tenant isolation.

    Args:
        document_id: UUID of document to process
        company_id: Company ID for tenant isolation

    Returns:
        dict: Processing result
    """
    doc_uuid = UUID(document_id)
    company_uuid = UUID(company_id)

    async with async_session_factory() as session:
        processor = DocumentProcessor(session)

        # Update status to processing
        await _update_document_status_in_session(session, doc_uuid, STATUS_PROCESSING)

        # Step 1: Extract text from document
        logger.info(f"Extracting text from document {document_id}")
        extraction_success = await processor.process_text_extraction(doc_uuid, company_uuid)

        if not extraction_success:
            logger.error(f"Text extraction failed for document {document_id}")
            await _update_document_status_in_session(session, doc_uuid, STATUS_FAILED)
            return {
                "status": "failed",
                "stage": "extraction",
                "document_id": document_id
            }

        # Step 2: Process chunking
        logger.info(f"Processing chunking for document {document_id}")
        chunking_success = await processor.process_chunking(doc_uuid, company_uuid)

        if not chunking_success:
            logger.error(f"Chunking failed for document {document_id}")
            await _update_document_status_in_session(session, doc_uuid, STATUS_FAILED)
            return {
                "status": "failed",
                "stage": "chunking",
                "document_id": document_id
            }

        # Update status to chunked
        await _update_document_status_in_session(session, doc_uuid, STATUS_CHUNKED)

        # Step 3: Generate embeddings
        logger.info(f"Generating embeddings for document {document_id}")
        embedding_success = await processor.process_embeddings(doc_uuid, company_uuid)

        if not embedding_success:
            logger.error(f"Embedding generation failed for document {document_id}")
            await _update_document_status_in_session(session, doc_uuid, STATUS_FAILED)
            return {
                "status": "failed",
                "stage": "embedding",
                "document_id": document_id
            }

        # Update status to embedded (ready for search)
        await _update_document_status_in_session(session, doc_uuid, STATUS_EMBEDDED)

        # Step 4: Extract timeline events
        logger.info(f"Extracting timeline events for document {document_id}")
        events_extracted = 0
        try:
            from app.services.event_extraction import EventExtractionService
            event_service = EventExtractionService(session)
            extraction_result = await event_service.extract_events_from_document(
                doc_uuid, company_uuid
            )
            events_extracted = extraction_result.events_extracted
            logger.info(f"Extracted {events_extracted} events from document {document_id}")

            # Update status to events_extracted
            await _update_document_status_in_session(session, doc_uuid, STATUS_EVENTS_EXTRACTED)
        except Exception as e:
            # Event extraction failure is non-fatal - document is still searchable
            logger.warning(f"Event extraction failed for document {document_id}: {str(e)}")
            # Keep status as embedded since core functionality still works

        # Step 5: Generate AI summary
        logger.info(f"Generating AI summary for document {document_id}")
        summary_generated = False
        try:
            summary_generated = await _generate_document_summary(
                session, doc_uuid, company_uuid
            )
            if summary_generated:
                logger.info(f"AI summary generated for document {document_id}")
            else:
                logger.info(f"No summary generated for document {document_id} (possibly empty text)")
        except Exception as e:
            # Summary generation failure is non-fatal - document is still searchable
            logger.warning(f"Summary generation failed for document {document_id}: {str(e)}")

        logger.info(f"Document {document_id} fully processed and ready for search")

        return {
            "status": "success",
            "document_id": document_id,
            "indexed_for_search": True,
            "events_extracted": events_extracted,
            "summary_generated": summary_generated
        }


async def _update_document_status(document_id: str, status: str):
    """
    Update document processing status (creates new session).

    Args:
        document_id: Document UUID
        status: New processing status
    """
    async with async_session_factory() as session:
        await _update_document_status_in_session(session, UUID(document_id), status)


async def _update_document_status_in_session(
    session,
    document_id: UUID,
    status: str
):
    """
    Update document processing status (uses existing session).

    Args:
        session: Database session
        document_id: Document UUID
        status: New processing status
    """
    from sqlalchemy import select, update

    # Update document status
    stmt = (
        update(Document)
        .where(Document.id == document_id)
        .values(processing_status=status)
    )

    await session.execute(stmt)
    await session.commit()

    logger.info(f"Document {document_id} status updated to {status}")


@celery_app.task(name="process_document_chunking", bind=True, max_retries=3)
def process_document_chunking(self, document_id: str, company_id: str) -> dict:
    """
    Background task to process document chunking only.

    This is a sub-task that can be called separately if needed.

    Args:
        self: Celery task instance
        document_id: UUID of document to chunk
        company_id: Company ID for tenant isolation (REQUIRED)

    Returns:
        dict: Chunking result
    """
    import asyncio

    logger.info(f"Starting chunking for document {document_id} (company: {company_id})")

    try:
        doc_uuid = UUID(document_id)
        company_uuid = UUID(company_id)

        async def _chunk():
            async with async_session_factory() as session:
                processor = DocumentProcessor(session)
                success = await processor.process_chunking(doc_uuid, company_uuid)

                if success:
                    await _update_document_status_in_session(
                        session, doc_uuid, STATUS_CHUNKED
                    )

                return success

        success = asyncio.run(_chunk())

        if success:
            return {"status": "success", "document_id": document_id}
        else:
            return {"status": "failed", "document_id": document_id}

    except Exception as e:
        logger.error(f"Chunking failed for {document_id}: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(name="process_document_embeddings", bind=True, max_retries=3)
def process_document_embeddings(self, document_id: str, company_id: str) -> dict:
    """
    Background task to generate embeddings for document chunks.

    This is a sub-task that can be called separately if needed.

    Args:
        self: Celery task instance
        document_id: UUID of document to generate embeddings for
        company_id: Company ID for tenant isolation (REQUIRED)

    Returns:
        dict: Embedding generation result
    """
    import asyncio

    logger.info(f"Starting embedding generation for document {document_id} (company: {company_id})")

    try:
        doc_uuid = UUID(document_id)
        company_uuid = UUID(company_id)

        async def _embed():
            async with async_session_factory() as session:
                processor = DocumentProcessor(session)
                success = await processor.process_embeddings(doc_uuid, company_uuid)

                if success:
                    await _update_document_status_in_session(
                        session, doc_uuid, STATUS_EMBEDDED
                    )

                return success

        success = asyncio.run(_embed())

        if success:
            return {"status": "success", "document_id": document_id, "indexed_for_search": True}
        else:
            return {"status": "failed", "document_id": document_id}

    except Exception as e:
        logger.error(f"Embedding generation failed for {document_id}: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


async def _generate_document_summary(
    session,
    document_id: UUID,
    company_id: UUID
) -> bool:
    """
    Generate AI summary for a document using its extracted text.

    Args:
        session: Database session
        document_id: Document UUID
        company_id: Company ID for tenant isolation

    Returns:
        bool: True if summary was generated, False otherwise
    """
    from datetime import datetime
    from sqlalchemy import select, update

    from app.services.summarization import summarization_service

    # Fetch document with tenant isolation
    stmt = (
        select(Document)
        .join(Matter)
        .where(
            Document.id == document_id,
            Matter.company_id == company_id
        )
    )
    result = await session.execute(stmt)
    document = result.scalar()

    if not document:
        logger.error(f"Document {document_id} not found for company {company_id}")
        return False

    if not document.extracted_text:
        logger.warning(f"Document {document_id} has no extracted text for summarization")
        return False

    # Generate summary
    summary = await summarization_service.generate_summary(
        text=document.extracted_text,
        document_title=document.document_title or document.original_filename,
        company_id=company_id,
        document_id=document_id
    )

    if not summary:
        return False

    # Update document with summary
    update_stmt = (
        update(Document)
        .where(Document.id == document_id)
        .values(
            ai_summary=summary,
            ai_summary_generated_at=datetime.utcnow()
        )
    )
    await session.execute(update_stmt)
    await session.commit()

    return True
