# BC Legal Tech - Implementation Roadmap v2

AI-powered legal document intelligence platform for law firms in British Columbia.

**Last Updated**: 2025-11-09 (Phase 3.5 marketing site enhancements complete)

## Vision

Serve law firms of different sizes, from solo lawyers to large firms:

- **Solo Lawyers**: One person is tenant, admin, and user
- **Multi-User Firms**: One tenant (law firm) with multiple admins and users

---

## Current Status

**[Done] Milestones 1, 2, 2.5, 3, 4A, 5A Complete** - Full stack MVP with error tracking
**Next: Production Infrastructure (M6) → Beta Launch (M9)**

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
- Celery + Valkey provides robust background processing for document pipeline

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
- [x] Optimistic UI updates (pending messages) [Done]
- [x] Conversation selection and state management [Done]

**Bug Fixes (2025-11-09):**

- [x] Fixed UUID serialization in message sources (mode='json') [Done]
- [x] Fixed SSE chunk formatting to include conversation_id at top level [Done]
- [x] Fixed conversation selection for new chats (empty state issue) [Done]
- [x] Implemented optimistic message rendering during streaming [Done]
- [x] Fixed React Query cache synchronization issues [Done]

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

**Status**: [Done] **COMPLETE** - All essential frontend features implemented

Minimum viable UI for lawyers to use the platform.

### Core Pages

**Authentication:**

1. [x] Login page
2. [x] Register page
3. [x] Password reset flow

**Document Management:**

4. [x] Document library (DocumentsPage.tsx with DocumentList component)
5. [x] Quick Upload form (5 fields: matter, type, title, date, confidentiality)
6. [ ] Standard Upload form (12 fields: adds author, recipient, dates, notes) - **Post-MVP**
7. [ ] Type-specific upload forms (Contract, Pleading, Correspondence, Discovery, Exhibit) - **Post-MVP**
8. [ ] Document viewer/preview - **Nice to have**
9. [ ] Document search interface - **Nice to have**

**Chat Interface:**

10. [x] Chat conversation list
11. [x] Chat message interface
12. [x] Streaming message display
13. [x] Source citations display (clickable links to documents)

**Matter Management:**

14. [x] Matter list page (MattersPage.tsx)
15. [x] Create/edit matter form (CreateMatterPage.tsx)
16. [x] Matter detail page with documents (MatterDetailPage.tsx)

**Infrastructure:**

17. [x] Loading states and spinners
18. [x] Error boundaries and error handling
19. [x] Toast notifications (react-hot-toast)
20. [x] Navigation layout

**What We Skip for MVP:**

- Dashboard with analytics
- User management UI (admin features)
- Settings pages
- Dark mode
- Mobile responsive (desktop-first for lawyers)
- Standard Upload form (12 fields)
- Type-specific upload forms (Contract, Pleading, etc.)
- Document viewer/preview
- Document search interface

**Tech Stack**: React + TypeScript + Vite + TailwindCSS

**Estimated Time**: 3-4 weeks

---

## MILESTONE 5B: Enhanced Frontend (Post-MVP)

**Priority**: **Defer to post-launch**

<details>
<summary>View deferred features</summary>

**Enhanced Document Upload:**
- [ ] Standard Upload form (12 fields: Quick Upload + author, recipient, dates, internal notes)
- [ ] Type-specific upload forms:
  - [ ] Contract Upload (adds: contract type, value, effective/expiration dates, governing law)
  - [ ] Pleading Upload (adds: court jurisdiction, case number, opposing party, judge, opposing counsel)
  - [ ] Correspondence Upload (adds: author, recipient, CC, subject, correspondence type)
  - [ ] Discovery Upload (adds: discovery type, propounding/responding parties, response due date)
  - [ ] Exhibit Upload (adds: exhibit number, related document linking)
- [ ] Bulk upload interface (multiple files at once)
- [ ] Excel import for bulk metadata
- [ ] Upload session management (save drafts)
- [ ] Document viewer/preview in browser

**Other Enhanced Features:**
- [ ] Dashboard with overview stats
- [ ] User management UI (admin)
- [ ] Settings pages (Profile, Company, Billing)
- [ ] Responsive mobile layout
- [ ] Dark mode support
- [ ] Document relationship management UI
- [ ] Advanced document search with filters

**Rationale**: Quick Upload (5 fields) is sufficient for MVP. Standard and type-specific uploads add nice-to-have metadata that can wait until users request them based on actual usage patterns.

</details>

---

## MILESTONE 6: Production Infrastructure

**Priority**: **Required before beta testing**

Deploy to production environment.

### Critical Infrastructure

**Database & Storage:**

