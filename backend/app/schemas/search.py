# app/schemas/search.py - Search request and response schemas

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    """Request schema for semantic search"""
    query: str = Field(..., min_length=1, description="Search query in natural language")
    matter_id: Optional[UUID] = Field(None, description="Filter results to specific matter")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results to return")
    similarity_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1, where 1 is identical)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the terms of the employment contract?",
                "matter_id": "123e4567-e89b-12d3-a456-426614174000",
                "limit": 10,
                "similarity_threshold": 0.7
            }
        }


class SearchResultChunk(BaseModel):
    """Individual search result chunk with document metadata"""
    chunk_id: UUID = Field(..., description="Unique chunk identifier")
    document_id: UUID = Field(..., description="Document this chunk belongs to")
    content: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., description="Position of this chunk in the document")
    similarity_score: float = Field(..., description="Similarity score (0-1)")

    # Document metadata
    document_title: str = Field(..., description="Document title")
    document_type: str = Field(..., description="Document type")
    document_date: Optional[datetime] = Field(None, description="Document date")
    matter_id: UUID = Field(..., description="Matter this document belongs to")
    matter_name: str = Field(..., description="Matter name")

    # Chunk metadata
    page_number: Optional[int] = Field(None, description="Page number where chunk appears")
    start_char: Optional[int] = Field(None, description="Starting character position")
    end_char: Optional[int] = Field(None, description="Ending character position")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "123e4567-e89b-12d3-a456-426614174001",
                "document_id": "123e4567-e89b-12d3-a456-426614174002",
                "content": "The employee shall receive an annual salary of $80,000...",
                "chunk_index": 5,
                "similarity_score": 0.89,
                "document_title": "Employment Contract - John Doe",
                "document_type": "Contract",
                "document_date": "2024-01-15T00:00:00",
                "matter_id": "123e4567-e89b-12d3-a456-426614174000",
                "matter_name": "Doe v. Acme Corp",
                "page_number": 3,
                "start_char": 1250,
                "end_char": 1850
            }
        }


class SemanticSearchResponse(BaseModel):
    """Response schema for semantic search"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResultChunk] = Field(..., description="List of matching chunks")
    total_results: int = Field(..., description="Number of results returned")
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the terms of the employment contract?",
                "results": [],
                "total_results": 5,
                "search_time_ms": 123.45
            }
        }
