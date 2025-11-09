# BC Legal Tech - Implementation Roadmap v2

AI-powered legal document intelligence platform for law firms in British Columbia.

**Last Updated**: 2025-11-08 (Matter management pages, usage tracking, schema fixes)

## Vision

Serve law firms of different sizes, from solo lawyers to large firms:

- **Solo Lawyers**: One person is tenant, admin, and user
- **Multi-User Firms**: One tenant (law firm) with multiple admins and users

---

## Current Status

**[Done] Milestones 1, 2, 2.5, 3, 4A Complete** - Full auth, document management, RAG pipeline, and AI chat system
** Next: Essential Frontend (remaining pages) → Production Deploy → Beta Launch**

---

## MILESTONE 1: Core Authentication & User Management [Done]

**Status**: [Done] **COMPLETE** - All core authentication features implemented

<details>
<summary>View completed tasks</summary>

- [x] JWT middleware for protected routes
- [x] `/api/v1/auth/me` endpoint
- [x] Refresh token endpoint
- [x] Password reset flow
- [x] Email service integration
- [x] User profile update
- [x] User avatar upload

</details>

---

## MILESTONE 2: Core Document Upload [Done]

**Status**: [Done] **COMPLETE** - Full document management with Quick Upload mode

<details>
<summary>View completed tasks</summary>

- [x] Matters table and CRUD API
- [x] Matter access control (role-based permissions)
- [x] Document metadata with type-specific fields
- [x] Security controls (confidentiality, privilege)
- [x] Document upload with S3 integration
- [x] Document classification (Contract, Pleading, Correspondence, Discovery, Exhibit)
- [x] Document listing with matter filtering
- [x] Document download with signed URLs
- [x] Document deletion with S3 cleanup

**Key Tables**: matters, documents, users, matter_access
**Supported Formats**: PDF, DOCX, DOC, TXT, MSG, EML (max 50MB)

</details>

---

## MILESTONE 2.5: Enhanced Document Classification [Done]

**Status**: [Done] **COMPLETE** - Standard Upload mode with auto-detection

<details>
<summary>View completed tasks</summary>

- [x] Type-specific field sets for all document categories
- [x] Document status tracking (Draft, Final, Executed, Filed)
- [x] Auto-detection (filename patterns, metadata extraction)
- [x] Advanced document search within matters
- [x] Duplicate detection (file hash comparison)
- [x] Standard Upload mode (17 fields)

**Upload Modes**: Quick Upload (5 fields, 60s) + Standard Upload (17 fields, 2-3min)

</details>

---

## MILESTONE 3: RAG Pipeline & Vector Search

**Status**: [Done] **COMPLETE** - Semantic search and background processing implemented

### Completed [Done]

**Core RAG Infrastructure:**

- [x] Database tables (document_chunks, document_relationships, document_processing_queue)
- [x] PGvector extension with IVFFlat indexing
- [x] Semantic chunking architecture (see RAG_ARCHITECTURE.md)
- [x] Vector dimensions configured (1536)
- [x] Text extraction service (PDF, DOCX, TXT)
- [x] Semantic chunking with legal document structure detection
- [x] Embedding generation (OpenAI text-embedding-3-small)
- [x] Hybrid database architecture (SQLAlchemy ORM + raw asyncpg for vectors)
- [x] Vector storage service (pgvector with type registration)
- [x] **Semantic search API** (`POST /api/v1/search/semantic`)
- [x] **Citation tracking** (document metadata, page numbers, similarity scores)

**What Works:**

```
Upload → Extract Text → Chunk → Generate Embeddings → Store Vectors → Semantic Search [Done]
```

### Completed in Latest Update [Done]

**Background Processing:**

- [x] **Background task queue** (Celery + Redis) [Done]
- [x] Auto-process documents after upload [Done]
- [x] Retry failed processing [Done]
- [x] Task status tracking [Done]

**Security & Validation:**

- [x] Rate limiting on API endpoints (security) [Done]
- [x] Input validation middleware (security) [Done]