1. [ ] Production PostgreSQL (AWS RDS with backups)
2. [ ] Valkey cluster for caching and task queue (AWS ElastiCache)
3. [ ] S3 buckets with IAM policies

**Application Deployment:** 4. [ ] Backend deployment (AWS ECS) 5. [ ] Frontend deployment (CloudFront) 6. [ ] Environment configuration (Secrets Manager) 7. [ ] SSL certificates and domain setup

**Observability:**
8. [ ] Monitoring and alerting (CloudWatch)
9. [ ] Log aggregation (CloudWatch Logs)
10. [x] Error tracking (Sentry - configured for dev/staging/prod)

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
- **Cache**: Valkey (Redis-compatible, open source)
- **Storage**: AWS S3 (LocalStack for local dev)
- **Background Jobs**: Celery + Valkey [Done]
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

## MVP Path (12-17 Weeks to Beta Launch)

### Phase 1: Production RAG (1-2 weeks) [Done] COMPLETE

**Goal**: Automatic document processing

- [x] Background task queue (Celery + Valkey) [Done]
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

### Phase 3: Essential Frontend (3-4 weeks) [Done] COMPLETE

**Goal**: Usable UI for lawyers

- [x] Auth pages (Login, Register, Password Reset) [Done]
- [x] Document library (DocumentsPage with DocumentList) [Done]
- [x] Quick Upload form (5 fields) [Done]
- [x] Chat interface [Done]
- [x] Matter management [Done]
- [x] Error boundaries [Done]
- [x] Toast notifications (react-hot-toast) [Done]

**Deliverable**: Complete end-user interface

**Status**: [Done] **COMPLETE** - All essential frontend features implemented. Standard Upload and type-specific upload forms are Post-MVP enhancements.

---

### Phase 3.5: Marketing Website & Legal Compliance (1-2 weeks) [Done]

**Goal**: Professional web presence and legal compliance for beta launch

**Marketing Site (www.bclegaltech.ca):**

- [x] Next.js 14 marketing site setup in `/marketing` folder (monorepo) [Done]
- [x] Landing page (hero, features, value proposition, CTA) [Done]
- [x] Features page (detailed product capabilities) [Done]
- [x] Pricing/Early Access page [Done]
- [x] About Us page (company, mission, team) [Done]
- [x] Contact form with waitlist signup [Done]

**Waitlist System:**

- [x] Add `waitlist_signups` table to PostgreSQL (bc_legal_ds schema) [Done]
- [x] Public FastAPI endpoint: `POST /api/v1/public/waitlist` [Done]
- [x] Email capture with validation and duplicate prevention [Done]
- [x] Track attribution (UTM parameters, source page) [Done]
- [x] CASL consent tracking (consent_marketing + consent_date fields) [Done]
- [x] Fix duplicate email error handling (proper 400 responses) [Done]
- [ ] Admin view to manage waitlist (internal tool) [Deferred]

**Legal & Compliance Pages:**

- [x] Privacy Policy (BC/Canadian privacy law compliance) [Done - Template]
- [x] Terms of Service (liability, acceptable use, account terms) [Done - Template]
- [x] Cookie Policy with consent banner (GDPR-compliant) [Done]
- [x] CASL compliance (Canada Anti-Spam Legislation) [Done]
- [x] Legal review checklist for lawyer (LEGAL_REVIEW_CHECKLIST.md) [Done]
- [ ] Data Processing Agreement (for enterprise law firms) [Deferred]
- [x] Get legal review from lawyer (critical for legal tech) [Scheduled]

**Email & Analytics:**

- [ ] Create required email accounts (@bclegaltech.ca domain)
  - [ ] noreply@bclegaltech.ca - transactional emails (password resets, confirmations)
  - [ ] hello@bclegaltech.ca - general inquiries (marketing site)
  - [ ] support@bclegaltech.ca - customer support (marketing site)
  - [ ] privacy@bclegaltech.ca - privacy inquiries (privacy policy, cookie policy)
  - [ ] legal@bclegaltech.ca - legal inquiries (terms of service)
  - Note: Currently only alexandre@bclegaltech.ca exists
- [ ] AWS SES setup for transactional emails (@bclegaltech.ca)
- [ ] Welcome email for waitlist signups
- [ ] Analytics setup (Plausible or GA4 with consent)
- [x] Cookie consent management [Done]

**Cross-Site Navigation:**

- [x] AuthLayout for login/register pages with header/footer [Done]
- [x] Marketing site header with Login/Get Started buttons [Done]
- [x] App logout redirects to marketing site [Done]
- [x] Environment variables for cross-site URLs [Done]
- [x] Legal document links point to marketing site [Done]

**UI/UX Improvements:**

