# BC Legal Tech Backend

FastAPI backend for AI-powered legal document intelligence platform.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Hybrid Database Architecture](#hybrid-database-architecture)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Document Processing Pipeline](#document-processing-pipeline)

## Architecture Overview

The backend is built with:
- **FastAPI** - Modern async Python web framework
- **SQLAlchemy 2.0** - Async ORM for database operations
- **PostgreSQL + pgvector** - Database with vector similarity search
- **asyncpg** - High-performance PostgreSQL driver
- **OpenAI** - Embedding generation for semantic search
- **LocalStack S3** - Document storage (development) / AWS S3 (production)
- **Redis** - Caching and session management

## Hybrid Database Architecture

### The Problem

We use **pgvector** extension in PostgreSQL to store and query document embeddings (1536-dimensional vectors). However, integrating pgvector with SQLAlchemy's async ORM presents challenges:

1. **Type Registration Issues**: The pgvector type (OID 49747) must be registered with asyncpg connections using `register_vector()` from `pgvector.asyncpg`
2. **SQLAlchemy Event Limitations**: SQLAlchemy's connection pool event system doesn't reliably work with asyncpg's asynchronous type registration
3. **Greenlet Context Violations**: Attempting to register types or perform async operations from within SQLAlchemy transaction contexts causes "greenlet_spawn has not been called" errors

### The Solution: Hybrid Approach

We use **two separate database access patterns**:

#### 1. SQLAlchemy ORM (95% of operations)
Use for all business logic and standard database operations:
- User management
- Document metadata
- Matters, companies, permissions
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
- Storing embeddings (`UPDATE document_chunks SET embedding = ...`)
- Querying embeddings (`SELECT ... WHERE embedding <=> ...`)
- Checking if embeddings exist

```python
# Example: Vector storage (see app/services/vector_storage.py)
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
    matter_id=matter_id,
    limit=10
)
```

### Implementation Details

#### Vector Storage Service (`app/services/vector_storage.py`)

The `VectorStorageService` maintains its own asyncpg connection pool:

```python
class VectorStorageService:
    async def get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            # Strip +asyncpg dialect for raw asyncpg
            db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

            # Create pool with type registration
            self._pool = await asyncpg.create_pool(
                db_url,
                min_size=2,
                max_size=10,
                init=self._init_connection  # Register vector type on each connection
            )
        return self._pool

    async def _init_connection(self, conn: asyncpg.Connection):
        """Register pgvector type on each new connection."""
        await register_vector(conn)
```

Key points:
- Separate connection pool from SQLAlchemy
- Type registration happens via `init` parameter (called for each new connection)
- Database URL must have `+asyncpg` dialect stripped for raw asyncpg

#### Document Chunk Model (`app/models/models.py`)

The embedding column uses deferred loading to prevent accidental ORM access:

```python
from sqlalchemy.orm import deferred
from pgvector.sqlalchemy import Vector

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    # ... other columns ...

    # Deferred loading prevents automatic loading of vector column
    embedding = deferred(Column(Vector(1536), nullable=True))
    embedding_model = Column(String(100), nullable=True)

    # Important: Database column is 'metadata', Python attribute is 'chunk_metadata'
    chunk_metadata = Column("metadata", JSON, nullable=True)
```

#### Document Processor (`app/services/document_processor.py`)

The processor uses ORM for document/chunk retrieval but raw SQL for embeddings:

```python
async def process_embeddings(self, document_id: UUID) -> bool:
    # Use ORM to get chunks (but don't load embedding column)
    chunks_query = select(
        DocumentChunk.id,
        DocumentChunk.content,
        DocumentChunk.chunk_index
    ).where(DocumentChunk.document_id == document_id)

    chunks_result = await self.db.execute(chunks_query)
    chunks = chunks_result.all()

    # Generate embeddings
    embeddings = embedding_service.generate_embeddings_batch([c.content for c in chunks])

    # Store using raw SQL (vector_storage_service)
    await vector_storage_service.store_embeddings(
        chunk_ids=[c.id for c in chunks],
        embeddings=embeddings,
        model="text-embedding-3-small"
    )
```

### Benefits

1. **Reliability**: Raw asyncpg has direct control over type registration
2. **Performance**: asyncpg is faster than SQLAlchemy ORM for vector operations
3. **Maintainability**: Clear separation - ORM for business logic, raw SQL for vectors
4. **Safety**: Deferred loading prevents accidental vector column access via ORM
5. **Scalability**: Separate connection pool for vector operations

### Trade-offs

1. **Consistency**: Two different database access patterns in the codebase
2. **Learning Curve**: Developers need to understand when to use each approach
3. **Testing**: Need to test both ORM and raw SQL paths

### Guidelines for Future Development

**DO:**
- Use SQLAlchemy ORM for all business logic and non-vector columns
- Use `vector_storage_service` for storing/querying embeddings
- Keep vector operations isolated in dedicated service classes
- Document any new vector operations clearly

**DON'T:**
- Access `embedding` column through SQLAlchemy ORM
- Try to "fix" the type registration in SQLAlchemy events (we tried, it doesn't work reliably)
- Mix ORM and raw SQL in the same transaction for vector operations
- Add vector operations to model methods (keep in services)

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Start PostgreSQL with pgvector
docker-compose up -d postgres

# Run migrations
python -m alembic upgrade head
```

### 3. Start Development Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bc_legal_db

# Redis
REDIS_URL=redis://localhost:6379

# S3 Storage
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1
S3_BUCKET_NAME=bc-legal-docs
S3_ENDPOINT_URL=http://localhost:4566  # LocalStack for development

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...

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

### Matters
- `POST /api/v1/matters` - Create matter
- `GET /api/v1/matters/{id}` - Get matter details
- `GET /api/v1/matters` - List matters
- `PUT /api/v1/matters/{id}` - Update matter

### Search
- `POST /api/v1/search/semantic` - Semantic search across documents
- `POST /api/v1/search/hybrid` - Hybrid search (keyword + semantic)

## Document Processing Pipeline

The document processing pipeline consists of several stages:

### 1. Upload
Document uploaded to S3 and metadata stored in database.

**Status:** `pending`

### 2. Text Extraction
Extract text content from PDF, DOCX, TXT files using `charset_normalizer` and other libraries.

**Status:** `text_extracted`

**Files:** `app/services/text_extraction.py`

### 3. Chunking
Split text into semantic chunks using `semantic-text-splitter` with sentence-aware splitting.

**Status:** `chunked`

**Files:**
- `app/services/chunking.py`
- `app/models/models.py` - DocumentChunk model

**Configuration:**
- Chunk size: 500-800 tokens
- Overlap: 50 tokens
- Sentence-aware splitting

### 4. Embedding Generation
Generate vector embeddings for each chunk using OpenAI's text-embedding-3-small model.

**Status:** `embedded`

**Files:**
- `app/services/embeddings.py` - OpenAI integration
- `app/services/vector_storage.py` - Raw asyncpg vector operations
- `app/services/document_processor.py` - Pipeline orchestration

**Configuration:**
- Model: text-embedding-3-small
- Dimensions: 1536
- Batch size: 100 chunks per API call
- Retry logic: 3 attempts with exponential backoff

### Manual Pipeline Triggering

Since automatic pipeline progression was removed (to prevent greenlet context errors), you can manually trigger pipeline stages:

```python
from app.services.document_processor import DocumentProcessor

async with AsyncSession() as session:
    processor = DocumentProcessor(session)

    # Trigger chunking
    await processor.process_chunking(document_id)

    # Trigger embedding generation
    await processor.process_embeddings(document_id)
```

Future enhancement: Add background task queue (Celery/RQ) for automatic progression.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_embeddings.py

# Manual pipeline test
python test_manual_pipeline.py
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
│   │   ├── embeddings.py         # OpenAI integration
│   │   ├── vector_storage.py     # Raw asyncpg for vectors
│   │   ├── document_processor.py # Pipeline orchestration
│   │   ├── chunking.py           # Text chunking
│   │   └── text_extraction.py   # Text extraction
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
4. Document any new vector operations
5. Update this README if adding new services
