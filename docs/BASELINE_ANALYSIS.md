# SR&ED Intelligence Platform - Baseline Analysis

**Generated**: January 18, 2026
**Platform Version**: POC (Pre-production)
**Analysis Scope**: Full codebase architecture, features, and gap analysis

---

## Executive Summary

The SR&ED Intelligence Platform is a production-grade, multi-tenant SaaS application designed for PwC consultants to analyze Scientific Research and Experimental Development (SR&ED) tax credit claims. The platform features:

- **Robust RAG Pipeline**: OpenAI embeddings (1536D) + pgvector + hybrid search (semantic + BM25 keyword with RRF)
- **AI-Powered Features**: Claude-based chat, eligibility reports, T661 form drafting, event extraction, daily briefings
- **Full Document Processing**: PDF/DOCX/TXT extraction, OCR (Textract/Tesseract), semantic chunking (500-800 tokens)
- **Multi-Tenancy**: Row-level security via `company_id` on all tables
- **Modern Stack**: FastAPI (async Python) + React 18 + TypeScript + PostgreSQL + Celery

The platform is approximately 85% complete for POC requirements, with strong foundations for document management, RAG-based chat, and CRA form generation. Key gaps include advanced document clustering, NER entity extraction, and analytics dashboards.

---

## Current Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React 18 + Vite)                         │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐  │
│  │Dashboard│ │Documents │ │  Chat  │ │ Timeline │ │ Claims  │ │T661 Drafting │  │
│  └────┬────┘ └────┬─────┘ └───┬────┘ └────┬─────┘ └────┬────┘ └──────┬───────┘  │
└───────┼──────────┼────────────┼───────────┼────────────┼─────────────┼──────────┘
        │          │            │           │            │             │
        ▼          ▼            ▼           ▼            ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          FastAPI (Async REST API)                               │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌───────────┐ ┌───────────────────┐  │
│  │   Auth   │ │ Documents │ │   Search   │ │   Chat    │ │ Eligibility/T661  │  │
│  └─────┬────┘ └─────┬─────┘ └──────┬─────┘ └─────┬─────┘ └─────────┬─────────┘  │
└────────┼────────────┼──────────────┼─────────────┼─────────────────┼────────────┘
         │            │              │             │                 │
         ▼            ▼              ▼             ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SERVICE LAYER                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐   │
│  │  Document Proc.  │  │  Vector Storage  │  │     AI Services (Claude)    │   │
│  │  • Extraction    │  │  • Semantic      │  │  • Chat/RAG                 │   │
│  │  • Chunking      │  │  • Keyword       │  │  • Eligibility Reports      │   │
│  │  • Embeddings    │  │  • Hybrid (RRF)  │  │  • T661 Drafting            │   │
│  └────────┬─────────┘  └────────┬─────────┘  │  • Event Extraction         │   │
│           │                     │            │  • Daily Briefings          │   │
│           │                     │            └──────────────┬───────────────┘   │
└───────────┼─────────────────────┼───────────────────────────┼───────────────────┘
            │                     │                           │
            ▼                     ▼                           ▼
┌───────────────────┐  ┌──────────────────────┐  ┌────────────────────────────────┐
│   Celery Worker   │  │  PostgreSQL + pgvec. │  │         External APIs          │
│  (Background)     │  │  ┌────────────────┐  │  │  ┌────────────┐ ┌───────────┐  │
│  • Text Extract   │  │  │ document_chunks│  │  │  │   OpenAI   │ │ Anthropic │  │
│  • Embedding Gen  │  │  │ (Vector 1536)  │  │  │  │ Embeddings │ │  Claude   │  │
│  • Event Extract  │  │  └────────────────┘  │  │  └────────────┘ └───────────┘  │
│  • AI Summary     │  └──────────────────────┘  └────────────────────────────────┘
└───────────────────┘
            │                     │
            ▼                     ▼