- [x] Remove duplicate headers from all marketing pages [Done]
- [x] Update CTAs from "Join Waitlist" to "Start Free Trial" [Done]
- [x] Consistent messaging across all marketing pages [Done]
- [x] Fix React Router future flag warnings [Done]

**Deployment:**

- [ ] AWS Amplify deployment from GitHub (`/marketing` folder) [Ready]
- [ ] Custom domain setup (www.bclegaltech.ca)
- [ ] SSL certificate configuration (AWS ACM)
- [ ] CloudFront CDN for global distribution

**Tech Stack:**
- Next.js 14 (static export) + TailwindCSS
- React Hook Form for forms
- AWS Amplify for hosting
- Shared FastAPI backend for waitlist API

**Repository Structure:**
```
bc-legal-tech/ (monorepo)
├── backend/          # Existing FastAPI
├── frontend/         # Existing React app
├── marketing/        # NEW - Next.js marketing site
└── docs/
```

**Deliverable**: Professional marketing website with waitlist capture and legal compliance pages

**Status**: [Done] **COMPLETE** - Marketing site fully functional with all legal pages, CASL compliance, cross-site navigation, and consistent branding. Ready for AWS Amplify deployment.

**Why This Matters**: Law firms need to see privacy policy, terms, and professional branding before trusting you with confidential legal documents. This is non-negotiable for beta launch.

---

### Phase 4: Production Infrastructure (2-3 weeks)

**Goal**: Deploy application to production environment

**Infrastructure Setup:**

- [ ] Production PostgreSQL (AWS RDS with automated backups)
- [ ] Production Valkey cluster (AWS ElastiCache - 20-33% cheaper than Redis)
- [ ] Production S3 buckets with IAM policies
- [ ] Backend deployment (AWS ECS or App Runner from GitHub)
- [ ] Frontend deployment (AWS Amplify: app.bclegaltech.ca)
- [ ] Environment configuration (AWS Secrets Manager)
- [ ] SSL certificates and domain setup (Route 53 + ACM)

**Security Hardening:**

- [ ] CORS configuration review
- [ ] Security headers (HSTS, CSP, X-Frame-Options)
- [ ] SQL injection audit (verify ORM usage)
- [ ] Security scanning and vulnerability assessment

**Observability:**

- [ ] Monitoring and alerting (CloudWatch)
- [ ] Log aggregation (CloudWatch Logs)
- [x] Error tracking (Sentry - already configured)
- [ ] Uptime monitoring

**Environments:**

- [ ] Staging environment (mirrors production)
- [ ] Production environment
- [ ] CI/CD pipeline from GitHub

**Performance:**

- [ ] Load testing (100+ concurrent users)
- [ ] Database query optimization
- [ ] API response time benchmarks
- [ ] Frontend performance audit

**Deliverable**: Production-ready infrastructure ready for beta testing

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

**Completed This Session (November 22, 2025 - Valkey Migration):**

- [Done] **Valkey Migration Complete**: Migrated from Redis to Valkey across entire codebase
  - Updated docker-compose.yml to use valkey/valkey:8-alpine
  - Updated all configuration files (config.py, .env.example)
  - Updated all documentation (14 files total)
  - Created comprehensive VALKEY_DECISION.md explaining rationale and cost savings
  - Zero code changes required (100% Redis-compatible)
  - Tested locally: all services running successfully
- [Done] **Cost Optimization**: Infrastructure decision for 20-33% AWS cost savings
  - Documented serverless vs node-based pricing models
  - Recommended ElastiCache Serverless for current stage (~$6-50/month)
  - Projected savings: $15K-25K/year for production workload
- [Done] **Documentation Updates**: Complete consistency across all docs
  - README.md, backend/README.md
  - ROADMAP.md, COST_CONTROLS.md, RUNNING-BACKEND.md, TESTING-GUIDE.md
  - BACKGROUND_PROCESSING.md
  - Claude Code context files (.claude/context/, .claude/commands/)
  - All references now mention Valkey with cost savings notes

**Completed Earlier (November 9, 2025 - Phase 3.5 Complete):**

- [Done] **Phase 3.5 Complete**: Marketing website with full legal compliance and cross-site navigation
- [Done] **Marketing Site Infrastructure**: Next.js 14 marketing site in `/marketing` folder (monorepo)
  - Landing page with hero, features, and waitlist form
  - Features page with detailed product capabilities
  - About Us page with mission, values, and company info
  - Contact/Waitlist page with React Hook Form integration
  - Pricing page (placeholder for beta)