### Remaining Tasks (Deferred to Post-MVP)

** LOW - Post-MVP:**

1. [ ] Document processing status dashboard
2. [ ] OCR support for scanned documents
3. [ ] Hybrid search (semantic + BM25 keyword)
4. [ ] Version control API endpoints
5. [ ] Document superseding logic
6. [ ] Similar document detection

### What We Learned

**Key Insights:**

- Semantic search alone works well (hybrid search not critical for MVP)
- Citation tracking already implemented (document metadata + page numbers in results)
- OpenAI text-embedding-3-small (1536 dims) performs well for legal documents
- Celery + Redis provides robust background processing for document pipeline

**Status**: Milestone 3 complete! Ready for production deployment.

---

## MILESTONE 4A: AI Chat System (MVP)

**Status**: [Done] **COMPLETE** - Full chat system with streaming frontend

Build conversational interface with RAG-powered responses.

### Completed [Done]

**Core Chat Infrastructure:**

- [x] Create conversations table and schemas [Done]
- [x] Messages table and schemas [Done]
- [x] Database migration for conversations/messages [Done]
- [x] Conversation CRUD endpoints (create, list, get, delete) [Done]
- [x] Message creation endpoint [Done]
- [x] Integrate Claude 3.5 Sonnet API [Done]
- [x] Implement RAG context retrieval (semantic search integration) [Done]
- [x] Build prompt engineering for legal context [Done]
- [x] Add streaming support (Server-Sent Events) [Done]
- [x] Implement conversation history management [Done]
- [x] **Always cite sources** (document name, page number, similarity scores) [Done]
- [x] Message rating system (thumbs up/down with feedback) [Done]

**Frontend Integration:**

- [x] Chat UI components (conversation list, message interface) [Done]
- [x] Streaming message display in frontend [Done]
- [x] Source citations display (clickable links to documents) [Done]
- [x] TypeScript types matching backend schemas [Done]
- [x] SSE streaming with token refresh [Done]

**What We Have:**

- [Done] Full chat backend API ([backend/app/api/v1/endpoints/chat.py](backend/app/api/v1/endpoints/chat.py))
- [Done] Chat service with RAG pipeline ([backend/app/services/chat_service.py](backend/app/services/chat_service.py))
- [Done] Complete chat frontend ([frontend/src/pages/ChatPage.tsx](frontend/src/pages/ChatPage.tsx))
- [Done] Chat components ([frontend/src/components/chat/](frontend/src/components/chat/))
- [Done] RAG context retrieval (semantic search API)
- [Done] Document metadata and citations
- [Done] Multi-tenant isolation (company_id filtering)
- [Done] Streaming responses via SSE

**New Tables**: conversations, messages (implemented)
**New Components**: ConversationList, ChatInterface, MessageInput, SourceCitations

**See Also**: [CHAT_FRONTEND_COMPLETE.md](CHAT_FRONTEND_COMPLETE.md) for detailed implementation notes

---

## MILESTONE 4B: Document Workflow (Post-MVP)

**Priority**: **Defer to post-launch**

Advanced workflow management features.

<details>
<summary>View deferred tasks</summary>

- [ ] Document review assignment system
- [ ] Review status tracking
- [ ] Priority levels (normal, high, urgent)
- [ ] Workflow instructions and internal notes
- [ ] Document access logging (table exists, not implemented)
- [ ] Notification system for assignments
- [ ] Review dashboard

**Rationale**: Chat is core value prop. Workflow is nice-to-have that can wait.

</details>

---

## MILESTONE 5A: Essential Frontend (MVP)

**Priority**: **Start in parallel with M4A**

Minimum viable UI for lawyers to use the platform.

### Core Pages

**Authentication:**

1. [x] Login page
2. [x] Register page
3. [x] Password reset flow

**Document Management:** 4. [ ] Document library (list view with filters) 5. [ ] Quick Upload form 6. [ ] Standard Upload form 7. [ ] Document viewer/preview 8. [ ] Document search interface

