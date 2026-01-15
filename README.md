# PwC SR&ED Intelligence Platform

AI-powered document intelligence platform for SR&ED (Scientific Research and Experimental Development) tax credit consulting.

## Overview

This platform helps PwC SR&ED consultants:
- Upload and analyze client project documentation
- Chat with AI that understands SR&ED eligibility requirements
- Generate eligibility assessment reports
- Draft T661 form responses based on document analysis
- Track consulting hours with AI-generated descriptions

## Quick Start

### 1. Start Docker Services

```bash
docker-compose up -d
```

This starts PostgreSQL, Valkey (Redis-compatible), LocalStack (S3), and MailHog.

### 2. Start Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Start Celery Worker (for document processing)

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

## Project Structure

```
sred/
├── backend/           # FastAPI Python backend
├── frontend/          # React 18 + TypeScript frontend
├── docs/              # Documentation
└── docker-compose.yml # Local development services
```

## Development URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| MailHog (email testing) | http://localhost:8025 |

## Key Features

- **Document Upload**: PDF, DOCX, TXT with OCR for scanned documents
- **RAG-Powered Chat**: AI chat with document context and source citations
- **Eligibility Reports**: AI-generated SR&ED eligibility assessments
- **T661 Drafting**: Draft responses for CRA T661 form sections
- **Project Timeline**: Auto-extracted R&D milestones from documents
- **Hybrid Search**: Semantic + keyword search for precise retrieval

## Documentation

- [CLAUDE.md](./CLAUDE.md) - Master developer reference
- [docs/ROADMAP.md](./docs/ROADMAP.md) - Implementation roadmap
- [docs/DECISIONS.md](./docs/DECISIONS.md) - Technical decisions
- [docs/SRED_DOMAIN.md](./docs/SRED_DOMAIN.md) - SR&ED terminology guide
- [backend/README.md](./backend/README.md) - Backend architecture
- [frontend/README.md](./frontend/README.md) - Frontend guide
