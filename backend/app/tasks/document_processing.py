# app/tasks/document_processing.py - Background tasks for document processing

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Optional

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import async_session_factory
from app.services.document_processor import DocumentProcessor
from app.models.models import Document, Claim as Matter, Project, ProjectDiscoveryRun

logger = logging.getLogger(__name__)

# Document processing status constants
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_SIGNALS_DETECTED = "signals_detected"
STATUS_CHUNKED = "chunked"
STATUS_EMBEDDED = "embedded"
STATUS_EVENTS_EXTRACTED = "events_extracted"
STATUS_SUMMARIZING = "summarizing"
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"

# Auto-discovery configuration
AUTO_DISCOVERY_MIN_DOCUMENTS = 3  # Minimum documents before auto-discovery triggers
AUTO_DISCOVERY_COOLDOWN_HOURS = 1  # Don't re-run discovery within this period


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

        # Step 1.5: Detect SR&ED signals (document-level)
        logger.info(f"Detecting SR&ED signals for document {document_id}")
        sred_signals_detected = False
        try:
            sred_success = await processor.process_sred_signals(doc_uuid, company_uuid)
            if sred_success:
                sred_signals_detected = True
                logger.info(f"SR&ED signals detected for document {document_id}")
                await _update_document_status_in_session(session, doc_uuid, STATUS_SIGNALS_DETECTED)
        except Exception as e:
            # Signal detection failure is non-fatal
            logger.warning(f"SR&ED signal detection failed for document {document_id}: {str(e)}")

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

        # Step 2.5: Detect SR&ED signals at chunk level
        try:
            chunk_signals_success = await processor.process_chunk_sred_signals(doc_uuid, company_uuid)
            if chunk_signals_success:
                logger.info(f"Chunk-level SR&ED signals detected for document {document_id}")
        except Exception as e:
            # Chunk signal detection failure is non-fatal
            logger.warning(f"Chunk SR&ED signal detection failed for document {document_id}: {str(e)}")

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
            # Update status to summarizing
            await _update_document_status_in_session(session, doc_uuid, STATUS_SUMMARIZING)

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

        # Update status to complete
        await _update_document_status_in_session(session, doc_uuid, STATUS_COMPLETE)
        logger.info(f"Document {document_id} fully processed and ready for search")

        # Step 6: Check if auto-discovery should be triggered
        auto_discovery_triggered = False
        try:
            # Get the claim_id for this document
            doc_query = select(Document).where(Document.id == doc_uuid)
            doc_result = await session.execute(doc_query)
            doc = doc_result.scalar()

            if doc and doc.claim_id:
                should_trigger = await _should_trigger_auto_discovery(
                    session, doc.claim_id, company_uuid
                )
                if should_trigger:
                    # Trigger discovery task asynchronously
                    discover_projects_task.delay(
                        str(doc.claim_id),
                        str(company_uuid),
                        None,  # user_id (None for auto-triggered)
                        True   # auto_triggered flag
                    )
                    auto_discovery_triggered = True
                    logger.info(
                        f"Auto-discovery triggered for claim {doc.claim_id} "
                        f"after document {document_id} completed"
                    )
        except Exception as e:
            # Auto-discovery failure is non-fatal
            logger.warning(f"Auto-discovery check failed for document {document_id}: {str(e)}")

        return {
            "status": "success",
            "document_id": document_id,
            "indexed_for_search": True,
            "sred_signals_detected": sred_signals_detected,
            "events_extracted": events_extracted,
            "summary_generated": summary_generated,
            "auto_discovery_triggered": auto_discovery_triggered
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


async def _should_trigger_auto_discovery(
    session,
    claim_id: UUID,
    company_id: UUID
) -> bool:
    """
    Check if auto-discovery should be triggered for a claim.

    Conditions:
    1. All documents in the claim are complete (none pending/processing)
    2. At least MIN_DOCUMENTS exist
    3. No discovery has run in the last COOLDOWN period

    Args:
        session: Database session
        claim_id: Claim UUID
        company_id: Company ID for tenant isolation

    Returns:
        bool: True if auto-discovery should be triggered
    """
    from sqlalchemy import select, func, and_

    # Check document counts
    total_docs_query = (
        select(func.count(Document.id))
        .join(Matter, Document.claim_id == Matter.id)
        .where(
            and_(
                Document.claim_id == claim_id,
                Matter.company_id == company_id
            )
        )
    )
    total_result = await session.execute(total_docs_query)
    total_docs = total_result.scalar() or 0

    if total_docs < AUTO_DISCOVERY_MIN_DOCUMENTS:
        logger.debug(
            f"Claim {claim_id}: {total_docs} docs < {AUTO_DISCOVERY_MIN_DOCUMENTS} min, "
            "skipping auto-discovery"
        )
        return False

    # Check for pending/processing documents
    incomplete_query = (
        select(func.count(Document.id))
        .join(Matter, Document.claim_id == Matter.id)
        .where(
            and_(
                Document.claim_id == claim_id,
                Matter.company_id == company_id,
                Document.processing_status.in_([
                    STATUS_PENDING, STATUS_PROCESSING, STATUS_SIGNALS_DETECTED,
                    STATUS_CHUNKED, STATUS_EMBEDDED, STATUS_EVENTS_EXTRACTED,
                    STATUS_SUMMARIZING
                ])
            )
        )
    )
    incomplete_result = await session.execute(incomplete_query)
    incomplete_docs = incomplete_result.scalar() or 0

    if incomplete_docs > 0:
        logger.debug(
            f"Claim {claim_id}: {incomplete_docs} docs still processing, "
            "skipping auto-discovery"
        )
        return False

    # Check cooldown - has discovery run recently?
    cooldown_threshold = datetime.now(timezone.utc) - timedelta(hours=AUTO_DISCOVERY_COOLDOWN_HOURS)
    recent_discovery_query = (
        select(func.count(ProjectDiscoveryRun.id))
        .where(
            and_(
                ProjectDiscoveryRun.claim_id == claim_id,
                ProjectDiscoveryRun.created_at >= cooldown_threshold,
                ProjectDiscoveryRun.status.in_(['running', 'completed'])
            )
        )
    )
    recent_result = await session.execute(recent_discovery_query)
    recent_runs = recent_result.scalar() or 0

    if recent_runs > 0:
        logger.debug(
            f"Claim {claim_id}: discovery ran within {AUTO_DISCOVERY_COOLDOWN_HOURS}h cooldown, "
            "skipping auto-discovery"
        )
        return False

    logger.info(
        f"Claim {claim_id}: all {total_docs} documents complete and no recent discovery - "
        "auto-discovery eligible"
    )
    return True


@celery_app.task(name="discover_projects", bind=True, max_retries=2)
def discover_projects_task(
    self,
    claim_id: str,
    company_id: str,
    user_id: Optional[str] = None,
    auto_triggered: bool = False
) -> dict:
    """
    Background task to run project discovery for a claim.

    Args:
        self: Celery task instance
        claim_id: UUID of the claim to analyze
        company_id: Company ID for tenant isolation
        user_id: Optional user who triggered discovery
        auto_triggered: Whether this was auto-triggered after document processing

    Returns:
        dict: Discovery result with projects found
    """
    import asyncio

    logger.info(
        f"Starting project discovery for claim {claim_id} "
        f"(company: {company_id}, auto_triggered: {auto_triggered})"
    )

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

        # Run async discovery
        result = loop.run_until_complete(
            _run_project_discovery(claim_id, company_id, user_id, auto_triggered)
        )

        logger.info(f"Project discovery completed for claim {claim_id}")
        return result

    except Exception as e:
        logger.error(f"Project discovery failed for claim {claim_id}: {str(e)}", exc_info=True)
        # Retry with exponential backoff (less aggressive than document processing)
        raise self.retry(exc=e, countdown=300 * (2 ** self.request.retries))


async def _run_project_discovery(
    claim_id: str,
    company_id: str,
    user_id: Optional[str],
    auto_triggered: bool
) -> dict:
    """
    Async helper to run project discovery.

    Args:
        claim_id: UUID of the claim
        company_id: Company ID
        user_id: Optional user ID
        auto_triggered: Whether this was auto-triggered

    Returns:
        dict: Discovery results
    """
    from app.services.project_discovery_service import ProjectDiscoveryService

    claim_uuid = UUID(claim_id)
    company_uuid = UUID(company_id)
    user_uuid = UUID(user_id) if user_id else None

    async with async_session_factory() as session:
        discovery_service = ProjectDiscoveryService(session)

        # Run discovery
        categorized = await discovery_service.discover_projects(
            claim_id=claim_uuid,
            company_id=company_uuid,
            user_id=user_uuid,
            backfill_signals=True
        )

        # Count results
        high_count = len(categorized.get("high_confidence", []))
        medium_count = len(categorized.get("medium_confidence", []))
        low_count = len(categorized.get("low_confidence", []))
        total_candidates = high_count + medium_count + low_count

        # For auto-triggered discovery, auto-save high confidence projects
        projects_saved = 0
        if auto_triggered and high_count > 0:
            saved_projects = await discovery_service.save_discovered_projects(
                claim_id=claim_uuid,
                company_id=company_uuid,
                candidates=categorized["high_confidence"],
                user_id=user_uuid
            )
            projects_saved = len(saved_projects)
            logger.info(
                f"Auto-saved {projects_saved} high-confidence projects for claim {claim_id}"
            )

        return {
            "status": "success",
            "claim_id": claim_id,
            "auto_triggered": auto_triggered,
            "total_candidates": total_candidates,
            "high_confidence": high_count,
            "medium_confidence": medium_count,
            "low_confidence": low_count,
            "projects_auto_saved": projects_saved
        }


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