**Chat Interface:**
9. [x] Chat conversation list
10. [x] Chat message interface
11. [x] Streaming message display
12. [x] Source citations display (clickable links to documents)

**Matter Management:**
13. [x] Matter list page (MattersPage.tsx)
14. [x] Create/edit matter form (CreateMatterPage.tsx)
15. [x] Matter detail page with documents (MatterDetailPage.tsx)

**Infrastructure:**
16. [x] Loading states and spinners
17. [ ] Error boundaries and error handling
18. [ ] Toast notifications
19. [x] Navigation layout

**What We Skip for MVP:**

- [TBD] Dashboard with analytics
- [TBD] User management UI (admin features)
- [TBD] Settings pages
- [TBD] Dark mode
- [TBD] Mobile responsive (desktop-first for lawyers)

**Tech Stack**: React + TypeScript + Vite + TailwindCSS

**Estimated Time**: 3-4 weeks

---

## MILESTONE 5B: Enhanced Frontend (Post-MVP)

**Priority**: **Defer to post-launch**

<details>
<summary>View deferred features</summary>

- [ ] Dashboard with overview stats
- [ ] User management UI (admin)
- [ ] Settings pages (Profile, Company, Billing)
- [ ] Responsive mobile layout
- [ ] Dark mode support
- [ ] Advanced upload UI (8-screen detailed flow)
- [ ] Bulk upload interface
- [ ] Excel import for bulk metadata
- [ ] Document relationship management UI
- [ ] Upload session management (save drafts)

**Rationale**: Quick + Standard upload is sufficient for MVP. The 8-screen detailed flow is over-engineered for initial launch.

</details>

---

## MILESTONE 6: Production Infrastructure

**Priority**: **Required before beta testing**

Deploy to production environment.

### Critical Infrastructure

**Database & Storage:**

1. [ ] Production PostgreSQL (AWS RDS with backups)
2. [ ] Redis cluster for caching
3. [ ] S3 buckets with IAM policies

**Application Deployment:** 4. [ ] Backend deployment (AWS ECS) 5. [ ] Frontend deployment (CloudFront) 6. [ ] Environment configuration (Secrets Manager) 7. [ ] SSL certificates and domain setup

**Observability:** 8. [ ] Monitoring and alerting (CloudWatch) 9. [ ] Log aggregation (CloudWatch Logs) 10. [ ] Error tracking (Sentry)

**Environments:** 11. [ ] Staging environment 12. [ ] Production environment

**Estimated Time**: 1-2 weeks

---

## MILESTONE 7: Security Hardening

**Priority**: 🟡 **Some items immediate, others before launch**

### Immediate (Do During M3/M4)

**Basic Security:**

- [ ] Rate limiting on API endpoints ← DO NOW
- [ ] Input validation and sanitization ← DO NOW
- [ ] CORS configuration review
- [ ] SQL injection audit (verify ORM usage)

### Before Beta Launch

**Production Security:**

- [ ] CSRF protection (depends on frontend architecture)
- [ ] Security headers (HSTS, CSP, X-Frame-Options)
- [ ] TLS/SSL certificate management
- [ ] Security scanning and vulnerability assessment
- [ ] Penetration testing

### Before Public Launch

**Compliance:**

- [ ] Data encryption at rest
- [ ] Data retention policies
- [ ] GDPR compliance documentation
- [ ] Privacy policy and terms of service
- [ ] Backup and disaster recovery procedures

**What We Already Have:**

- [Done] Row-level security (company_id isolation)
- [Done] JWT authentication
- [Done] Parameterized queries (SQLAlchemy ORM)
- [Done] Gitignored secrets (.env file)

---

## MILESTONE 8: Testing & QA

**Priority**: 🟡 **Incremental, not a separate phase**

### Approach: Test During Development

**Unit Tests (Write alongside features):**

- [ ] Authentication service tests
- [ ] Document service tests
- [ ] RAG pipeline tests
- [ ] Search service tests
- [ ] Chat service tests

