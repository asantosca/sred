# BC Legal Tech - RAG Pipeline Architecture

---

Complete database schema and implementation guide for the RAG (Retrieval-Augmented Generation) pipeline.

---

## Table of Contents

1. [Database Schema Overview](#database-schema-overview)
2. [RAG Pipeline Flow](#rag-pipeline-flow)
3. [Version Control System](#version-control-system)
4. [Key Implementation Details](#key-implementation-details)
5. [Anti-Hallucination Strategy](#anti-hallucination-strategy)

---

## Database Schema Overview

### Core Tables

#### 1. **documents** (Existing - 65+ columns)

Main document storage with comprehensive metadata.

**Key Fields for RAG:**

```sql
- id (UUID) - Primary key
- matter_id (UUID) - Links to matter/case
- filename, storage_path - S3 storage info
- file_hash (SHA-256) - Deduplication
- document_type, document_subtype - Classification
- processing_status - 'pending', 'processing', 'completed', 'failed'
- text_extracted (boolean) - Has text been extracted?
- indexed_for_search (boolean) - Has embeddings been generated?

-- Version Control Fields
- is_current_version (boolean) - Is this the active version?
- version_number (integer) - Sequential version number
- version_label (string) - e.g., "v1.0", "Draft 3"
- parent_document_id (UUID) - Previous version
- root_document_id (UUID) - First version in chain
- superseded_date (date) - When this version was replaced
- change_summary (text) - What changed from previous version
```

#### 2. **document_chunks** (NEW - RAG Core)

Stores document text split into semantic chunks with vector embeddings.

**Purpose:** Enable semantic search and context retrieval for AI responses.

```sql
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,           -- Order in document (0, 1, 2...)
  content TEXT NOT NULL,                  -- Actual text chunk
  embedding VECTOR(1536),                 -- OpenAI/Voyage AI embedding
  embedding_model VARCHAR(100),           -- Which model generated this
  metadata JSONB,                         -- {page: 5, section: "Introduction"}
  token_count INTEGER,                    -- Approximate token count
  char_count INTEGER NOT NULL,            -- Character count
  start_char INTEGER,                     -- Position in original doc
  end_char INTEGER,                       -- End position
  created_at TIMESTAMP WITH TIME ZONE,

  UNIQUE(document_id, chunk_index)
);

-- Indexes
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat(embedding) WITH (lists=100);
```

**Embedding Options:**

- **OpenAI text-embedding-3-large**: 3072 dimensions (high accuracy)
- **OpenAI text-embedding-3-small**: 1536 dimensions (default, fast)
- **Voyage AI voyage-law-2**: 1024 dimensions (legal-specific, recommended)

**Metadata Structure:**

```json
{
  "page_number": 5,
  "section": "Terms and Conditions",
  "headers": ["Agreement", "Section 3"],
  "is_heading": false,
  "confidence": 0.95
}
```

#### 3. **document_relationships** (NEW - Version Control & Links)

Tracks relationships between documents.

**Purpose:** Version tracking, document dependencies, exhibit links.

```sql
CREATE TABLE document_relationships (
  id UUID PRIMARY KEY,
  source_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  target_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  relationship_type VARCHAR(50) NOT NULL,  -- See types below
  description TEXT,                        -- Optional explanation
  metadata JSONB,                          -- Additional info
  created_at TIMESTAMP WITH TIME ZONE,
  created_by UUID NOT NULL REFERENCES users(id),

  UNIQUE(source_document_id, target_document_id, relationship_type)
);
```

**Relationship Types:**

- `amendment` - Target amends source
- `supersedes` - Target replaces source (version control)
- `exhibit` - Target is exhibit to source
- `attachment` - Target is attached to source
- `response` - Target responds to source (e.g., motion response)
- `version_of` - Explicit version link

#### 4. **document_processing_queue** (NEW - Async Task Queue)

Background job queue for document processing.

**Purpose:** Async text extraction, embedding generation, OCR processing.

```sql
CREATE TABLE document_processing_queue (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  task_type VARCHAR(50) NOT NULL,         -- See types below
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  priority INTEGER NOT NULL DEFAULT 5,    -- 1-10, lower = higher priority
  attempts INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  error_message TEXT,
  result_data JSONB,                      -- Task output/metadata
  created_at TIMESTAMP WITH TIME ZONE,
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  worker_id VARCHAR(100),                 -- Which worker is processing

  INDEX idx_queue_status_priority(status, priority, created_at)
);
```

**Task Types:**

- `extract_text` - Extract text from PDF/DOCX
- `generate_embeddings` - Create vector embeddings
- `ocr` - OCR for scanned documents
- `analyze` - Auto-detection, classification
- `reprocess` - Re-run failed task

**Status Values:**

- `pending` - Waiting to be processed
- `processing` - Currently being processed
- `completed` - Successfully completed
- `failed` - Failed after max attempts

---

## RAG Pipeline Flow

### Document Upload → Retrieval → AI Response

```
┌─────────────────────────────────────────────────────────────────┐
│                      1. DOCUMENT UPLOAD                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         POST /api/v1/documents/upload/standard
         - User uploads PDF/DOCX
         - File saved to S3
         - Document record created
         - processing_status = 'pending'
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                2. QUEUE TEXT EXTRACTION TASK                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         INSERT INTO document_processing_queue
         - task_type = 'extract_text'
         - priority = 5 (normal)
         - status = 'pending'
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              3. BACKGROUND WORKER: TEXT EXTRACTION               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         Celery Worker picks up task
         - PDF: pdfplumber.extract_text()
         - DOCX: python-docx Document().paragraphs
         - TXT: direct read
         - Store full text temporarily
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  4. SEMANTIC CHUNKING                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         Intelligent text splitting
         - NOT fixed-size (e.g., 512 tokens)
         - Split on paragraph/section boundaries
         - Preserve context (headers, page numbers)
         - Overlap: 50-100 chars between chunks
         - Target: 300-800 tokens per chunk
                              ↓
         INSERT INTO document_chunks (multiple rows)
         - chunk_index = 0, 1, 2...
         - content = chunk text
         - metadata = {page, section, headers}
         - embedding = NULL (not yet generated)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              5. QUEUE EMBEDDING GENERATION                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         INSERT INTO document_processing_queue
         - task_type = 'generate_embeddings'
         - For each chunk
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           6. BACKGROUND WORKER: GENERATE EMBEDDINGS              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         Batch process chunks (e.g., 100 at a time)
         - Call OpenAI API or Voyage AI API
         - Generate vector embeddings
         - UPDATE document_chunks SET embedding = [...]
                              ↓
         UPDATE documents
         - text_extracted = TRUE
         - indexed_for_search = TRUE
         - processing_status = 'completed'
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  7. USER ASKS QUESTION                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         POST /api/v1/chat/messages
         {
           "conversation_id": "...",
           "message": "What are the terms of the ABC Corp contract?"
         }
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              8. HYBRID SEARCH: RETRIEVE CONTEXT                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         A) Vector Similarity Search (Semantic)
         - Embed user question
         - Search document_chunks
         - ORDER BY embedding <=> question_embedding
         - LIMIT 10
                              ↓
         B) Keyword Search (BM25/Full-Text)
         - Extract keywords: "ABC Corp", "contract"
         - Search document_chunks.content
         - ts_rank_cd(to_tsvector(content), query)
                              ↓
         C) Re-rank Results
         - Combine A + B results
         - Score by relevance + recency + document type
         - Select top 5-7 chunks
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               9. BUILD PROMPT WITH CITATIONS                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         Construct prompt for Claude:

         System: You are a legal assistant. Answer based ONLY on the
         provided documents. Always cite sources with [Doc: filename, Page X].
         If uncertain, say "I don't have enough information."

         Context Documents:
         [1] Service Agreement - ABC Corp (Page 3)
         "The term of this agreement shall be..."

         [2] Service Agreement - ABC Corp (Page 5)
         "Payment terms: Net 30 days..."

         User Question: What are the terms of the ABC Corp contract?
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              10. CLAUDE API: GENERATE RESPONSE                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         Call Anthropic Claude API
         - Model: claude-3-5-sonnet-20241022
         - Include retrieved context
         - Stream response to user
                              ↓
         Claude Response:
         "Based on the Service Agreement with ABC Corp, the key terms are:

         1. **Contract Duration**: 12-month term starting Feb 1, 2024
            [Doc: Service Agreement - ABC Corp, Page 3]

         2. **Payment Terms**: Net 30 days from invoice date
            [Doc: Service Agreement - ABC Corp, Page 5]

         3. **Termination**: Either party may terminate with 60 days notice
            [Doc: Service Agreement - ABC Corp, Page 8]"
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               11. STORE CONVERSATION HISTORY                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         INSERT INTO messages
         - User message
         - AI response
         - Citations (document_id, chunk_id, page)
         - Confidence score
```

---

## Version Control System

### Document Version Chain

```
Root Document (v1)              Document v2                Document v3 (Current)
┌──────────────────┐           ┌──────────────────┐       ┌──────────────────┐
│ ID: doc-123      │           │ ID: doc-456      │       │ ID: doc-789      │
│ root: NULL       │◄──────────│ root: doc-123    │◄──────│ root: doc-123    │
│ parent: NULL     │   parent  │ parent: doc-123  │parent │ parent: doc-456  │
│ version: 1       │           │ version: 2       │       │ version: 3       │
│ is_current: FALSE│           │ is_current: FALSE│       │ is_current: TRUE │
│ superseded: Y    │           │ superseded: Y    │       │ superseded: NULL │
└──────────────────┘           └──────────────────┘       └──────────────────┘
       │                              │                            │
       │                              │                            │
       └──────────────────────────────┴────────────────────────────┘
                                      │
                         document_relationships
                         ┌─────────────────────────┐
                         │ source: doc-123         │
                         │ target: doc-456         │
                         │ type: 'supersedes'      │
                         ├─────────────────────────┤
                         │ source: doc-456         │
                         │ target: doc-789         │
                         │ type: 'supersedes'      │
                         └─────────────────────────┘
```

### Version Control Queries

**Get Current Version:**

```sql
SELECT * FROM documents
WHERE matter_id = ?
  AND is_current_version = TRUE
  AND document_type = 'contract';
```

**Get All Versions (History):**

```sql
SELECT * FROM documents
WHERE root_document_id = ?
ORDER BY version_number ASC;
```

**Get Version Chain:**

```sql
WITH RECURSIVE version_chain AS (
  -- Start with root document
  SELECT * FROM documents WHERE id = ?
  UNION ALL
  -- Follow parent links
  SELECT d.* FROM documents d
  JOIN version_chain vc ON d.parent_document_id = vc.id
)
SELECT * FROM version_chain ORDER BY version_number;
```

**Compare Versions:**

```sql
SELECT
  d1.id as old_version,
  d2.id as new_version,
  d2.change_summary,
  dr.metadata as changes
FROM documents d1
JOIN documents d2 ON d2.parent_document_id = d1.id
LEFT JOIN document_relationships dr
  ON dr.source_document_id = d1.id
  AND dr.target_document_id = d2.id
  AND dr.relationship_type = 'supersedes'
WHERE d1.id = ?;
```

---

## Key Implementation Details

### 1. Semantic Chunking Strategy

**Why NOT Fixed-Size Chunking?**

- Breaks mid-sentence
- Loses context (headers, section structure)
- Poor for legal documents with clauses, subsections

**Intelligent Chunking Approach:**

```python
def semantic_chunk(text: str, max_tokens: int = 600) -> List[Chunk]:
    chunks = []

    # 1. Detect document structure
    sections = detect_sections(text)  # Headers, page breaks

    # 2. Split on natural boundaries
    for section in sections:
        paragraphs = section.split('\n\n')

        current_chunk = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = estimate_tokens(para)

            if current_tokens + para_tokens > max_tokens:
                # Save current chunk
                chunks.append({
                    'content': '\n\n'.join(current_chunk),
                    'metadata': {
                        'section': section.header,
                        'page': section.page
                    }
                })
                # Start new chunk with overlap
                current_chunk = [current_chunk[-1], para]  # Overlap!
                current_tokens = estimate_tokens(current_chunk)
            else:
                current_chunk.append(para)
                current_tokens += para_tokens

        # Add remaining chunk
        if current_chunk:
            chunks.append(...)

    return chunks
```

### 2. Hybrid Search Implementation

**Combine Vector + Keyword for Best Results:**

```python
async def hybrid_search(query: str, matter_id: UUID, limit: int = 10):
    # 1. Vector Similarity (Semantic)
    query_embedding = await embed_text(query)

    vector_results = await db.execute("""
        SELECT
            dc.*,
            d.document_title,
            1 - (dc.embedding <=> $1) as similarity_score
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.matter_id = $2
        ORDER BY dc.embedding <=> $1
        LIMIT 20
    """, query_embedding, matter_id)

    # 2. Keyword Search (BM25)
    keywords = extract_keywords(query)  # "ABC Corp", "contract", "terms"

    keyword_results = await db.execute("""
        SELECT
            dc.*,
            d.document_title,
            ts_rank_cd(
                to_tsvector('english', dc.content),
                plainto_tsquery('english', $1)
            ) as keyword_score
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.matter_id = $2
          AND to_tsvector('english', dc.content) @@ plainto_tsquery('english', $1)
        ORDER BY keyword_score DESC
        LIMIT 20
    """, keywords, matter_id)

    # 3. Re-rank: Combine scores
    combined = merge_and_rerank(vector_results, keyword_results)

    # 4. Diversify: Don't take all chunks from one document
    diversified = diversify_sources(combined, max_per_doc=3)

    return diversified[:limit]
```

### 3. Confidence Scoring

**When to Say "I Don't Know":**

```python
def should_answer(search_results: List[Chunk], query: str) -> bool:
    # No relevant documents found
    if not search_results:
        return False

    # Best match has low similarity
    best_score = search_results[0].similarity_score
    if best_score < 0.7:  # Threshold
        return False

    # All results from wrong document type
    doc_types = [r.document_type for r in search_results]
    if query_mentions_contract(query) and 'contract' not in doc_types:
        return False

    return True
```

---

## Anti-Hallucination Strategy

### 1. Always Cite Sources

```python
SYSTEM_PROMPT = """
You are a legal document assistant. Follow these rules:

1. ONLY answer based on the provided documents
2. ALWAYS cite sources: [Doc: filename, Page X]
3. If information is NOT in the documents, say:
   "I don't have information about that in the available documents."
4. If uncertain, say: "Based on the limited information available..."
5. Never make up case law, statutes, or legal precedents
"""
```

### 2. Show Retrieved Context

Return both the AI answer AND the source chunks so lawyers can verify.

### 3. Confidence Indicators

```json
{
  "answer": "The contract term is 12 months...",
  "confidence": "high",
  "sources": [
    {
      "document": "Service Agreement - ABC Corp",
      "page": 3,
      "excerpt": "The term of this agreement shall be twelve (12) months...",
      "relevance": 0.94
    }
  ],
  "gaps": ["No information found about renewal terms"]
}
```

### 4. Highlight Gaps

If the query asks multiple questions but only some are answerable:

```
Answer: "Based on the available documents:

1. Contract Duration: 12 months [Doc: ABC Corp Agreement, Page 3]
2. Payment Terms: I don't have information about payment terms in the available documents.
3. Termination: Either party may terminate with 60 days notice [Doc: ABC Corp Agreement, Page 8]"
```

---

## Next Implementation Steps

1. **Text Extraction Service** (`backend/app/services/text_extraction.py`)

   - PDF: pdfplumber or PyMuPDF
   - DOCX: python-docx
   - TXT: direct read

2. **Chunking Service** (`backend/app/services/chunking.py`)

   - Semantic paragraph-aware splitting
   - Metadata extraction
   - Overlap handling

3. **Embedding Service** (`backend/app/services/embeddings.py`)

   - OpenAI or Voyage AI integration
   - Batch processing
   - Rate limiting

4. **Celery Tasks** (`backend/app/tasks/`)

   - Background workers
   - Queue management
   - Retry logic

5. **Search Service** (`backend/app/services/search.py`)

   - Hybrid search implementation
   - Re-ranking algorithm
   - Citation tracking

6. **Chat API** (`backend/app/api/v1/endpoints/chat.py`)
   - Conversation management
   - Claude API integration
   - Streaming responses

---

**Last Updated:** 2025-11-05
**Status:** Database schema complete, ready for service implementation