┌───────────────────┐  ┌──────────────────────┐
│   Valkey (Redis)  │  │       AWS S3         │
│  • Task Queue     │  │  (LocalStack dev)    │
│  • Result Backend │  │  • Document Files    │
└───────────────────┘  └──────────────────────┘
```

---

## PART 1: ARCHITECTURE & DATA MODEL

### 1. Document Structure & Metadata

#### Document Model (`backend/app/models/models.py:Document`)

The Document model contains **50+ fields** covering:

```python
class Document(Base):
    __tablename__ = "documents"

    # Core Identifiers
    id: UUID (PK)
    company_id: UUID (FK)           # Denormalized for RLS performance
    claim_id: UUID (FK)

    # File Information
    filename: String(500)
    original_filename: String(500)
    file_extension: String(10)
    file_size_bytes: BigInteger
    storage_path: String(1000)       # S3 path
    file_hash: String(64)            # SHA-256 for deduplication
    mime_type: String(100)

    # Classification (SR&ED-specific)
    document_type: String(100)       # project_plan, timesheet, email, technical_report, etc.
    document_subtype: String(100)
    document_title: String(500)
    document_date: Date
    document_status: String(50)      # draft, final, executed, filed

    # Security/Privilege
    confidentiality_level: String(50)  # public, internal, standard_confidential, highly_confidential
    is_privileged: Boolean
    privilege_attorney_client: Boolean
    privilege_work_product: Boolean

    # Parties (for correspondence)
    author: String(255)
    recipient: String(255)

    # Processing Status
    processing_status: String(50)    # pending, processing, text_extracted, chunked, embedded, complete, failed
    text_extracted: Boolean
    indexed_for_search: Boolean

    # Text Extraction Results
    extracted_text: Text
    page_count: Integer
    word_count: Integer
    extraction_method: String(50)    # pdfplumber, python-docx, ocr_textract, ocr_tesseract

    # OCR Metadata
    ocr_applied: Boolean
    ocr_engine: String(50)
    ocr_pages_processed: Integer
    ocr_confidence_avg: Float

    # AI Enhancement
    ai_summary: Text
    ai_summary_generated_at: DateTime

    # Audit Trail
    created_at, updated_at: DateTime
    created_by, updated_by: UUID (FK)
```

#### Document Chunk Model (`backend/app/models/models.py:DocumentChunk`)

```python
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: UUID (PK)
    document_id: UUID (FK, CASCADE)
    chunk_index: Integer              # Position in document
    content: Text                     # Chunk text

    # Vector Embedding (RAG)
    embedding: Vector(1536)           # pgvector with 1536 dimensions
    embedding_model: String(100)      # 'text-embedding-3-small'

    # Full-text Search (BM25)
    search_vector: TSVECTOR           # Auto-populated by trigger

    # Position Metadata
    chunk_metadata: JSON              # {start_page, end_page, section, paragraph_count}
    token_count: Integer
    char_count: Integer
    start_char, end_char: Integer
```

#### Project/Claim Organizational Structure

Yes, documents are organized by **Claims** (SR&ED claims for fiscal years):

```python
class Claim(Base):
    __tablename__ = "claims"

    id: UUID (PK)
    company_id: UUID (FK)

    # Identifiers
    claim_number: String(50)          # e.g., "SRED-2025-001"
    company_name: String(255)         # Client company name
    project_type: String(100)         # Software Development, Manufacturing, etc.
    claim_status: String(50)          # draft, in_progress, under_review, submitted, approved

    # SR&ED-specific
    fiscal_year_end: Date
    naics_code: String(10)
    cra_business_number: String(15)
    total_eligible_expenditures: DECIMAL(15,2)
    federal_credit_estimate: DECIMAL(15,2)
    provincial_credit_estimate: DECIMAL(15,2)

    # Project Context (for AI T661 generation)
    project_title: String(255)
    project_objective: Text
    technology_focus: String(500)

    # Lead Consultant
    lead_consultant_user_id: UUID (FK)