**Integration Tests (After each milestone):**

- [ ] API endpoint tests
- [ ] Database integration tests
- [ ] S3 integration tests
- [ ] OpenAI API integration tests

**E2E Tests (Before launch):**

- [ ] Critical user flows
- [ ] Document upload → search → chat flow
- [ ] Multi-user collaboration scenarios

**Performance Testing (Before launch):**

- [ ] Load testing (100+ concurrent users)
- [ ] Database query optimization
- [ ] API response time benchmarks
- [ ] Frontend performance audit

**Rationale**: Testing as a separate milestone means we're not testing during development. Better to test incrementally.

---

## MILESTONE 9: Beta Launch

**Priority**: **After M4A, M5A, M6, M7 essentials complete**

Launch with 3-5 pilot law firms.

### Pre-Launch

**Documentation:**

1. [ ] API documentation with examples
2. [ ] User guide (how to use the platform)
3. [ ] Video walkthrough (5-10 min)
4. [ ] FAQ document

**Onboarding:** 5. [ ] New user onboarding flow 6. [ ] In-app tutorials/tooltips 7. [ ] Sample documents and matters

**Support:** 8. [ ] Support email setup 9. [ ] Bug reporting system 10. [ ] Feedback collection form

### Beta Testing

**Pilot Firms:** 11. [ ] Recruit 3-5 small law firms in BC 12. [ ] Onboard each firm (1-2 users per firm) 13. [ ] Weekly check-ins and feedback sessions 14. [ ] Monitor usage and errors 15. [ ] Iterate based on feedback

**Success Criteria:**

- 80% of users successfully upload documents
- 80% of users successfully search documents
- 80% of users successfully use chat
- Average response: "Would recommend to colleague"

**Estimated Time**: 2-3 weeks

---

## MILESTONE 10: Monetization & Advanced Features

**Priority**: **Post-beta, pre-public launch**

<details>
<summary>View future features</summary>

**Monetization:**

- [ ] Usage tracking and billing metering
- [ ] Subscription management (Stripe integration)
- [ ] Plan enforcement and upgrade prompts
- [ ] Billing dashboard

**Advanced Features:**

- [ ] Google OAuth authentication
- [ ] Microsoft OAuth authentication (Office 365)
- [ ] Analytics dashboard (usage stats)
- [ ] Audit logging (document access tracking)
- [ ] API key management for programmatic access
- [ ] Webhooks for external integrations
- [ ] Custom branding (Enterprise)
- [ ] Admin panel for platform management

**What We Already Have:**

- [Done] Matter/case organization (matters table with full API)
- [Done] Multi-tenant isolation (company-based)

**Note**: Matter management already fully implemented. Remove from this milestone in future updates.

</details>

---

## Tech Stack (Actual)

Based on what we've actually built:

### Backend

- **Framework**: FastAPI (Python) with async support
- **Database**: PostgreSQL 15 with PGvector extension (bc_legal_ds schema)
- **ORM**: SQLAlchemy 2.0 (async)
- **Cache**: Redis
- **Storage**: AWS S3 (LocalStack for local dev)
- **Background Jobs**: Celery + Redis [Done]
- **Migrations**: Alembic with single consolidated initial migration

### AI/ML

- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Chat**: Claude 3.5 Sonnet (planned)
- **Vector DB**: PostgreSQL + PGvector
- **Search**: Semantic similarity (cosine distance)

### Frontend (Planned)

- **Framework**: React + TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **State Management**: React Query + Context API

### Infrastructure

- **Cloud**: AWS
- **IaC**: Terraform (structure exists, not configured)
- **Deployment**: ECS or Railway (backend), Vercel (frontend)

### Multi-Tenancy

- **Approach**: Row-level security (company_id filtering)
- **Isolation**: Company-based with JWT tokens
- **Models**: Currently shared database, can migrate to dedicated schemas later

---

## MVP Path (10-15 Weeks to Beta Launch)

### Phase 1: Production RAG (1-2 weeks) [Done] COMPLETE

