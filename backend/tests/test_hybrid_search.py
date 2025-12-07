"""Tests for hybrid search functionality."""

import pytest
from app.schemas.search import SearchMode, SemanticSearchRequest, SemanticSearchResponse, SearchResultChunk


class TestSearchSchemas:
    """Test search schema validation."""

    def test_search_mode_enum(self):
        """Test SearchMode enum values."""
        assert SearchMode.SEMANTIC.value == "semantic"
        assert SearchMode.KEYWORD.value == "keyword"
        assert SearchMode.HYBRID.value == "hybrid"

    def test_semantic_search_request_defaults(self):
        """Test default values for SemanticSearchRequest."""
        request = SemanticSearchRequest(query="test query")

        assert request.query == "test query"
        assert request.matter_id is None
        assert request.limit == 10
        assert request.similarity_threshold == 0.7
        assert request.mode == SearchMode.HYBRID  # Default to hybrid
        assert request.keyword_weight == 0.3
        assert request.semantic_weight == 0.7

    def test_semantic_search_request_custom_mode(self):
        """Test SemanticSearchRequest with custom mode."""
        request = SemanticSearchRequest(
            query="Section 12.3",
            mode=SearchMode.KEYWORD,
            limit=20
        )

        assert request.mode == SearchMode.KEYWORD
        assert request.limit == 20

    def test_semantic_search_request_hybrid_weights(self):
        """Test SemanticSearchRequest with custom weights."""
        request = SemanticSearchRequest(
            query="contract terms",
            mode=SearchMode.HYBRID,
            keyword_weight=0.5,
            semantic_weight=0.5
        )

        assert request.keyword_weight == 0.5
        assert request.semantic_weight == 0.5

    def test_search_result_chunk_with_scores(self):
        """Test SearchResultChunk includes optional score breakdown."""
        from uuid import uuid4

        chunk = SearchResultChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Test content",
            chunk_index=0,
            similarity_score=0.85,
            semantic_score=0.9,
            keyword_score=0.7,
            document_title="Test Doc",
            document_type="Contract",
            matter_id=uuid4(),
            matter_name="Test Matter"
        )

        assert chunk.similarity_score == 0.85
        assert chunk.semantic_score == 0.9
        assert chunk.keyword_score == 0.7

    def test_search_result_chunk_without_score_breakdown(self):
        """Test SearchResultChunk works without score breakdown."""
        from uuid import uuid4

        chunk = SearchResultChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Test content",
            chunk_index=0,
            similarity_score=0.85,
            document_title="Test Doc",
            document_type="Contract",
            matter_id=uuid4(),
            matter_name="Test Matter"
        )

        assert chunk.similarity_score == 0.85
        assert chunk.semantic_score is None
        assert chunk.keyword_score is None

    def test_semantic_search_response_includes_mode(self):
        """Test SemanticSearchResponse includes search mode."""
        response = SemanticSearchResponse(
            query="test",
            mode=SearchMode.HYBRID,
            results=[],
            total_results=0,
            search_time_ms=50.0
        )

        assert response.mode == SearchMode.HYBRID


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
