# BC Legal Tech

AI-powered legal document intelligence platform for law firms in British Columbia.

## Quick Context

- **Backend**: FastAPI (Python 3.12+) at `/backend`
- **Frontend**: React 18 + TypeScript + Vite at `/frontend`
- **Database**: PostgreSQL 15 + pgvector (1536 dimensions)
- **AI**: OpenAI embeddings (text-embedding-3-small) + Claude chat (claude-3-7-sonnet)
- **Cache/Queue**: Valkey + Celery
- **Storage**: AWS S3 (LocalStack for local dev)

## Project Structure

```
bc-legal-tech/
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/      # API endpoints
│   │   ├── core/        # Config, security, rate limiting, logging
│   │   ├── db/          # Database session management
│   │   ├── middleware/  # Auth, security headers, validation
│   │   ├── models/      # SQLAlchemy ORM models
│   │   ├── schemas/     # Pydantic request/response schemas
│   │   ├── services/    # Business logic layer
│   │   ├── tasks/       # Celery background tasks
│   │   └── utils/       # Helper utilities
│   ├── alembic/         # Database migrations
│   ├── tests/           # Pytest test suite
│   └── logs/            # Application logs
├── frontend/            # React 18 + TypeScript frontend
│   └── src/
│       ├── components/  # React components
│       ├── hooks/       # Custom React hooks
│       ├── lib/         # API client (axios)
│       ├── pages/       # Page components
│       ├── store/       # Zustand state management
│       ├── types/       # TypeScript type definitions
│       └── utils/       # Helper utilities
├── docs/                # Project documentation
├── .claude/commands/    # Custom slash commands
├── infrastructure/      # Terraform IaC configs
└── docker-compose.yml   # Local development services
```

## Key Docs

- `docs/ROADMAP.md` - Implementation phases and task tracking
- `docs/DECISIONS.md` - Strategic and technical decisions
- `backend/README.md` - Detailed backend architecture

## Common Tasks

```bash
# Start Docker services (PostgreSQL, Valkey, LocalStack, MailHog)
docker-compose up -d

# Backend (port 8000)
cd backend && uvicorn app.main:app --reload

# Frontend (port 3000)
cd frontend && npm run dev

# Celery worker (for background document processing)
cd backend && celery -A app.core.celery_app worker --loglevel=info

# Database migrations
cd backend && alembic upgrade head
cd backend && alembic revision -m "description"

# Tests
cd backend && pytest
cd backend && pytest --cov=app  # with coverage
cd frontend && npm test
```

**URLs**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MailHog UI: http://localhost:8025

## Architecture Notes

### Multi-Tenancy
- Row-level security via `company_id` on all tables
- All queries MUST filter by `company_id`
- JWT token contains `company_id` claim

### RAG Pipeline (Background Processing)
1. Upload document → S3 storage
2. Text extraction (PDF/DOCX/TXT)
3. Semantic chunking (paragraph/section boundaries, 500-800 tokens)
4. Embedding generation (OpenAI text-embedding-3-small)
5. Vector storage (pgvector with cosine similarity)

### Critical: Hybrid Database Pattern
Vector operations use **raw asyncpg**, NOT SQLAlchemy ORM:
- `vector_storage_service` maintains its own asyncpg pool
- Reason: pgvector type registration doesn't work reliably with SQLAlchemy async
- Use ORM for all business logic
- Use `vector_storage_service` ONLY for embedding storage/retrieval

### Search Modes
1. **Semantic**: Vector similarity (conceptual queries)
2. **Keyword**: BM25 full-text search (exact terms like "Section 12.3")
3. **Hybrid** (default): Combined with Reciprocal Rank Fusion (RRF)

## Key Features

- **Authentication**: JWT with refresh token rotation, password reset, email confirmation
- **Document Management**: Upload PDF/DOCX/TXT, extensive legal metadata, S3 storage
- **AI Chat**: Claude with RAG context, streaming responses, source citations
- **Hybrid Search**: Semantic + BM25 keyword search
- **Matter Management**: Cases/files with access control
- **Billable Hours**: Track time from conversations, AI-generated descriptions
- **Daily Briefings**: AI-generated daily summaries
- **Document Timeline**: AI-extracted events and dates from documents

## API Endpoints

Main endpoint groups in `backend/app/api/v1/endpoints/`:
- `auth.py` - Registration, login, password reset, email confirmation
- `users.py` - User management, profiles
- `matters.py` - Matter/case management
- `documents.py` - Document upload, download, metadata
- `search.py` - Semantic, keyword, hybrid search
- `chat.py` - AI chat with RAG
- `billable.py` - Billable hours tracking
- `briefing.py` - Daily briefings
- `timeline.py` - Document event timeline
- `usage.py` - Usage tracking and plan limits

## Database Tables

**Core**:
- `companies` - Tenants (law firms)
- `users` - User accounts with company_id
- `groups` - RBAC groups with JSON permissions
- `matters` - Cases/files
- `matter_access` - User access control per matter

**Documents & RAG**:
- `documents` - Document metadata (extensive legal-specific fields)
- `document_chunks` - Text chunks with embeddings (Vector 1536)
- `document_events` - Timeline events extracted from documents

**AI Chat**:
- `conversations` - Chat conversations (matter-scoped)
- `messages` - Chat messages with sources and context

**Billing**:
- `billable_sessions` - Billable time tracking
- `daily_briefings` - AI-generated summaries

## Frontend Stack

- **Build**: Vite (port 3000, proxies /api to backend)
- **Styling**: TailwindCSS
- **State**: Zustand (auth) + TanStack React Query (server state)
- **Routing**: React Router v6
- **Forms**: React Hook Form + Zod validation
- **HTTP**: Axios with JWT interceptors

## Environment Variables

Required in `backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bc_legal_db
REDIS_URL=redis://localhost:6379
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localhost:4566
S3_BUCKET_NAME=bc-legal-documents
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
SMTP_HOST=localhost
SMTP_PORT=1025
```

## Current Phase

Beta preparation. Completed:
- Core features (auth, documents, search, chat, matters)
- Hybrid search (semantic + BM25)
- Billable hours tracking
- Daily briefings
- Document timeline with event extraction

Priority gaps before beta:
1. OCR support - many legal docs are scanned PDFs
2. CI/CD pipeline

## Commit Message Rules

**IMPORTANT**: Do not include attribution to Claude in commit messages. Never add:
- "Generated with Claude Code"
- "Co-Authored-By: Claude"
- Any other Claude attribution

Use clean, single-line commit messages. No icons or emoticons.

## Troubleshooting

- **Logs**: `backend/logs/` (app.log, error.log with rotation)
- **Vector issues**: Check `vector_storage_service` - don't use ORM for embeddings
- **Background tasks**: Ensure Celery worker is running
- **Email**: Check MailHog UI at http://localhost:8025