**Goal**: Automatic document processing

- [x] Background task queue (Celery + Redis) [Done]
- [x] Document processing status tracking [Done]
- [x] Rate limiting [Done]
- [x] Input validation [Done]

**Deliverable**: Documents auto-process after upload

**Status**: [Done] **COMPLETE**

---

### Phase 2: AI Chat (2-3 weeks) [Done] COMPLETE

**Goal**: Conversational search with citations

- [x] Conversation & message tables [Done]
- [x] Chat CRUD endpoints [Done]
- [x] Claude 3.5 Sonnet integration [Done]
- [x] RAG context retrieval (use semantic search) [Done]
- [x] Cited sources in responses [Done]
- [x] Streaming support [Done]
- [x] Chat frontend with SSE streaming [Done]
- [x] Source citations UI [Done]
- [x] Message feedback UI [Done]

**Deliverable**: Working chat interface (backend + frontend)

**Status**: [Done] **COMPLETE** - Full chat system with streaming frontend

---

### Phase 3: Essential Frontend (3-4 weeks)

**Goal**: Usable UI for lawyers

- [x] Auth pages (Login, Register, Password Reset) [Done]
- [ ] Document library (upload, list, view)
- [x] Chat interface [Done]
- [x] Matter management [Done]
- [x] Error handling and loading states [Partial - needs error boundaries and toast notifications]

**Deliverable**: Complete end-user interface

**Progress**: Chat interface, auth pages, and matter management complete. Document library remains.

---

### Phase 4: Production Ready (2-3 weeks)

**Goal**: Deploy to production environment

- [ ] Infrastructure setup (AWS/Railway + Vercel)
- [ ] Security hardening (SSL, headers, rate limiting)
- [ ] Monitoring and logging
- [ ] Staging environment
- [ ] Performance testing
- [ ] Bug fixes

**Deliverable**: Production deployment ready for beta

---

### Phase 5: Beta Launch (2-3 weeks)

**Goal**: Launch with 3-5 pilot firms

- [ ] Documentation (user guide, API docs, FAQ)
- [ ] Onboarding flow
- [ ] Support system
- [ ] Recruit pilot firms (3-5 small BC law firms)
- [ ] Weekly feedback sessions
- [ ] Iterate based on feedback

**Deliverable**: Validated MVP with real users

---

## Success Metrics

**Beta (Phase 5):**

- 3-5 pilot law firms
- 10-20 active users
- 80%+ task completion rate
- Positive feedback ("would recommend")

**Public Launch (Post-Beta):**

- 10-20 paying law firms
- 50-100 active users
- $5K-10K MRR
- 90%+ uptime

**Scale (Year 1):**

- 50-100 law firms
- 500+ active users
- $50K+ MRR
- Multiple subscription tiers

---

## Key Differentiators

What makes BC Legal Tech unique:

1. **Legal-Specific RAG**

   - Semantic chunking that understands legal document structure
   - Always cited sources with page numbers
   - Confidence indicators for AI responses
   - "I don't know" when insufficient information

2. **BC-Focused**

   - Tailored for British Columbia law firms
   - Understands BC legal terminology
   - Future: BC case law integration

3. **Secure Multi-Tenancy**

   - Complete data isolation between firms
   - Role-based access control
   - Audit logging for compliance

4. **Matter-Centric Organization**

   - All documents organized by legal matters/cases
   - Matter-based access control
   - Easy case file management

5. **Production-Grade Architecture**
   - Hybrid database approach (ORM + raw SQL for vectors)
   - Async-first for performance
   - Scalable to thousands of firms

---

## What Changed From v1

**Completed Since Last Update (November 8, 2025 - Late Evening):**

