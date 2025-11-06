"""
Vector storage service using raw asyncpg for pgvector operations.

This bypasses SQLAlchemy ORM for vector operations to avoid type registration issues.
All other database operations continue to use the ORM normally.
"""

import logging
from typing import List, Optional
from uuid import UUID

import asyncpg
from pgvector.asyncpg import register_vector

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStorageService:
    """Service for storing and retrieving vector embeddings using raw SQL."""

    def __init__(self):
        """Initialize the vector storage service."""
        self._pool: Optional[asyncpg.Pool] = None

    async def get_pool(self) -> asyncpg.Pool:
        """Get or create the asyncpg connection pool."""
        if self._pool is None:
            # Strip +asyncpg dialect from DATABASE_URL for raw asyncpg connection
            db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

            # Create connection pool
            self._pool = await asyncpg.create_pool(
                db_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
                # Setup function to register vector type on each connection
                init=self._init_connection
            )
            logger.info("Created asyncpg connection pool for vector operations")

        return self._pool

    async def _init_connection(self, conn: asyncpg.Connection):
        """Initialize a new connection by registering the vector type."""
        await register_vector(conn)
        logger.debug("Registered pgvector type on connection")

    async def store_embeddings(
        self,
        chunk_ids: List[UUID],
        embeddings: List[List[float]],
        model: str
    ) -> int:
        """
        Store embeddings for document chunks using raw SQL.

        Args:
            chunk_ids: List of chunk UUIDs
            embeddings: List of embedding vectors (must match chunk_ids length)
            model: Name of the embedding model used

        Returns:
            Number of chunks updated

        Raises:
            ValueError: If chunk_ids and embeddings lengths don't match
        """
        if len(chunk_ids) != len(embeddings):
            raise ValueError(
                f"Chunk IDs ({len(chunk_ids)}) and embeddings ({len(embeddings)}) "
                "must have the same length"
            )

        if not chunk_ids:
            return 0

        pool = await self.get_pool()

        try:
            async with pool.acquire() as conn:
                # Batch update all chunks with their embeddings
                updated = await conn.executemany(
                    """
                    UPDATE document_chunks
                    SET embedding = $1::vector(1536),
                        embedding_model = $2
                    WHERE id = $3
                    """,
                    [(embedding, model, chunk_id)
                     for chunk_id, embedding in zip(chunk_ids, embeddings)]
                )

                logger.info(
                    f"Stored {len(chunk_ids)} embeddings for model {model}"
                )
                return len(chunk_ids)

        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}", exc_info=True)
            raise

    async def get_embeddings(
        self,
        document_id: UUID
    ) -> List[dict]:
        """
        Retrieve all embeddings for a document.

        Args:
            document_id: UUID of the document

        Returns:
            List of dicts with chunk_id, embedding, and embedding_model
        """
        pool = await self.get_pool()

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, embedding, embedding_model
                    FROM document_chunks
                    WHERE document_id = $1
                    AND embedding IS NOT NULL
                    ORDER BY chunk_index
                    """,
                    document_id
                )

                return [
                    {
                        "chunk_id": row["id"],
                        "embedding": row["embedding"],
                        "embedding_model": row["embedding_model"]
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(
                f"Error retrieving embeddings for document {document_id}: {str(e)}",
                exc_info=True
            )
            raise

    async def similarity_search(
        self,
        query_embedding: List[float],
        matter_id: Optional[UUID] = None,
        limit: int = 10,
        similarity_threshold: float = 0.8
    ) -> List[dict]:
        """
        Perform similarity search using cosine distance.

        Args:
            query_embedding: The query vector to search for
            matter_id: Optional matter ID to filter results
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1, where 1 is identical)

        Returns:
            List of dicts with chunk info and similarity score
        """
        pool = await self.get_pool()

        try:
            async with pool.acquire() as conn:
                # Cosine distance: 0 = identical, 2 = opposite
                # Convert to similarity: 1 - (distance / 2)
                # Filter by: distance < (1 - threshold) * 2
                max_distance = (1 - similarity_threshold) * 2

                if matter_id:
                    query = """
                        SELECT
                            dc.id,
                            dc.document_id,
                            dc.content,
                            dc.chunk_index,
                            1 - (dc.embedding <=> $1::vector(1536)) / 2 as similarity
                        FROM document_chunks dc
                        JOIN documents d ON d.id = dc.document_id
                        WHERE d.matter_id = $2
                        AND dc.embedding IS NOT NULL
                        AND dc.embedding <=> $1::vector(1536) < $3
                        ORDER BY dc.embedding <=> $1::vector(1536)
                        LIMIT $4
                    """
                    rows = await conn.fetch(
                        query, query_embedding, matter_id, max_distance, limit
                    )
                else:
                    query = """
                        SELECT
                            id,
                            document_id,
                            content,
                            chunk_index,
                            1 - (embedding <=> $1::vector(1536)) / 2 as similarity
                        FROM document_chunks
                        WHERE embedding IS NOT NULL
                        AND embedding <=> $1::vector(1536) < $2
                        ORDER BY embedding <=> $1::vector(1536)
                        LIMIT $3
                    """
                    rows = await conn.fetch(query, query_embedding, max_distance, limit)

                return [
                    {
                        "chunk_id": row["id"],
                        "document_id": row["document_id"],
                        "content": row["content"],
                        "chunk_index": row["chunk_index"],
                        "similarity": float(row["similarity"])
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}", exc_info=True)
            raise

    async def close(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Closed asyncpg connection pool")
            self._pool = None


# Singleton instance
vector_storage_service = VectorStorageService()
