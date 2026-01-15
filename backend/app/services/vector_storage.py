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
        model: str,
        company_id: UUID
    ) -> int:
        """
        Store embeddings for document chunks using raw SQL with tenant isolation.

        Args:
            chunk_ids: List of chunk UUIDs
            embeddings: List of embedding vectors (must match chunk_ids length)
            model: Name of the embedding model used
            company_id: Company ID for tenant isolation (REQUIRED)

        Returns:
            Number of chunks updated

        Raises:
            ValueError: If chunk_ids and embeddings lengths don't match
            ValueError: If any chunks don't belong to the specified company
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
                # First, verify all chunks belong to the specified company
                # This prevents cross-tenant embedding manipulation
                verification_query = """
                    SELECT dc.id
                    FROM bc_legal_ds.document_chunks dc
                    JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                    JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                    WHERE dc.id = ANY($1::uuid[])
                    AND m.company_id = $2
                """
                valid_chunks = await conn.fetch(
                    verification_query,
                    chunk_ids,
                    company_id
                )
                valid_chunk_ids = {row["id"] for row in valid_chunks}

                # Check if all requested chunks are valid
                invalid_chunks = set(chunk_ids) - valid_chunk_ids
                if invalid_chunks:
                    raise ValueError(
                        f"Chunks do not belong to company or do not exist: {invalid_chunks}"
                    )

                # Batch update all chunks with their embeddings
                await conn.executemany(
                    """
                    UPDATE bc_legal_ds.document_chunks
                    SET embedding = $1::vector(1536),
                        embedding_model = $2
                    WHERE id = $3
                    """,
                    [(embedding, model, chunk_id)
                     for chunk_id, embedding in zip(chunk_ids, embeddings)]
                )

                logger.info(
                    f"Stored {len(chunk_ids)} embeddings for model {model} (company: {company_id})"
                )
                return len(chunk_ids)

        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}", exc_info=True)
            raise

    async def get_embeddings(
        self,
        document_id: UUID,
        company_id: UUID
    ) -> List[dict]:
        """
        Retrieve all embeddings for a document with tenant isolation.

        Args:
            document_id: UUID of the document
            company_id: Company ID for tenant isolation (REQUIRED)

        Returns:
            List of dicts with chunk_id, embedding, and embedding_model
        """
        pool = await self.get_pool()

        try:
            async with pool.acquire() as conn:
                # Join through documents and matters to verify company ownership
                rows = await conn.fetch(
                    """
                    SELECT dc.id, dc.embedding, dc.embedding_model
                    FROM bc_legal_ds.document_chunks dc
                    JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                    JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                    WHERE dc.document_id = $1
                    AND m.company_id = $2
                    AND dc.embedding IS NOT NULL
                    ORDER BY dc.chunk_index
                    """,
                    document_id,
                    company_id
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

    async def keyword_search(
        self,
        query: str,
        company_id: UUID,
        matter_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[dict]:
        """
        Perform keyword-only search using PostgreSQL full-text search (BM25-style ranking).

        Args:
            query: Search query text
            company_id: Company ID for tenant isolation (REQUIRED)
            matter_id: Optional matter ID to further filter results
            limit: Maximum number of results to return

        Returns:
            List of dicts with chunk info and keyword score
        """
        pool = await self.get_pool()

        try:
            async with pool.acquire() as conn:
                if matter_id:
                    query_sql = """
                        SELECT
                            dc.id,
                            dc.document_id,
                            dc.content,
                            dc.chunk_index,
                            ts_rank_cd(dc.search_vector, plainto_tsquery('english', $1), 32) as keyword_score
                        FROM bc_legal_ds.document_chunks dc
                        JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                        JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                        WHERE m.company_id = $2
                        AND d.claim_id = $3
                        AND dc.search_vector IS NOT NULL
                        AND dc.search_vector @@ plainto_tsquery('english', $1)
                        ORDER BY keyword_score DESC
                        LIMIT $4
                    """
                    rows = await conn.fetch(query_sql, query, company_id, matter_id, limit)
                else:
                    query_sql = """
                        SELECT
                            dc.id,
                            dc.document_id,
                            dc.content,
                            dc.chunk_index,
                            ts_rank_cd(dc.search_vector, plainto_tsquery('english', $1), 32) as keyword_score
                        FROM bc_legal_ds.document_chunks dc
                        JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                        JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                        WHERE m.company_id = $2
                        AND dc.search_vector IS NOT NULL
                        AND dc.search_vector @@ plainto_tsquery('english', $1)
                        ORDER BY keyword_score DESC
                        LIMIT $3
                    """
                    rows = await conn.fetch(query_sql, query, company_id, limit)

                # Normalize keyword scores (0-1 range)
                if rows:
                    max_score = max(row["keyword_score"] for row in rows) or 1
                    return [
                        {
                            "chunk_id": row["id"],
                            "document_id": row["document_id"],
                            "content": row["content"],
                            "chunk_index": row["chunk_index"],
                            "similarity": float(row["keyword_score"]) / max_score,
                            "keyword_score": float(row["keyword_score"]) / max_score
                        }
                        for row in rows
                    ]
                return []

        except Exception as e:
            logger.error(f"Error performing keyword search: {str(e)}", exc_info=True)
            raise

    async def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        company_id: UUID,
        matter_id: Optional[UUID] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7
    ) -> List[dict]:
        """
        Perform hybrid search combining semantic similarity and BM25 keyword matching.

        Uses Reciprocal Rank Fusion (RRF) to combine scores from both methods.
        This ensures exact term matches (e.g., "Section 12.3", "Smith v. Jones")
        are found even when they don't match semantically.

        Args:
            query: Original search query text (for keyword matching)
            query_embedding: The query vector for semantic search
            company_id: Company ID for tenant isolation (REQUIRED)
            matter_id: Optional matter ID to further filter results
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            keyword_weight: Weight for keyword (BM25) scores (0-1)
            semantic_weight: Weight for semantic similarity scores (0-1)

        Returns:
            List of dicts with chunk info and combined score
        """
        pool = await self.get_pool()

        try:
            async with pool.acquire() as conn:
                # Convert threshold to max distance
                max_distance = (1 - similarity_threshold) * 2

                # Build the query with RRF score combination
                # RRF formula: score = sum(1 / (k + rank)) where k = 60 is standard
                # We use a simplified weighted combination of normalized scores

                if matter_id:
                    query_sql = """
                        WITH semantic_results AS (
                            SELECT
                                dc.id,
                                dc.document_id,
                                dc.content,
                                dc.chunk_index,
                                1 - (dc.embedding <=> $1::vector(1536)) / 2 as semantic_score,
                                ROW_NUMBER() OVER (ORDER BY dc.embedding <=> $1::vector(1536)) as semantic_rank
                            FROM bc_legal_ds.document_chunks dc
                            JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                            JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                            WHERE m.company_id = $2
                            AND d.claim_id = $3
                            AND dc.embedding IS NOT NULL
                            AND dc.embedding <=> $1::vector(1536) < $4
                            LIMIT $5 * 2
                        ),
                        keyword_results AS (
                            SELECT
                                dc.id,
                                dc.document_id,
                                dc.content,
                                dc.chunk_index,
                                ts_rank_cd(dc.search_vector, plainto_tsquery('english', $6), 32) as keyword_score,
                                ROW_NUMBER() OVER (ORDER BY ts_rank_cd(dc.search_vector, plainto_tsquery('english', $6), 32) DESC) as keyword_rank
                            FROM bc_legal_ds.document_chunks dc
                            JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                            JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                            WHERE m.company_id = $2
                            AND d.claim_id = $3
                            AND dc.search_vector IS NOT NULL
                            AND dc.search_vector @@ plainto_tsquery('english', $6)
                            LIMIT $5 * 2
                        ),
                        combined AS (
                            SELECT
                                COALESCE(s.id, k.id) as id,
                                COALESCE(s.document_id, k.document_id) as document_id,
                                COALESCE(s.content, k.content) as content,
                                COALESCE(s.chunk_index, k.chunk_index) as chunk_index,
                                COALESCE(s.semantic_score, 0) as semantic_score,
                                COALESCE(k.keyword_score, 0) as keyword_score,
                                -- RRF-style combination with weights
                                (
                                    $7 * COALESCE(1.0 / (60 + s.semantic_rank), 0) +
                                    $8 * COALESCE(1.0 / (60 + k.keyword_rank), 0)
                                ) as rrf_score,
                                -- Weighted linear combination for display
                                (
                                    $7 * COALESCE(s.semantic_score, 0) +
                                    $8 * COALESCE(k.keyword_score / NULLIF((SELECT MAX(keyword_score) FROM keyword_results), 0), 0)
                                ) as combined_score
                            FROM semantic_results s
                            FULL OUTER JOIN keyword_results k ON s.id = k.id
                        )
                        SELECT
                            id,
                            document_id,
                            content,
                            chunk_index,
                            semantic_score,
                            keyword_score,
                            combined_score
                        FROM combined
                        ORDER BY rrf_score DESC
                        LIMIT $5
                    """
                    rows = await conn.fetch(
                        query_sql,
                        query_embedding,  # $1
                        company_id,       # $2
                        matter_id,        # $3
                        max_distance,     # $4
                        limit,            # $5
                        query,            # $6
                        semantic_weight,  # $7
                        keyword_weight    # $8
                    )
                else:
                    query_sql = """
                        WITH semantic_results AS (
                            SELECT
                                dc.id,
                                dc.document_id,
                                dc.content,
                                dc.chunk_index,
                                1 - (dc.embedding <=> $1::vector(1536)) / 2 as semantic_score,
                                ROW_NUMBER() OVER (ORDER BY dc.embedding <=> $1::vector(1536)) as semantic_rank
                            FROM bc_legal_ds.document_chunks dc
                            JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                            JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                            WHERE m.company_id = $2
                            AND dc.embedding IS NOT NULL
                            AND dc.embedding <=> $1::vector(1536) < $3
                            LIMIT $4 * 2
                        ),
                        keyword_results AS (
                            SELECT
                                dc.id,
                                dc.document_id,
                                dc.content,
                                dc.chunk_index,
                                ts_rank_cd(dc.search_vector, plainto_tsquery('english', $5), 32) as keyword_score,
                                ROW_NUMBER() OVER (ORDER BY ts_rank_cd(dc.search_vector, plainto_tsquery('english', $5), 32) DESC) as keyword_rank
                            FROM bc_legal_ds.document_chunks dc
                            JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                            JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                            WHERE m.company_id = $2
                            AND dc.search_vector IS NOT NULL
                            AND dc.search_vector @@ plainto_tsquery('english', $5)
                            LIMIT $4 * 2
                        ),
                        combined AS (
                            SELECT
                                COALESCE(s.id, k.id) as id,
                                COALESCE(s.document_id, k.document_id) as document_id,
                                COALESCE(s.content, k.content) as content,
                                COALESCE(s.chunk_index, k.chunk_index) as chunk_index,
                                COALESCE(s.semantic_score, 0) as semantic_score,
                                COALESCE(k.keyword_score, 0) as keyword_score,
                                -- RRF-style combination with weights
                                (
                                    $6 * COALESCE(1.0 / (60 + s.semantic_rank), 0) +
                                    $7 * COALESCE(1.0 / (60 + k.keyword_rank), 0)
                                ) as rrf_score,
                                -- Weighted linear combination for display
                                (
                                    $6 * COALESCE(s.semantic_score, 0) +
                                    $7 * COALESCE(k.keyword_score / NULLIF((SELECT MAX(keyword_score) FROM keyword_results), 0), 0)
                                ) as combined_score
                            FROM semantic_results s
                            FULL OUTER JOIN keyword_results k ON s.id = k.id
                        )
                        SELECT
                            id,
                            document_id,
                            content,
                            chunk_index,
                            semantic_score,
                            keyword_score,
                            combined_score
                        FROM combined
                        ORDER BY rrf_score DESC
                        LIMIT $4
                    """
                    rows = await conn.fetch(
                        query_sql,
                        query_embedding,  # $1
                        company_id,       # $2
                        max_distance,     # $3
                        limit,            # $4
                        query,            # $5
                        semantic_weight,  # $6
                        keyword_weight    # $7
                    )

                return [
                    {
                        "chunk_id": row["id"],
                        "document_id": row["document_id"],
                        "content": row["content"],
                        "chunk_index": row["chunk_index"],
                        "similarity": float(row["combined_score"]),
                        "semantic_score": float(row["semantic_score"]),
                        "keyword_score": float(row["keyword_score"])
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Error performing hybrid search: {str(e)}", exc_info=True)
            raise

    async def similarity_search(
        self,
        query_embedding: List[float],
        company_id: UUID,
        matter_id: Optional[UUID] = None,
        limit: int = 10,
        similarity_threshold: float = 0.8
    ) -> List[dict]:
        """
        Perform similarity search using cosine distance.

        Args:
            query_embedding: The query vector to search for
            company_id: Company ID for tenant isolation (REQUIRED)
            matter_id: Optional matter ID to further filter results
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
                    # Filter by both company_id AND matter_id
                    query = """
                        SELECT
                            dc.id,
                            dc.document_id,
                            dc.content,
                            dc.chunk_index,
                            1 - (dc.embedding <=> $1::vector(1536)) / 2 as similarity
                        FROM bc_legal_ds.document_chunks dc
                        JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                        JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                        WHERE m.company_id = $2
                        AND d.claim_id = $3
                        AND dc.embedding IS NOT NULL
                        AND dc.embedding <=> $1::vector(1536) < $4
                        ORDER BY dc.embedding <=> $1::vector(1536)
                        LIMIT $5
                    """
                    rows = await conn.fetch(
                        query, query_embedding, company_id, matter_id, max_distance, limit
                    )
                else:
                    # Filter by company_id only (search across all company's documents)
                    query = """
                        SELECT
                            dc.id,
                            dc.document_id,
                            dc.content,
                            dc.chunk_index,
                            1 - (dc.embedding <=> $1::vector(1536)) / 2 as similarity
                        FROM bc_legal_ds.document_chunks dc
                        JOIN bc_legal_ds.documents d ON d.id = dc.document_id
                        JOIN bc_legal_ds.claims m ON m.id = d.claim_id
                        WHERE m.company_id = $2
                        AND dc.embedding IS NOT NULL
                        AND dc.embedding <=> $1::vector(1536) < $3
                        ORDER BY dc.embedding <=> $1::vector(1536)
                        LIMIT $4
                    """
                    rows = await conn.fetch(
                        query, query_embedding, company_id, max_distance, limit
                    )

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