- [Done] **Waitlist System Backend**: Full backend integration for marketing waitlist
  - Database migration: `waitlist_signups` table in bc_legal_ds schema
  - SQLAlchemy model: `WaitlistSignup` with tracking fields
  - Pydantic schemas: `WaitlistSignupCreate` and `WaitlistSignupResponse`
  - Public API endpoint: `POST /api/v1/public/waitlist` (no auth required)
  - Rate limiting: 3 signups per minute per IP
  - Email validation and duplicate prevention
  - UTM parameter tracking for attribution
- [Done] **Legal Pages Complete**: All legal compliance pages for marketing site
  - Privacy Policy: Comprehensive template covering BC/Canadian privacy law (11 sections)
  - Terms of Service: Complete terms covering all aspects of service usage (14 sections)
  - Cookie Policy: Detailed cookie usage and management guide with tables
  - Cookie Consent Banner: GDPR-compliant banner with granular preferences
- [Done] **Repository Organization**: Docs moved to `/docs` folder for better structure
- [Done] **AWS Amplify Configuration**: Created amplify.yml for `/marketing` folder deployment
- [Done] **CASL Compliance Implementation**: Full Canada Anti-Spam Legislation compliance
  - Added consent_marketing and consent_date fields to waitlist_signups table
  - Database migration for CASL tracking fields
  - Updated Pydantic schemas with consent fields
  - Explicit checkbox on waitlist form with clear language
  - Consent timestamp recording in database
  - Legal review checklist includes CASL compliance section
- [Done] **Waitlist Error Handling Fixes**: Proper HTTP status codes for duplicate emails
  - Fixed HTTPException handling to return 400 instead of 500
  - Added consent fields to WaitlistSignupResponse schema
  - Updated CORS to allow marketing site (localhost:3001)
- [Done] **Cross-Site Navigation System**: Seamless navigation between marketing and app
  - Created AuthLayout component with header/footer for login/register pages
  - Added Header component to marketing site with Login/Get Started buttons
  - Environment variables for app URL (localhost:3000 dev, app.bclegaltech.ca prod)
  - Logout from app redirects to marketing site
  - Legal links in registration form point to marketing site
- [Done] **Marketing Site UI/UX Improvements**: Professional, consistent branding
  - Removed duplicate navigation headers from all marketing pages
  - Updated all CTAs from "Join Waitlist" to "Start Free Trial"
  - Consistent messaging across features, pricing, about, and contact pages
  - Fixed React Router future flag warnings in main app
  - Adjusted contact form spacing and messaging
- [Done] **Legal Review Documentation**: Comprehensive checklist for lawyer review
  - Created LEGAL_REVIEW_CHECKLIST.md with 16 questions
  - Documented all BC/Canadian specific legal requirements
  - Identified high-priority legal risks and considerations
  - Technical context for lawyer understanding data flow

**Completed Earlier This Session (November 9, 2025 - Phase 3 Complete):**

- [Done] **Phase 3 Complete**: Implemented error boundaries and toast notifications for production-ready error handling
- [Done] **Sentry Error Tracking**: Full integration for both backend (FastAPI) and frontend (React)
  - Backend: Sentry SDK with FastAPI integration, test endpoints, environment configuration
  - Frontend: Sentry initialization with privacy settings (maskAllText, blockAllMedia for legal documents)
  - Documentation: Comprehensive SENTRY_SETUP.md with setup guide and troubleshooting
  - Privacy: Configured to protect sensitive legal data (no PII, masked text in replays)
- [Done] **Error Boundary Component**: Full error UI with dev/prod modes and Sentry integration
- [Done] **Toast Notifications**: Integrated react-hot-toast across auth, documents, matters, and chat
- [Done] **TypeScript Fixes**: Added missing props (Button.icon, DocumentUpload.matterId)
- [Done] **BC Test Data**: Created realistic British Columbia legal test data for two law firms with multiple matters
- [Done] **Celery Worker Docker Integration**: Fixed S3 lazy initialization preventing import-time connection errors
- [Done] **Document Processing Pipeline**: Added missing text extraction step (Extract → Chunk → Embed)
- [Done] **Asyncio Event Loop Fix**: Changed from `asyncio.run()` to `loop.run_until_complete()` for Celery compatibility
- [Done] **Environment Configuration**: Created Docker-compatible environment variable setup with root .env file
- [Done] **Valkey Migration**: Migrated from Redis to Valkey for cost savings (20-33% cheaper on AWS ElastiCache)
- [Done] **AWS Endpoint Configuration**: Fixed hardcoded localhost to use proper Docker service hostnames
- [Done] **Chat Service Model Fixes**: Fixed attribute mismatches (doc.title → doc.document_title, matter.name → matter.matter_number)
- [Done] **Docker Containerization**: Created Dockerfile and .dockerignore for Celery worker deployment

**Completed Earlier (November 8, 2025 - Late Evening):**

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

- [Done] Background task queue (Celery + Valkey) for document processing
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