```

#### Metadata Extraction During Upload

The system extracts metadata via:

1. **DocumentIntelligenceService** (pre-upload analysis):
   - Filename parsing for document type, date, author
   - MIME type detection
   - File hash calculation (SHA-256)

2. **Text Extraction** (background processing):
   - Page count, word count, character count
   - Extraction method used
   - OCR confidence (if scanned)

3. **AI Summary Generation** (background):
   - Claude-generated document summary

---

### 2. Storage & Database

#### Vector Database: PostgreSQL + pgvector

**NOT using** Pinecone/Weaviate/Chroma. The system uses:

- **PostgreSQL 15** with **pgvector extension**
- **Vector dimensions**: 1536 (matches OpenAI text-embedding-3-small)
- **Distance metric**: Cosine distance (`<=>` operator)

**Critical Architecture Decision**: Vector operations use **raw asyncpg**, NOT SQLAlchemy ORM:

```python
# backend/app/services/vector_storage.py
class VectorStorageService:
    """Uses raw asyncpg for pgvector operations"""

    async def store_embeddings(self, chunk_ids, embeddings, model, company_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE sred_ds.document_chunks
                SET embedding = $1::vector(1536),
                    embedding_model = $2
                WHERE id = $3
            """, embedding, model, chunk_id)
```

**Reason**: pgvector type registration doesn't work reliably with SQLAlchemy async sessions.

#### Traditional Database: PostgreSQL

**Schema**: `sred_ds` (22+ tables)

**Core Tables**:
- `companies` - PwC client companies
- `users` - User accounts with company_id
- `groups` - RBAC groups with JSON permissions
- `claims` - SR&ED claims (fiscal year tracking)
- `claim_access` - User access control per claim

**Documents & RAG**:
- `documents` - Document metadata (50+ fields)
- `document_chunks` - Text chunks with embeddings (Vector 1536)
- `document_events` - AI-extracted timeline events

**AI Chat**:
- `conversations` - Chat sessions (claim-scoped)
- `messages` - Chat messages with sources and context

**Tracking**:
- `billable_sessions` - Consulting time tracking
- `daily_briefings` - AI-generated summaries
- `api_usage_logs` - Token usage and cost tracking

#### Current Organization

Documents are organized **by Claim** (SR&ED claim for a fiscal year):

```
Company (PwC client)
└── Claims (fiscal year claims)
    └── Documents (uploaded files)
        └── Chunks (text segments with embeddings)
```

All queries filter by `company_id` for multi-tenant isolation.

---

### 3. Processing Pipeline

#### Document Upload Flow

**Endpoint**: `POST /api/v1/documents/upload/quick`

```
1. User Upload (Browser)
   ├── Drag-and-drop or file picker
   ├── Max size: 500MB
   └── Formats: PDF, DOCX, DOC, TXT, PNG, JPG, TIFF

2. API Validation
   ├── Check user has can_upload permission for claim
   ├── Validate file size and extension
   ├── Calculate SHA-256 hash (duplicate detection)
   └── Auto-detect metadata (title, date, author)

3. S3 Upload
   ├── Upload to S3 bucket (LocalStack for dev)
   └── Store storage_path in database

4. Create Document Record
   ├── processing_status = 'pending'
   ├── text_extracted = False
   └── indexed_for_search = False

5. Trigger Background Task
   └── Celery: process_document_pipeline.delay(document_id, company_id)
```

#### Background Processing Pipeline (Celery)

**Location**: `backend/app/tasks/document_processing.py`

```
process_document_pipeline (Celery Task)
│
├── Stage 1: TEXT EXTRACTION
│   ├── Download file from S3
│   ├── Detect file type
│   ├── Extract text:
│   │   ├── PDF → pdfplumber (scanned → OCR fallback)
│   │   ├── DOCX → python-docx
│   │   └── TXT → charset_normalizer (encoding detection)
│   ├── OCR if needed:
│   │   ├── AWS Textract (production)
│   │   └── Tesseract (local dev)
│   └── Save: extracted_text, page_count, word_count
│
├── Stage 2: CHUNKING
│   ├── Semantic chunking (NOT fixed-size)
│   ├── Target: 500 tokens (range: 100-800)
│   ├── Respects boundaries:
│   │   ├── Paragraphs (double newlines)
│   │   ├── Section headers (ARTICLE I, Section 2.1)
│   │   └── Page markers [Page N]
│   ├── Overlap: Last paragraph carried to next chunk
│   └── Create DocumentChunk records
│
├── Stage 3: EMBEDDING GENERATION
│   ├── Batch extract chunk content
│   ├── Call OpenAI API (batch size: 100)
│   ├── Model: text-embedding-3-small
│   ├── Dimensions: 1536
│   ├── Retry logic: 3 attempts, exponential backoff
│   └── Store via raw asyncpg (NOT ORM)
│
├── Stage 4: EVENT EXTRACTION (non-fatal)
│   ├── Extract R&D milestones via Claude
│   └── Create DocumentEvent records
│
└── Stage 5: AI SUMMARIZATION (non-fatal)
    ├── Generate Claude summary
    └── Save to document.ai_summary
```

#### OCR System

**Primary**: AWS Textract (production)
**Fallback**: Tesseract (local development)

```python
# backend/app/services/text_extraction.py
def is_likely_scanned_pdf(text: str, page_count: int) -> bool:
    """Detect if PDF needs OCR based on text density"""
    if not text or len(text.strip()) < 100:
        return True
    words_per_page = len(text.split()) / max(page_count, 1)
    return words_per_page < 50  # Threshold for scanned detection
```

#### Chunking Implementation

```python
# backend/app/services/chunking.py
class ChunkingService:
    MIN_CHUNK_TOKENS = 100
    TARGET_CHUNK_TOKENS = 500
    MAX_CHUNK_TOKENS = 800
    OVERLAP_CHARS = 100

    # Section detection patterns (legal/technical documents)
    SECTION_PATTERNS = [
        r'^ARTICLE\s+[IVXLCDM\d]+',      # ARTICLE I
        r'^Section\s+\d+\.?\d*',          # Section 1, 2.1
        r'^\d+\.\s+[A-Z]',                # 1. INTRODUCTION
        r'^[A-Z][A-Z\s]{10,}:?$',         # ALL CAPS HEADERS
    ]
```

#### Embedding Model

- **Provider**: OpenAI
- **Model**: `text-embedding-3-small`
- **Dimensions**: 1536
- **Batch size**: 100 texts per API call
- **Retry**: 3 attempts with exponential backoff

---

## PART 2: EXISTING FEATURES

### 4. Upload & Ingestion

| Feature | Status | Details |
|---------|--------|---------|
| Single file upload | EXISTS | Quick upload with 5 required fields |
| Drag-and-drop | EXISTS | Supported in DocumentUpload.tsx |
| Batch upload | MISSING | No multi-file upload in single request |
| External sources (Google Drive) | MISSING | No integrations |
| Folder organization during upload | PARTIAL | Assign to claim, but no folder hierarchy |
| Pre-upload analysis | EXISTS | Auto-detect document type, date, author |
| Duplicate detection | EXISTS | SHA-256 hash comparison |

**Supported Formats**: PDF, DOCX, DOC, TXT, PNG, JPG, JPEG, TIFF

**Upload Limits**: 500MB per file (increased for SR&ED technical reports)

---

### 5. Query & Retrieval

#### Current RAG Query Flow

```
User Message
    │
    ▼
Generate Query Embedding (OpenAI text-embedding-3-small)
    │
    ▼
Hybrid Search (VectorStorageService)
├── Semantic: Vector cosine similarity
├── Keyword: PostgreSQL full-text search (BM25)
└── Combine: Reciprocal Rank Fusion (RRF)
    │
    ▼
Retrieve Top-K Chunks (default: 5, threshold: 0.5)
    │
    ▼
Build System Prompt
├── Document summaries (if available)
├── Context chunks with [Source X] notation
└── SR&ED domain instructions
    │
    ▼
Call Claude API
├── System prompt with context
├── Conversation history (last 10 messages)
└── User message
    │
    ▼
Parse Response
├── Extract confidence level [HIGH/MEDIUM/LOW]
├── Track source citations
└── Generate improvement suggestions
    │
    ▼
Return to User
├── Streaming (SSE) or non-streaming
├── Source citations with document links
└── Question suggestions (if low confidence)
```

#### Search Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `semantic` | Vector similarity only | Conceptual queries |
| `keyword` | BM25 full-text search | Exact terms ("Section 12.3", case names) |
| `hybrid` | RRF combination (default) | Best of both worlds |

**RRF Formula**:
```
rrf_score = semantic_weight × (1/(60 + semantic_rank)) +
            keyword_weight × (1/(60 + keyword_rank))
```

**Default Weights**: semantic=0.7, keyword=0.3

#### UI for Querying

| Feature | Status | Component |
|---------|--------|-----------|
| Chat interface | EXISTS | ChatInterface.tsx, MessageInput.tsx |
| Streaming responses | EXISTS | SSE with content/source/done events |
| Source citations | EXISTS | SourceCitations.tsx with similarity scores |
| Filter by claim | EXISTS | ClaimSelectorCompact.tsx |
| Discovery mode (no claim) | EXISTS | General SR&ED Q&A without RAG |

#### Filtering Capabilities

- **By claim**: Required for RAG, optional for discovery mode
- **By date range**: Available in advanced search
- **By document type**: Available in document list
- **By confidence level**: Available in timeline view

---

### 6. User Management

#### Multi-User System

| Feature | Status | Details |
|---------|--------|---------|
| Multi-tenant | EXISTS | Row-level security via company_id |
| User accounts | EXISTS | Email/password with JWT |
| RBAC groups | EXISTS | Groups with JSON permissions |
| Admin role | EXISTS | Company admin can manage users |
| Claim-level access | EXISTS | ClaimAccess model with role-based permissions |

#### Claim Access Roles

```python
access_role: str  # lead_consultant, analyst, reviewer, read_only
can_upload: bool
can_edit: bool
can_delete: bool
```

#### Authentication

- **JWT Access Tokens**: 15-minute expiration
- **Refresh Tokens**: Stored in database, rotated on refresh
- **Password Reset**: 1-day TTL, email-based
- **Email Confirmation**: 5-day TTL for new registrations

---

### 7. UI/Frontend

#### Framework

- **React 18** with TypeScript
- **Vite** build tool (port 3000, proxies /api to backend)
- **TailwindCSS** for styling
- **Zustand** for auth state
- **TanStack React Query** for server state

#### Main Pages/Views

| Page | File | Purpose |
|------|------|---------|
| Dashboard | `DashboardPage.tsx` | Usage stats, daily briefing, upcoming events |
| Claims | `ClaimsPage.tsx` | List/manage SR&ED claims |
| Documents | `DocumentsPage.tsx` | Upload and manage documents |
| Chat | `ChatPage.tsx` | RAG-powered chat with claim context |
| Timeline | `TimelinePage.tsx` | AI-extracted R&D milestones |
| Billable | `BillablePage.tsx` | Consulting hours tracking |
| Profile | `ProfilePage.tsx` | User profile and avatar |

#### Chat Interface Features

- Message bubbles with user/assistant roles
- Streaming content rendering (real-time)
- Source citations with document links
- Copy button for responses
- Feedback buttons (thumbs up/down)
- Question improvement suggestions
- Markdown rendering
- Claim selector for context

#### Document Management Features

- Quick upload with drag-and-drop
- Processing status indicators (8 states)
- AI summary preview
- Metadata editing modal
- Download and delete actions
- Search and filtering

---

## PART 3: CAPABILITIES ASSESSMENT

### 8. Feature Status Matrix

| Feature | Status | Notes |
|---------|--------|-------|
| Document tagging/labeling | PARTIAL | `document_type`, `tags` array, but no tag management UI |
| Document metadata beyond filename | EXISTS | 50+ fields including dates, parties, privilege |
| Multi-project/case organization | EXISTS | Claims with fiscal year tracking |
| Clustering or grouping of documents | MISSING | No automatic clustering |
| Automatic categorization | PARTIAL | Document type detection on upload |
| Interactive chat interface | EXISTS | Full RAG chat with streaming |
| Document preview/viewer | PARTIAL | Metadata view, but no in-app PDF viewer |
| Bulk operations on documents | PARTIAL | Delete works, no bulk edit/move |
| Change detection (new uploads) | PARTIAL | File hash for duplicates, no version comparison |
| Analytics or dashboards | PARTIAL | Basic usage stats, no detailed analytics |
| Export capabilities | PARTIAL | Billable export, no document export |
| API endpoints documentation | EXISTS | Swagger/OpenAPI at /docs |

### 9. Natural Language Processing

| Feature | Status | Implementation |
|---------|--------|----------------|
| Named Entity Recognition (NER) | MISSING | No dedicated NER pipeline |
| Date extraction | PARTIAL | Claude extracts dates for timeline events |
| Person/organization extraction | PARTIAL | Basic author/recipient detection |
| Custom entity extraction | MISSING | No custom entity models |
| Sentiment analysis | MISSING | Not implemented |
| Keyword extraction | PARTIAL | BM25 uses tsvector for keyword matching |

**Note**: The timeline event extraction uses Claude for date/event extraction but lacks dedicated NER for entities like company names, people, or technical terms.

### 10. Advanced RAG Features

| Feature | Status | Implementation |
|---------|--------|----------------|
| Context window management | PARTIAL | Fixed 5 chunks + 10 message history |
| Multi-document reasoning | EXISTS | Hybrid search across all claim documents |
| Citation/source tracking | EXISTS | Full source attribution with similarity scores |
| Confidence scoring | EXISTS | Self-reported by Claude [HIGH/MEDIUM/LOW] |
| Re-ranking of results | PARTIAL | RRF combines semantic + keyword, but no learned re-ranker |

---

## PART 4: CODE INVENTORY

### 11. File Structure

```
sred/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API route handlers (11 files)
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── users.py         # User management
│   │   │   ├── matters.py       # Claim management (legacy name)
│   │   │   ├── documents.py     # Document CRUD + upload
│   │   │   ├── search.py        # Semantic/hybrid search
│   │   │   ├── chat.py          # RAG chat endpoints
│   │   │   ├── eligibility.py   # SR&ED eligibility reports
│   │   │   ├── t661.py          # CRA T661 form drafting
│   │   │   ├── timeline.py      # Document event timeline
│   │   │   ├── billable.py      # Consulting hours
│   │   │   └── briefing.py      # Daily briefings
│   │   │
│   │   ├── core/                # Config, security, middleware (8 files)
│   │   │   ├── config.py        # Environment settings
│   │   │   ├── security.py      # JWT, password hashing
│   │   │   ├── tenant.py        # Multi-tenancy context
│   │   │   ├── celery_app.py    # Celery configuration
│   │   │   └── rate_limit.py    # slowapi rate limiting
│   │   │
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   └── models.py        # All 22+ tables (2000+ lines)
│   │   │
│   │   ├── schemas/             # Pydantic request/response schemas (15+ files)
│   │   │
│   │   ├── services/            # Business logic layer (15+ files)
│   │   │   ├── auth.py          # Authentication service
│   │   │   ├── chat_service.py  # RAG chat logic
│   │   │   ├── vector_storage.py    # pgvector operations (raw asyncpg)
│   │   │   ├── embeddings.py    # OpenAI embedding generation
│   │   │   ├── text_extraction.py   # PDF/DOCX/TXT extraction
│   │   │   ├── chunking.py      # Semantic text chunking
│   │   │   ├── document_processor.py # Pipeline orchestration
│   │   │   ├── storage.py       # S3 file operations
│   │   │   ├── eligibility_report_service.py
│   │   │   ├── t661_service.py
│   │   │   ├── event_extraction.py
│   │   │   └── briefing_service.py
│   │   │
│   │   ├── tasks/               # Celery background tasks
│   │   │   └── document_processing.py
│   │   │
│   │   └── utils/               # Helper utilities
│   │
│   ├── alembic/                 # Database migrations (19 versions)
│   └── tests/                   # Pytest test suite
│
├── frontend/
│   └── src/
│       ├── components/          # React components
│       │   ├── documents/       # DocumentUpload, DocumentList
│       │   ├── chat/            # ChatInterface, MessageInput, SourceCitations
│       │   ├── t661/            # T661DraftModal
│       │   ├── layout/          # DashboardLayout, ProtectedRoute
│       │   └── ui/              # Button, Card, Input, Alert
│       │
│       ├── pages/               # Page components (17 pages)
│       ├── store/               # Zustand auth store
│       ├── lib/                 # API client (axios)
│       ├── types/               # TypeScript type definitions
│       └── hooks/               # Custom React hooks
│
├── docs/                        # Project documentation
│   ├── ROADMAP.md
│   ├── DECISIONS.md
│   └── SRED_DOMAIN.md
│
└── docker-compose.yml           # Local development services
```

### 12. Dependencies

#### Backend (Python 3.12+)

**Core Framework**:
- FastAPI 0.118.0 - Async web framework
- SQLAlchemy 2.0.44 - ORM
- asyncpg 0.30.0 - PostgreSQL async driver
- pgvector 0.4.1 - Vector extension

**AI/ML**:
- openai 2.7.1 - Embeddings (text-embedding-3-small)
- anthropic 0.72.0 - Claude chat

**Document Processing**:
- pdfplumber 0.11.7 - PDF extraction
- python-docx 1.2.0 - DOCX parsing
- pytesseract 0.3.13 - OCR (Tesseract)
- boto3 1.40.40 - AWS S3/Textract

**Background Jobs**:
- celery 5.5.3 - Task queue
- redis 6.4.0 - Valkey client

**Auth & Security**:
- python-jose 3.5.0 - JWT
- passlib 1.7.4 - Password hashing

#### Frontend (React 18)

**Core**:
- react 18.2.0, react-dom 18.2.0
- react-router-dom 6.18.0
- typescript 5.2.2

**State & Data**:
- zustand 4.4.6 - State management
- @tanstack/react-query 5.8.1 - Server state
- axios 1.6.0 - HTTP client
- react-hook-form 7.47.0, zod 3.22.4 - Forms

**UI**:
- tailwindcss 3.3.5
- @headlessui/react 1.7.17
- lucide-react 0.294.0

### 13. Configuration

#### Environment Variables (backend/.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sred_db

# Cache/Queue
REDIS_URL=redis://localhost:6379

# Storage
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localhost:4566  # LocalStack
S3_BUCKET_NAME=sred-documents

# Auth
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# AI APIs
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536

# Email
SMTP_HOST=localhost
SMTP_PORT=1025  # MailHog

# Optional
SENTRY_DSN=...
```

---

## PART 5: GAP ANALYSIS

### Already Have (Can Reuse As-Is)

| Component | Details |
|-----------|---------|
| **Document Upload Pipeline** | S3 storage, validation, metadata extraction |
| **Text Extraction** | PDF (pdfplumber), DOCX, TXT, OCR (Textract/Tesseract) |
| **Semantic Chunking** | 500-800 tokens, respects section boundaries |
| **Embedding Generation** | OpenAI text-embedding-3-small (1536D) |
| **Vector Storage** | pgvector with raw asyncpg |
| **Hybrid Search** | Semantic + BM25 keyword with RRF |
| **RAG Chat** | Claude with context, streaming, source citations |
| **Multi-Tenancy** | Row-level security via company_id |
| **User Authentication** | JWT with refresh token rotation |
| **Claim Organization** | Claims with fiscal year tracking |
| **T661 Drafting** | CRA form sections with word limits |
| **Timeline Events** | AI-extracted R&D milestones |
| **Billable Hours** | Time tracking from conversations |

### Can Extend (Needs Enhancement)

| Feature | Current State | Enhancement Needed |
|---------|---------------|-------------------|
| **Document Categorization** | Basic type detection | Add ML-based auto-categorization |
| **Metadata Extraction** | Author, date, title | Add NER for people, orgs, technical terms |
| **Analytics Dashboard** | Basic usage stats | Add comprehensive analytics (search patterns, document insights) |
| **Document Preview** | Metadata only | Add in-app PDF/DOCX viewer |
| **Bulk Operations** | Delete only | Add bulk edit, move, export |
| **Context Window** | Fixed 5 chunks | Add dynamic context sizing based on query |
| **Confidence Scoring** | Claude self-report | Add retrieval-based confidence metrics |
| **Tag Management** | Tags array exists | Add tag CRUD UI, tag suggestions |

### Need to Build (Net-New)

| Feature | Priority | Effort |
|---------|----------|--------|
| **Document Clustering** | Medium | High - requires ML pipeline |
| **Named Entity Recognition** | Medium | Medium - integrate spaCy or custom model |
| **Batch Upload** | Low | Low - extend existing endpoint |
| **External Source Integrations** | Low | High - Google Drive, SharePoint APIs |
| **Advanced Analytics** | Medium | Medium - build dashboard components |
| **Document Versioning** | Low | Medium - version comparison logic |
| **Export to Practice Systems** | Medium | Medium - Clio integration |
| **Learned Re-ranker** | Low | High - train custom model |

### Potential Conflicts (May Need Refactoring)

| Issue | Current State | Concern |
|-------|---------------|---------|
| **"Matters" vs "Claims" naming** | Backend uses both | Standardize to "claims" everywhere |
| **Vector storage architecture** | Raw asyncpg separate from ORM | May complicate transactions |
| **Fixed chunk parameters** | Hardcoded 500-800 tokens | May need tuning for different document types |
| **Monolithic services** | Some services are large | Consider splitting for maintainability |

---

## Gap Analysis Summary Table

| Category | Score | Status |
|----------|-------|--------|
| Document Upload & Storage | 90% | EXISTS - fully functional |
| Text Processing & Chunking | 90% | EXISTS - semantic chunking, OCR |
| Embedding & Vector Search | 95% | EXISTS - hybrid search with RRF |
| RAG Chat Interface | 90% | EXISTS - streaming, citations |
| SR&ED-Specific Features | 85% | EXISTS - T661, eligibility reports |
| Multi-Tenancy & Auth | 95% | EXISTS - RLS, JWT, RBAC |
| NLP/Entity Extraction | 30% | PARTIAL - basic date/event extraction |
| Document Clustering | 0% | MISSING |
| Analytics & Dashboards | 40% | PARTIAL - basic usage stats |
| Bulk Operations | 30% | PARTIAL - limited functionality |
| External Integrations | 0% | MISSING |

**Overall Completeness**: ~75% of typical document intelligence platform features

---

## Recommended Migration Strategy

Given the current architecture, here's the recommended approach for extending the platform:

### Phase 1: Consolidate & Stabilize
1. Standardize "matters" → "claims" terminology in remaining code
2. Add comprehensive test coverage
3. Document existing API contracts

### Phase 2: Enhance Core Capabilities
1. Add document preview (PDF.js integration)
2. Build tag management UI
3. Implement batch upload
4. Add dynamic context window sizing

### Phase 3: Add Intelligence Layer
1. Integrate spaCy for NER (people, orgs, dates, technical terms)
2. Add document clustering (TF-IDF + k-means or HDBSCAN)
3. Build analytics dashboard
4. Implement learned re-ranker (optional)

### Phase 4: Integrations
1. Export to practice management systems
2. External document sources (if needed)
3. Advanced reporting and export

---

## File Paths Reference

**Models**: `backend/app/models/models.py`
**Vector Service**: `backend/app/services/vector_storage.py`
**Embedding Service**: `backend/app/services/embeddings.py`
**Chunking Service**: `backend/app/services/chunking.py`
**Text Extraction**: `backend/app/services/text_extraction.py`
**Document Processor**: `backend/app/services/document_processor.py`
**Chat Service**: `backend/app/services/chat_service.py`
**Search Endpoint**: `backend/app/api/v1/endpoints/search.py`
**Document Endpoint**: `backend/app/api/v1/endpoints/documents.py`
**Configuration**: `backend/app/core/config.py`
**Migrations**: `backend/alembic/versions/`

---

*This baseline document reflects the codebase as of January 2026. Update as features are added or modified.*
