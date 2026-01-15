# PwC SR&ED Intelligence Platform

AI-powered SR&ED (Scientific Research and Experimental Development) tax credit analysis platform for PwC consultants.

## Quick Context

- **Backend**: FastAPI (Python 3.12+) at `/backend`
- **Frontend**: React 18 + TypeScript + Vite at `/frontend`
- **Database**: PostgreSQL 15 + pgvector (1536 dimensions)
- **AI**: OpenAI embeddings (text-embedding-3-small) + Claude chat (claude-3-7-sonnet)
- **Cache/Queue**: Valkey + Celery
- **Storage**: AWS S3 (LocalStack for local dev)

## Terminology

| Term | Description |
|------|-------------|
| Company | PwC client company claiming SR&ED credits |
| Claim | An SR&ED claim for a specific fiscal year |
| Project | R&D project within a claim |
| Consultant | PwC SR&ED team member |
| T661 | CRA form for SR&ED claims |

## Project Structure

```
sred/
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
└── docker-compose.yml   # Local development services
```

## Key Docs

- `docs/ROADMAP.md` - Implementation phases and task tracking
- `docs/DECISIONS.md` - Strategic and technical decisions
- `docs/SRED_DOMAIN.md` - SR&ED terminology and CRA requirements
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
2. **Keyword**: BM25 full-text search (exact terms like "Phase 2.3")
3. **Hybrid** (default): Combined with Reciprocal Rank Fusion (RRF)

## Key Features

- **Authentication**: JWT with refresh token rotation, password reset, email confirmation
- **Document Management**: Upload PDF/DOCX/TXT, SR&ED metadata, S3 storage
- **AI Chat**: Claude with RAG context, streaming responses, source citations
- **Hybrid Search**: Semantic + BM25 keyword search
- **Claim Management**: SR&ED claims with fiscal year tracking
- **Eligibility Reports**: AI-generated SR&ED eligibility assessments
- **T661 Drafting**: AI-generated draft responses for CRA T661 form sections
- **Consulting Hours**: Track time from conversations, AI-generated descriptions
- **Daily Briefings**: AI-generated daily summaries
- **Project Timeline**: AI-extracted R&D milestones and events from documents

## API Endpoints

Main endpoint groups in `backend/app/api/v1/endpoints/`:
- `auth.py` - Registration, login, password reset, email confirmation
- `users.py` - User management, profiles
- `claims.py` - SR&ED claim management
- `documents.py` - Document upload, download, metadata
- `search.py` - Semantic, keyword, hybrid search
- `chat.py` - AI chat with RAG
- `eligibility.py` - SR&ED eligibility report generation
- `t661.py` - T661 form draft generation
- `billable.py` - Consulting hours tracking
- `briefing.py` - Daily briefings
- `timeline.py` - Document event timeline
- `usage.py` - Usage tracking and plan limits

## Database Tables

**Core**:
- `companies` - PwC client companies
- `users` - User accounts with company_id
- `groups` - RBAC groups with JSON permissions
- `claims` - SR&ED claims (fiscal year, project info)
- `claim_access` - User access control per claim

**Documents & RAG**:
- `documents` - Document metadata (SR&ED-specific fields)
- `document_chunks` - Text chunks with embeddings (Vector 1536)
- `document_events` - Timeline events extracted from documents

**AI Chat**:
- `conversations` - Chat conversations (claim-scoped)
- `messages` - Chat messages with sources and context

**Tracking**:
- `billable_sessions` - Consulting time tracking
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
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sred_db
REDIS_URL=redis://localhost:6379
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localhost:4566
S3_BUCKET_NAME=sred-documents
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
SMTP_HOST=localhost
SMTP_PORT=1025
```

## Current Phase

POC development for PwC. Focus areas:
1. Document upload and RAG processing
2. Chat interface with SR&ED expertise
3. Eligibility report generation
4. T661 form drafting

## SR&ED Domain Context

### Five-Question Test (CRA Eligibility Criteria)
1. **Technological Uncertainty** - Was there genuine uncertainty about how to achieve the objective?
2. **Systematic Investigation** - Was there a methodical approach (hypothesis, testing, analysis)?
3. **Technological Advancement** - Was new knowledge or capability gained?
4. **Scientific/Technical Content** - Was qualified personnel involved?
5. **Documentation** - Is there contemporaneous evidence of the work?

### Eligible Expenditures
- **Salaries**: Time spent directly on R&D activities
- **Materials**: Consumed in R&D (not capital assets)
- **Contractors**: Third-party R&D work
- **Overhead**: Proxy method or traditional allocation

### Document Types for SR&ED
- `project_plan` - Technical project documentation
- `timesheet` - Labor hour records
- `email` - Email communications
- `financial` - Financial records
- `technical_report` - Technical/scientific reports
- `lab_notebook` - R&D notes
- `invoice` - Contractor invoices

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
