"""
Document processing service for RAG pipeline.

Handles text extraction, chunking, and embedding generation for documents.
Integrates with the document_processing_queue for async task management.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Document, DocumentChunk
from app.services.text_extraction import text_extraction_service
from app.services.storage import storage_service
from app.services.chunking import chunking_service
from app.services.embeddings import embedding_service
from app.services.vector_storage import vector_storage_service

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing documents through the RAG pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_text_extraction(self, document_id: UUID) -> bool:
        """
        Extract text from a document and store it in the database.

        Args:
            document_id: UUID of the document to process

        Returns:
            True if extraction succeeded, False otherwise
        """
        try:
            # Get document from database
            query = select(Document).where(Document.id == document_id)
            result = await self.db.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                logger.error(f"Document {document_id} not found")
                return False

            # Check if already extracted
            if document.text_extracted:
                logger.info(f"Document {document_id} already has extracted text")
                return True

            # Download file from storage
            logger.info(f"Downloading document {document_id} from S3: {document.storage_path}")
            file_content = await storage_service.download_file(document.storage_path)

            if not file_content:
                error_msg = "Failed to download file from storage"
                logger.error(f"Document {document_id}: {error_msg}")
                await self._mark_extraction_failed(document, error_msg)
                return False

            # Extract text
            logger.info(f"Extracting text from document {document_id} ({document.filename})")
            extraction_result = text_extraction_service.extract_text(
                file_content=file_content,
                filename=document.filename,
                mime_type=document.mime_type
            )

            if extraction_result['success']:
                # Update document with extracted text
                await self._save_extraction_results(document, extraction_result)
                logger.info(
                    f"Successfully extracted text from document {document_id}: "
                    f"{extraction_result['metadata'].get('word_count', 0)} words, "
                    f"{extraction_result['metadata'].get('page_count', 0)} pages"
                )
                return True
            else:
                # Mark extraction as failed
                error_msg = extraction_result.get('error', 'Unknown extraction error')
                logger.error(f"Document {document_id} extraction failed: {error_msg}")
                await self._mark_extraction_failed(document, error_msg)
                return False

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            try:
                # Try to mark as failed in database
                query = select(Document).where(Document.id == document_id)
                result = await self.db.execute(query)
                document = result.scalar_one_or_none()
                if document:
                    await self._mark_extraction_failed(document, str(e))
            except Exception as db_error:
                logger.error(f"Failed to mark document as failed: {str(db_error)}")
            return False

    async def _save_extraction_results(
        self,
        document: Document,
        extraction_result: dict
    ) -> None:
        """Save extraction results to the document."""
        metadata = extraction_result.get('metadata', {})

        # Update document fields
        document.extracted_text = extraction_result['text']
        document.page_count = metadata.get('page_count')
        document.word_count = metadata.get('word_count')
        document.extraction_method = metadata.get('extraction_method')
        document.extraction_date = datetime.now(timezone.utc)
        document.text_extracted = True
        document.processing_status = 'text_extracted'
        document.extraction_error = None

        # Commit changes
        await self.db.commit()
        await self.db.refresh(document)

        # NOTE: Automatic chunking removed due to greenlet context issues
        # Chunking will be triggered separately via background task queue
        # or manual trigger to avoid SQLAlchemy transaction conflicts

    async def _mark_extraction_failed(
        self,
        document: Document,
        error_message: str
    ) -> None:
        """Mark document extraction as failed."""
        document.text_extracted = False
        document.processing_status = 'extraction_failed'
        document.extraction_error = error_message
        document.extraction_date = datetime.now(timezone.utc)

        # Commit changes
        await self.db.commit()
        await self.db.refresh(document)

    async def process_chunking(self, document_id: UUID) -> bool:
        """
        Create semantic chunks from document text.

        Args:
            document_id: UUID of the document to chunk

        Returns:
            True if chunking succeeded, False otherwise
        """
        try:
            # Get document from database
            query = select(Document).where(Document.id == document_id)
            result = await self.db.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                logger.error(f"Document {document_id} not found")
                return False

            # Check if text has been extracted
            if not document.text_extracted or not document.extracted_text:
                logger.error(f"Document {document_id} has no extracted text")
                return False

            # Check if already chunked by checking processing status
            # (Avoid async DB calls here to prevent greenlet context issues)
            if document.processing_status in ['chunked', 'embedded']:
                logger.info(f"Document {document_id} already chunked (status: {document.processing_status}), skipping")
                return True

            # Chunk the text
            logger.info(f"Chunking document {document_id} ({document.filename})")
            chunks = chunking_service.chunk_text(
                text=document.extracted_text,
                document_id=str(document_id)
            )

            if not chunks:
                logger.warning(f"No chunks created for document {document_id}")
                return False

            # Save chunks to database
            for chunk in chunks:
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    chunk_metadata=chunk.metadata,
                    token_count=chunk.token_count,
                    char_count=chunk.char_count,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char
                    # Embeddings will be added in the next pipeline step
                )
                self.db.add(db_chunk)

            # Update document status
            document.processing_status = 'chunked'
            document.indexed_for_search = False  # Not yet embedded

            await self.db.commit()

            logger.info(
                f"Successfully chunked document {document_id}: "
                f"{len(chunks)} chunks created"
            )

            # NOTE: Automatic embedding generation removed due to greenlet context issues
            # Embedding generation will be triggered separately via background task queue
            # or manual trigger to avoid SQLAlchemy transaction conflicts

            return True

        except Exception as e:
            logger.error(f"Error chunking document {document_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            return False

    async def process_embeddings(self, document_id: UUID) -> bool:
        """
        Generate embeddings for all chunks of a document.

        Uses ORM for document/chunk retrieval and raw SQL for vector storage.

        Args:
            document_id: UUID of the document to generate embeddings for

        Returns:
            True if embedding generation succeeded, False otherwise
        """
        try:
            # Get document from database (ORM)
            query = select(Document).where(Document.id == document_id)
            result = await self.db.execute(query)
            document = result.scalar_one_or_none()

            if not document:
                logger.error(f"Document {document_id} not found")
                return False

            # Check if document has been chunked
            if document.processing_status not in ['chunked', 'embedded']:
                logger.error(
                    f"Document {document_id} must be chunked before generating embeddings "
                    f"(current status: {document.processing_status})"
                )
                return False

            # Get all chunks for this document (ORM - but don't load embedding column)
            chunks_query = select(
                DocumentChunk.id,
                DocumentChunk.content,
                DocumentChunk.chunk_index
            ).where(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index)
            chunks_result = await self.db.execute(chunks_query)
            chunks = chunks_result.all()

            if not chunks:
                logger.warning(f"No chunks found for document {document_id}")
                return False

            # Check if already embedded (via raw SQL to avoid loading vector column)
            try:
                pool = await vector_storage_service.get_pool()
                async with pool.acquire() as conn:
                    first_chunk = await conn.fetchrow(
                        "SELECT embedding FROM document_chunks WHERE id = $1",
                        chunks[0].id
                    )
                    if first_chunk and first_chunk['embedding'] is not None:
                        logger.info(f"Document {document_id} chunks already have embeddings, skipping")
                        return True
            except Exception as check_error:
                logger.warning(f"Could not check existing embeddings: {str(check_error)}")

            # Extract text content from chunks
            chunk_texts = [chunk.content for chunk in chunks]
            chunk_ids = [chunk.id for chunk in chunks]

            # Generate embeddings in batch
            logger.info(
                f"Generating embeddings for {len(chunks)} chunks of document {document_id}"
            )
            embeddings = embedding_service.generate_embeddings_batch(chunk_texts)

            # Get embedding metadata
            embedding_metadata = embedding_service.get_embedding_metadata()
            embedding_model = embedding_metadata['model']

            # Store embeddings using raw SQL (bypasses ORM vector type issues)
            await vector_storage_service.store_embeddings(
                chunk_ids=chunk_ids,
                embeddings=embeddings,
                model=embedding_model
            )

            # Update document status (ORM)
            document.processing_status = 'embedded'
            document.indexed_for_search = True
            await self.db.commit()

            logger.info(
                f"Successfully generated embeddings for document {document_id}: "
                f"{len(embeddings)} chunks embedded with model {embedding_model}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error generating embeddings for document {document_id}: {str(e)}",
                exc_info=True
            )
            await self.db.rollback()
            return False

    async def get_document_status(self, document_id: UUID) -> Optional[dict]:
        """
        Get processing status for a document.

        Returns:
            Dictionary with processing status information
        """
        query = select(Document).where(Document.id == document_id)
        result = await self.db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            return None

        return {
            'document_id': str(document.id),
            'filename': document.filename,
            'processing_status': document.processing_status,
            'text_extracted': document.text_extracted,
            'page_count': document.page_count,
            'word_count': document.word_count,
            'extraction_method': document.extraction_method,
            'extraction_date': document.extraction_date.isoformat() if document.extraction_date else None,
            'extraction_error': document.extraction_error
        }


# Singleton instance factory
def get_document_processor(db: AsyncSession) -> DocumentProcessor:
    """Get a DocumentProcessor instance with database session."""
    return DocumentProcessor(db)