- [Done] **Matter Management Frontend**: Complete matter list, create, and detail pages with document integration
- [Done] **Usage Tracking System**: Plan limits enforcement with document count, storage, and tier-based restrictions
- [Done] **Schema Fixes**: Added bc_legal_ds schema prefix to all SQL queries (usage_tracker, vector_storage, document_processor)
- [Done] **Database Migrations**: Created plan_limits table and usage tracking columns with proper Alembic migrations
- [Done] **Plan Tier Alignment**: Fixed default plan_tier from 'starter' to 'free' to match available plan tiers
- [Done] **Frontend-Backend Alignment**: Fixed API response structure mismatch (matters vs items)

**Completed Earlier (November 8, 2025 - Evening):**

- [Done] **Database Schema Reorganization**: Created `bc_legal_ds` dedicated schema for all application tables
- [Done] **Migration Consolidation**: Reduced 7 separate migration files into 1 clean initial migration
- [Done] **Email Confirmation Bug Fix**: Fixed dual message display issue on email confirmation page
- [Done] **Schema Benefits**: Better organization, security, and separation from PostgreSQL system tables
- [Done] **Migration Improvements**: Added explicit commit in async migration runner for reliability

**Completed Earlier (November 8, 2025 - Morning):**

- [Done] Complete chat frontend with streaming support
- [Done] Chat UI components (ConversationList, ChatInterface, MessageInput, SourceCitations)
- [Done] SSE streaming integration with token refresh
- [Done] TypeScript types matching backend Pydantic schemas
- [Done] Source citations display with document navigation
- [Done] Message feedback UI (thumbs up/down)
- [Done] Comprehensive documentation (CHAT_FRONTEND_COMPLETE.md)

**Previously Completed (November 6, 2025):**

- [Done] Background task queue (Celery + Redis) for document processing
- [Done] Rate limiting middleware for API protection
- [Done] Input validation middleware for security
- [Done] Chat API with full CRUD endpoints
- [Done] Claude 3.5 Sonnet integration for AI assistance
- [Done] Chat service with RAG pipeline integration
- [Done] Conversation and message models with database migration
- [Done] Streaming support via Server-Sent Events
- [Done] Message rating system (thumbs up/down with feedback)

**Previously Completed:**

- [Done] Semantic search API with vector similarity
- [Done] Citation tracking (document metadata + page numbers)
- [Done] Search result enrichment

**Reorganized:**

- Split M4 → M4A (Chat - MVP) + M4B (Workflow - Post-MVP)
- Split M5 → M5A (Essential UI - MVP) + M5B (Advanced Features - Post-MVP)
- Moved infrastructure to M6 (before beta, not after)
- Made testing incremental, not a separate phase
- Moved critical security items earlier

**Deferred to Post-MVP:**

- OCR support (many legal docs are digital)
- Hybrid search (semantic works well alone)
- Advanced upload UI (8-screen flow is over-engineered)
- Bulk upload with Excel import
- Version control features (less critical than chat)
- OAuth providers (can launch without)
- Dashboard analytics (can launch without)

**Added Clarity:**

- Clear MVP path (10-15 weeks)
- Phase-by-phase deliverables
- What we already have vs. what's needed
- Actual tech stack (not planned/proposed)

---

## Questions to Consider

**Before Starting Phase 1:**

1. Do we want to use Railway (simpler) or AWS (more control) for backend hosting?
2. Should we add rate limiting now or wait until after chat?
3. What's our budget for OpenAI API costs? (embeddings + chat)

**Before Starting Phase 2:** 4. How do we want to handle conversation history limits? (token limits) 5. Should chat be free or paid feature? 6. Do we need conversation export (PDF/DOCX) for MVP?

**Before Starting Phase 3:** 7. Do we need mobile responsive for lawyers? (most work on desktop) 8. Should we build our own UI components or use a library? (shadcn/ui, Chakra, etc.)

**Before Phase 5:** 9. How do we recruit pilot firms? (personal network, cold outreach, ads?) 10. What's our pricing strategy? (per user, per document, per firm?)

---

**End of Roadmap v2**

This roadmap is based on actual implementation progress as of November 8, 2025.
Current state: Milestones 1-4A complete (auth, documents, RAG, chat all working).
Next step: Complete remaining frontend pages (auth, matter management) and deploy to production.
