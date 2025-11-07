# app/api/v1/endpoints/search.py - Semantic search endpoints

import logging
import time
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.models import User, Document, Matter, DocumentChunk
from app.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchResultChunk
)
from app.services.embeddings import embedding_service
from app.services.vector_storage import vector_storage_service
from app.core.rate_limit import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/semantic", response_model=SemanticSearchResponse)
@limiter.limit(get_rate_limit("search_semantic"))
async def semantic_search(
    req: Request,
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic search across documents using vector similarity.

    Args:
        request: Search parameters (query, matter_id, limit, threshold)
        current_user: Authenticated user
        db: Database session

    Returns:
        Search results with document chunks and metadata
    """
    start_time = time.time()

    try:
        # Generate embedding for the search query
        logger.info(f"Generating embedding for query: '{request.query}'")
        query_embedding = embedding_service.generate_embedding(request.query)

        if not query_embedding:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query embedding"
            )

        # Perform vector similarity search
        logger.info(
            f"Searching with matter_id={request.matter_id}, "
            f"limit={request.limit}, threshold={request.similarity_threshold}"
        )

        search_results = await vector_storage_service.similarity_search(
            query_embedding=query_embedding,
            matter_id=request.matter_id,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )

        logger.info(f"Found {len(search_results)} matching chunks")

        # Enrich results with document and matter metadata
        enriched_results = await _enrich_search_results(
            search_results, db, current_user
        )

        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000

        return SemanticSearchResponse(
            query=request.query,
            results=enriched_results,
            total_results=len(enriched_results),
            search_time_ms=round(search_time_ms, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


async def _enrich_search_results(
    search_results: List[dict],
    db: AsyncSession,
    current_user: User
) -> List[SearchResultChunk]:
    """
    Enrich search results with document and matter metadata.

    Args:
        search_results: Raw search results from vector storage
        db: Database session
        current_user: Current user for access control

    Returns:
        List of enriched search result chunks
    """
    if not search_results:
        return []

    # Get unique document IDs from search results
    document_ids = list(set(result["document_id"] for result in search_results))

    # Fetch document and matter metadata in batch
    query = (
        select(Document, Matter, DocumentChunk)
        .join(Matter, Document.matter_id == Matter.id)
        .join(DocumentChunk, DocumentChunk.document_id == Document.id)
        .where(Document.id.in_(document_ids))
        .where(Document.company_id == current_user.company_id)  # Access control
    )

    result = await db.execute(query)
    rows = result.all()

    # Create lookup dictionaries
    doc_metadata = {}
    chunk_metadata = {}

    for doc, matter, chunk in rows:
        if doc.id not in doc_metadata:
            doc_metadata[doc.id] = {
                "title": doc.title,
                "type": doc.document_type,
                "date": doc.document_date,
                "matter_id": matter.id,
                "matter_name": matter.name
            }

        chunk_metadata[chunk.id] = {
            "page_number": chunk.chunk_metadata.get("page_number") if chunk.chunk_metadata else None,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char
        }

    # Enrich search results
    enriched = []
    for result in search_results:
        doc_id = result["document_id"]
        chunk_id = result["chunk_id"]

        # Skip if document metadata not found (access control filtered it out)
        if doc_id not in doc_metadata:
            continue

        doc_meta = doc_metadata[doc_id]
        chunk_meta = chunk_metadata.get(chunk_id, {})

        enriched.append(SearchResultChunk(
            chunk_id=chunk_id,
            document_id=doc_id,
            content=result["content"],
            chunk_index=result["chunk_index"],
            similarity_score=result["similarity"],
            document_title=doc_meta["title"],
            document_type=doc_meta["type"],
            document_date=doc_meta["date"],
            matter_id=doc_meta["matter_id"],
            matter_name=doc_meta["matter_name"],
            page_number=chunk_meta.get("page_number"),
            start_char=chunk_meta.get("start_char"),
            end_char=chunk_meta.get("end_char")
        ))

    return enriched
