"""
Semantic chunking service for legal documents.

Intelligently splits document text into semantic chunks optimized for RAG retrieval.
Uses paragraph boundaries, section headers, and page markers instead of fixed-size chunking.
"""

import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a semantic chunk of document text."""
    content: str
    chunk_index: int
    metadata: Dict
    token_count: int
    char_count: int
    start_char: int
    end_char: int


class ChunkingService:
    """Service for semantic document chunking optimized for legal documents."""

    # Target token range for chunks (will vary based on content boundaries)
    MIN_CHUNK_TOKENS = 100
    TARGET_CHUNK_TOKENS = 500
    MAX_CHUNK_TOKENS = 800

    # Character overlap between chunks to preserve context
    OVERLAP_CHARS = 100

    # Legal document section patterns
    SECTION_PATTERNS = [
        r'^ARTICLE\s+[IVXLCDM\d]+',  # ARTICLE I, ARTICLE 1
        r'^Section\s+\d+\.?\d*',      # Section 1, Section 2.1
        r'^\d+\.\s+[A-Z]',            # 1. INTRODUCTION
        r'^[A-Z][A-Z\s]{10,}:?$',     # ALL CAPS HEADERS
        r'^\([a-z]\)',                # (a) subsection
        r'^\([ivxlcdm]+\)',           # (i) roman numeral subsection
    ]

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for text.
        Rough estimate: ~4 characters per token for English text.
        """
        # Remove extra whitespace for more accurate counting
        cleaned = ' '.join(text.split())
        return len(cleaned) // 4

    @staticmethod
    def detect_page_markers(text: str) -> List[tuple]:
        """
        Extract page markers and their positions from text.
        Page markers are in format: [Page N]

        Returns list of (page_number, char_position) tuples.
        """
        page_markers = []
        for match in re.finditer(r'\[Page (\d+)\]', text):
            page_num = int(match.group(1))
            position = match.start()
            page_markers.append((page_num, position))

        return page_markers

    @staticmethod
    def get_page_for_position(position: int, page_markers: List[tuple]) -> int:
        """
        Determine which page a character position belongs to.

        Args:
            position: Character position in text
            page_markers: List of (page_number, char_position) tuples

        Returns:
            Page number (1-indexed), or 1 if no page markers found
        """
        if not page_markers:
            return 1

        # Find the most recent page marker before this position
        current_page = 1
        for page_num, marker_pos in page_markers:
            if marker_pos <= position:
                current_page = page_num
            else:
                break

        return current_page

    @staticmethod
    def detect_section_header(line: str) -> Optional[str]:
        """
        Determine if a line is a section header.

        Returns the section title if it's a header, None otherwise.
        """
        line = line.strip()

        if not line:
            return None

        # Check against section patterns
        for pattern in ChunkingService.SECTION_PATTERNS:
            if re.match(pattern, line):
                return line

        # Check for all-caps lines (common in legal docs)
        if len(line) > 10 and line.isupper() and not line.endswith('.'):
            return line

        return None

    @staticmethod
    def split_into_paragraphs(text: str) -> List[Dict]:
        """
        Split text into paragraphs while preserving metadata.

        Returns list of dicts with:
        - content: paragraph text
        - start_char: starting position
        - end_char: ending position
        - is_header: whether this is likely a section header
        """
        paragraphs = []

        # Split on double newlines (paragraph boundaries)
        raw_paragraphs = re.split(r'\n\s*\n', text)

        current_pos = 0
        for para_text in raw_paragraphs:
            para_text = para_text.strip()

            if not para_text:
                continue

            # Find the actual position in original text
            start = text.find(para_text, current_pos)
            end = start + len(para_text)

            # Detect if this is a section header
            is_header = ChunkingService.detect_section_header(para_text) is not None

            paragraphs.append({
                'content': para_text,
                'start_char': start,
                'end_char': end,
                'is_header': is_header
            })

            current_pos = end

        return paragraphs

    def chunk_text(
        self,
        text: str,
        document_id: str = None,
        preserve_page_markers: bool = False
    ) -> List[Chunk]:
        """
        Chunk text using semantic boundaries (paragraphs, sections).

        Args:
            text: Full document text to chunk
            document_id: Optional document ID for logging
            preserve_page_markers: If True, keep [Page N] markers in chunk text

        Returns:
            List of Chunk objects with content and metadata
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided for chunking (document: {document_id})")
            return []

        # Detect page markers for citation tracking
        page_markers = self.detect_page_markers(text)

        # Split into paragraphs
        paragraphs = self.split_into_paragraphs(text)

        if not paragraphs:
            logger.warning(f"No paragraphs found in text (document: {document_id})")
            return []

        chunks = []
        current_chunk_paragraphs = []
        current_chunk_tokens = 0
        current_section_header = None
        chunk_start_char = paragraphs[0]['start_char']

        for i, para in enumerate(paragraphs):
            para_text = para['content']
            para_tokens = self.estimate_tokens(para_text)

            # Check if this is a section header
            if para['is_header']:
                current_section_header = para_text

            # Decision: Should we start a new chunk?
            should_split = False

            # Don't split if current chunk is too small
            if current_chunk_tokens < self.MIN_CHUNK_TOKENS:
                should_split = False
            # Split if adding this para would exceed max tokens
            elif current_chunk_tokens + para_tokens > self.MAX_CHUNK_TOKENS:
                should_split = True
            # Split at section headers if we're above target size
            elif para['is_header'] and current_chunk_tokens >= self.TARGET_CHUNK_TOKENS:
                should_split = True

            if should_split and current_chunk_paragraphs:
                # Create chunk from accumulated paragraphs
                chunk_text = '\n\n'.join([p['content'] for p in current_chunk_paragraphs])
                chunk_end_char = current_chunk_paragraphs[-1]['end_char']

                # Remove page markers from chunk text if requested
                if not preserve_page_markers:
                    chunk_text = re.sub(r'\[Page \d+\]\n?', '', chunk_text)

                # Determine page range for this chunk
                start_page = self.get_page_for_position(chunk_start_char, page_markers)
                end_page = self.get_page_for_position(chunk_end_char, page_markers)

                chunk = Chunk(
                    content=chunk_text.strip(),
                    chunk_index=len(chunks),
                    metadata={
                        'start_page': start_page,
                        'end_page': end_page,
                        'section': current_section_header,
                        'paragraph_count': len(current_chunk_paragraphs),
                        'has_section_header': any(p['is_header'] for p in current_chunk_paragraphs)
                    },
                    token_count=current_chunk_tokens,
                    char_count=len(chunk_text),
                    start_char=chunk_start_char,
                    end_char=chunk_end_char
                )

                chunks.append(chunk)

                # Start new chunk with overlap (last paragraph for context)
                if len(current_chunk_paragraphs) > 1:
                    # Include last paragraph for context continuity
                    overlap_para = current_chunk_paragraphs[-1]
                    current_chunk_paragraphs = [overlap_para, para]
                    current_chunk_tokens = self.estimate_tokens(overlap_para['content']) + para_tokens
                    chunk_start_char = overlap_para['start_char']
                else:
                    current_chunk_paragraphs = [para]
                    current_chunk_tokens = para_tokens
                    chunk_start_char = para['start_char']
            else:
                # Add paragraph to current chunk
                current_chunk_paragraphs.append(para)
                current_chunk_tokens += para_tokens

        # Add final chunk if there's content remaining
        if current_chunk_paragraphs:
            chunk_text = '\n\n'.join([p['content'] for p in current_chunk_paragraphs])
            chunk_end_char = current_chunk_paragraphs[-1]['end_char']

            if not preserve_page_markers:
                chunk_text = re.sub(r'\[Page \d+\]\n?', '', chunk_text)

            start_page = self.get_page_for_position(chunk_start_char, page_markers)
            end_page = self.get_page_for_position(chunk_end_char, page_markers)

            chunk = Chunk(
                content=chunk_text.strip(),
                chunk_index=len(chunks),
                metadata={
                    'start_page': start_page,
                    'end_page': end_page,
                    'section': current_section_header,
                    'paragraph_count': len(current_chunk_paragraphs),
                    'has_section_header': any(p['is_header'] for p in current_chunk_paragraphs)
                },
                token_count=current_chunk_tokens,
                char_count=len(chunk_text),
                start_char=chunk_start_char,
                end_char=chunk_end_char
            )

            chunks.append(chunk)

        logger.info(
            f"Created {len(chunks)} chunks from text "
            f"(document: {document_id}, avg tokens: {sum(c.token_count for c in chunks) / len(chunks):.0f})"
        )

        return chunks


# Singleton instance
chunking_service = ChunkingService()
