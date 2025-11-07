"""
Manually trigger chunking and embedding generation for a document.
"""
import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import UUID

from app.core.config import settings
from app.services.document_processor import DocumentProcessor

async def main():
    # Document ID from the test
    document_id = UUID('5969b950-f019-4a17-a0b8-38aee113405c')

    # Create async engine and session
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        processor = DocumentProcessor(session)

        # Step 1: Process chunking
        print(f"\n1. Processing chunking for document {document_id}...")
        chunking_success = await processor.process_chunking(document_id)

        if not chunking_success:
            print("   X Chunking failed!")
            return

        print("   OK Chunking completed successfully")

        # Step 2: Process embeddings
        print(f"\n2. Generating embeddings for document {document_id}...")
        embedding_success = await processor.process_embeddings(document_id)

        if not embedding_success:
            print("   X Embedding generation failed!")
            return

        print("   OK Embeddings generated successfully")

    # Verify in database
    print("\n3. Verifying in database...")
    conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))

    # Check document status
    doc = await conn.fetchrow(
        "SELECT processing_status, indexed_for_search FROM documents WHERE id = $1",
        document_id
    )
    print(f"   Document status: {doc['processing_status']}")
    print(f"   Indexed for search: {doc['indexed_for_search']}")

    # Check chunks
    chunk_count = await conn.fetchval(
        "SELECT COUNT(*) FROM document_chunks WHERE document_id = $1",
        document_id
    )
    print(f"   Chunk count: {chunk_count}")

    # Check embeddings (check if any chunk has an embedding)
    embedded_count = await conn.fetchval(
        "SELECT COUNT(*) FROM document_chunks WHERE document_id = $1 AND embedding IS NOT NULL",
        document_id
    )
    print(f"   Embedded chunks: {embedded_count}")

    await conn.close()

    if doc['processing_status'] == 'embedded' and doc['indexed_for_search'] and embedded_count == chunk_count:
        print("\n\nOK Full pipeline completed successfully!")
    else:
        print("\n\nX Pipeline incomplete or failed")

if __name__ == "__main__":
    asyncio.run(main())
