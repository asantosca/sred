# PwC SR&ED Intelligence Platform - Backend

FastAPI backend for AI-powered SR&ED document intelligence platform.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Hybrid Database Architecture](#hybrid-database-architecture)
- [Row-Level Security (RLS)](#row-level-security-rls)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Platform Admin & Cost Reporting](#platform-admin--cost-reporting)
- [Feedback Analytics](#feedback-analytics)
- [Document Processing Pipeline](#document-processing-pipeline)

## Architecture Overview

The backend is built with:
- **FastAPI** - Modern async Python web framework
- **SQLAlchemy 2.0** - Async ORM for database operations
- **PostgreSQL + pgvector** - Database with vector similarity search
- **asyncpg** - High-performance PostgreSQL driver
- **OpenAI** - Embedding generation for semantic search
- **LocalStack S3** - Document storage (development) / AWS S3 (production)
- **Valkey** - Caching and task queue (Redis-compatible)

## Hybrid Database Architecture

### The Problem

We use **pgvector** extension in PostgreSQL to store and query document embeddings (1536-dimensional vectors). However, integrating pgvector with SQLAlchemy's async ORM presents challenges:

1. **Type Registration Issues**: The pgvector type must be registered with asyncpg connections
2. **SQLAlchemy Event Limitations**: Connection pool events don't reliably work with asyncpg's async type registration
3. **Greenlet Context Violations**: Async operations within SQLAlchemy transaction contexts cause errors

### The Solution: Hybrid Approach

We use **two separate database access patterns**:

#### 1. SQLAlchemy ORM (95% of operations)
Use for all business logic and standard database operations:
- User management
- Document metadata
- Claims, companies, permissions
- Document chunks (content, metadata, token counts)
- All relationships and foreign keys

```python
# Example: Standard ORM usage
from sqlalchemy import select
from app.models.models import Document

async with AsyncSession() as session:
    query = select(Document).where(Document.id == document_id)
    result = await session.execute(query)
    document = result.scalar_one_or_none()
```

#### 2. Raw asyncpg (Vector operations only)
Use **only** for operations involving the `embedding` column:
- Storing embeddings
- Querying embeddings (similarity search)
- Checking if embeddings exist

```python
# Example: Vector storage
from app.services.vector_storage import vector_storage_service

# Store embeddings using raw SQL
await vector_storage_service.store_embeddings(
    chunk_ids=[uuid1, uuid2],
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
    model="text-embedding-3-small"
)

# Similarity search using raw SQL
results = await vector_storage_service.similarity_search(
    query_embedding=[0.5, 0.6, ...],
    claim_id=claim_id,
    limit=10
)
```

### Guidelines for Development

**DO:**
- Use SQLAlchemy ORM for all business logic and non-vector columns
- Use `vector_storage_service` for storing/querying embeddings
- Keep vector operations isolated in dedicated service classes

**DON'T:**
- Access `embedding` column through SQLAlchemy ORM
- Mix ORM and raw SQL in the same transaction for vector operations
- Add vector operations to model methods

## Row-Level Security (RLS)

The platform uses PostgreSQL Row-Level Security for database-enforced multi-tenant isolation.

### How It Works

1. **JWT Authentication**: User logs in and receives JWT containing `company_id`
2. **Middleware Extraction**: `TenantContextMiddleware` extracts `company_id` from JWT
3. **Session Variable**: `get_db()` sets `app.current_company_id` PostgreSQL session variable
4. **RLS Policies**: All queries automatically filtered by `company_id`

### Tables with RLS Policies

| Table | Isolation Method |
|-------|------------------|
| `companies` | Public read, tenant update |
| `users` | Public read (login), tenant update |
| `groups` | Direct `company_id` |
| `documents` | Direct `company_id` (denormalized) |
| `document_chunks` | Via `documents.company_id` |
| `claims` | Direct `company_id` |
| `conversations` | Direct `company_id` |
| `messages` | Via `conversations.company_id` |
| `billable_sessions` | Direct `company_id` |
| `daily_briefings` | Direct `company_id` |

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install OCR Dependencies (Optional)

OCR is used for extracting text from scanned PDFs:

- **AWS Textract** (production) - Used when AWS credentials are configured
- **Tesseract** (local development) - Free, offline fallback

**Docker (recommended):** The Celery worker in `docker-compose.yml` includes OCR tools.

### 3. Database Setup

```bash
# Start PostgreSQL with pgvector
docker-compose up -d postgres

# Run migrations
python -m alembic upgrade head
```

### 4. Start Development Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sred_db

# Valkey (Redis-compatible cache/queue)
REDIS_URL=redis://localhost:6379

# S3 Storage
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=ca-central-1
S3_BUCKET_NAME=sred-documents
S3_ENDPOINT_URL=http://localhost:4566  # LocalStack for development

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...

# Anthropic (for chat)
ANTHROPIC_API_KEY=sk-ant-...

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=development
DEBUG=true
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/refresh` - Refresh access token

### Documents
- `POST /api/v1/documents/upload/quick` - Quick upload (auto-processing)
- `POST /api/v1/documents/upload/advanced` - Advanced upload with metadata
- `GET /api/v1/documents/{id}` - Get document details
- `GET /api/v1/documents` - List documents (with filters)
- `DELETE /api/v1/documents/{id}` - Delete document

### Claims (SR&ED)
- `POST /api/v1/claims` - Create claim
- `GET /api/v1/claims/{id}` - Get claim details
- `GET /api/v1/claims` - List claims
- `PUT /api/v1/claims/{id}` - Update claim

### SR&ED Analysis
- `POST /api/v1/eligibility/{claim_id}/report` - Generate eligibility report
- `POST /api/v1/t661/{claim_id}/draft` - Generate T661 form draft

### Search
- `POST /api/v1/search/semantic` - Semantic search across documents
- `POST /api/v1/search/hybrid` - Hybrid search (keyword + semantic)

### Chat
- `POST /api/v1/chat/send` - Send message with RAG context
- `GET /api/v1/chat/conversations` - List conversations
- `GET /api/v1/chat/conversations/{id}` - Get conversation messages

### Platform Admin
- `GET /api/v1/admin/usage` - Get API usage summary with cost estimates
- `GET /api/v1/admin/usage/daily` - Get daily usage for trending
- `GET /api/v1/admin/feedback/stats` - Get feedback statistics

## Platform Admin & Cost Reporting

The platform includes API usage tracking and cost estimation.

### Setup

Add your email to `.env`:
```bash
PLATFORM_ADMIN_EMAILS=admin@pwc.com
```

### Services Tracked

| Service | Metrics | Pricing Basis |
|---------|---------|---------------|
| `claude_chat` | input/output tokens | $3/$15 per 1M tokens |
| `claude_summary` | input/output tokens | $3/$15 per 1M tokens |
| `openai_embeddings` | chunks processed | $0.02 per 1M tokens |
| `textract_ocr` | pages processed | ~$0.015 per page |

## Feedback Analytics

The platform tracks AI response quality through explicit user feedback and implicit behavioral signals.

### Tracked Signals

| Signal Type | Description |
|-------------|-------------|
| Explicit feedback | Thumbs up/down with optional category |
| Copy events | User copied AI response text |
| Source clicks | User clicked on cited document |
| Session duration | Time spent in conversation |
| Rephrase detection | User rephrased question |

## Document Processing Pipeline

### 1. Upload
Document uploaded to S3 and metadata stored in database.

### 2. Text Extraction
Extract text from PDF, DOCX, TXT files. For scanned PDFs, OCR is automatically triggered.

### 3. Chunking
Split text into semantic chunks (500-800 tokens) using sentence-aware splitting.

### 4. Embedding Generation
Generate vector embeddings using OpenAI text-embedding-3-small (1536 dimensions).

### 5. Event Extraction
Extract R&D milestones and dated events for project timeline.

### 6. Summarization
Generate AI summary for improved RAG context.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_claims.py
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Configuration, security
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── embeddings.py           # OpenAI integration
│   │   ├── vector_storage.py       # Raw asyncpg for vectors
│   │   ├── document_processor.py   # Pipeline orchestration
│   │   ├── chat_service.py         # AI chat with RAG
│   │   ├── eligibility_report_service.py  # SR&ED eligibility
│   │   ├── t661_service.py         # T661 form drafting
│   │   ├── chunking.py             # Text chunking
│   │   ├── text_extraction.py      # Text extraction
│   │   └── ocr.py                  # OCR (Textract + Tesseract)
│   ├── db/               # Database connection
│   └── main.py           # FastAPI application
├── alembic/              # Database migrations
├── tests/                # Test files
└── requirements.txt      # Dependencies
```

## Contributing

When adding new features:

1. Use SQLAlchemy ORM for business logic
2. Use `vector_storage_service` for vector operations
3. Write tests for both paths
4. Document any new SR&ED-specific services
5. Update this README if adding new services
