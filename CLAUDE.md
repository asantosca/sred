# BC Legal Tech

AI-powered legal document intelligence platform for law firms in British Columbia.

## Quick Context

- **Backend**: FastAPI (Python) at `/backend`
- **Frontend**: React 18 + TypeScript at `/frontend`
- **Database**: PostgreSQL 15 + pgvector (1536 dimensions)
- **AI**: OpenAI embeddings (text-embedding-3-small) + Claude chat
- **Cache/Queue**: Valkey + Celery

## Key Docs

- `docs/ROADMAP.md` - Implementation phases and task tracking
- `docs/DECISIONS.md` - Strategic and technical decisions

## Common Tasks

- Start services: `docker-compose up -d` (PostgreSQL, Valkey, LocalStack, MailHog)
- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Migrations: `cd backend && alembic upgrade head`
- Tests: `cd backend && pytest` / `cd frontend && npm test`

## Architecture Notes

- Multi-tenant via `company_id` on all tables (row-level security)
- RAG pipeline: Upload -> Extract text -> Chunk -> Embed -> Store in pgvector
- Vector operations use raw asyncpg (not SQLAlchemy ORM) due to pgvector type registration issues
- Semantic chunking at paragraph/section boundaries (not fixed-size)

## Current Phase

Beta preparation. Priority gaps before beta:

1. Hybrid search (vector + BM25) - lawyers need exact term matching
2. OCR support - many legal docs are scanned PDFs

## Commit Message Rules

**IMPORTANT**: Do not include attribution to Claude in commit messages. Never add:

- "Generated with Claude Code"
- "Co-Authored-By: Claude"
- Any other Claude attribution

Use clean, single-line commit messages. No icons or emoticons.

## Troubleshooting

- Logs are located in C:\Users\alexs\projects\bc-legal-tech\backend\logs
