# BC Legal Tech - Implementation Roadmap v3

## Vision

Serve law firms of different sizes, from solo lawyers to large firms:

- **Solo Lawyers**: One person is tenant, admin, and user
- **Multi-User Firms**: One tenant (law firm) with multiple admins and users

## Tech Stack

### Backend

- **Framework**: FastAPI (Python) with async support
- **Database**: PostgreSQL 15 with pgvector extension
- **ORM**: SQLAlchemy 2.0 (async)
- **Cache/Broker**: Valkey (Redis-compatible, 20-33% cheaper than Redis)
- **Storage**: AWS S3 (LocalStack for local dev)
- **Background Jobs**: Celery + Valkey
- **Migrations**: Alembic

### AI/ML

- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Chat**: Claude claude-3-7-sonnet-20250219
- **Vector DB**: PostgreSQL + pgvector
- **Search**: Semantic similarity (cosine distance)

### Frontend

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **State Management**: Zustand + TanStack React Query

### Infrastructure

- **Cloud**: AWS (RDS, ElastiCache, S3, ECS, CloudFront)
- **IaC**: Terraform
- **Monitoring**: Sentry + CloudWatch

### Multi-Tenancy

- **Approach**: PostgreSQL Row-Level Security (RLS) policies
- **Isolation**: Company-based with JWT tokens containing `company_id`
- **Enforcement**: Database-level via `app.current_company_id` session variable

---

## Beta Success Criteria

Recruit 3-5 small law firms in BC, onboard each firm (1-2 users per firm), weekly check-ins and feedback sessions, monitor usage and errors, iterate based on feedback.

- 80% of users successfully upload documents
- 80% of users successfully search documents
- 80% of users successfully use chat
- Average response: "Would recommend to colleague"

---

## Section 1: Core Features (COMPLETE)

- [x] JWT authentication with refresh token rotation
- [x] Document upload (PDF, DOCX, TXT)
- [x] Semantic search with embeddings
- [x] Chat with RAG and source citations
- [x] Matter management with access control
- [x] Rate limiting (slowapi)
- [x] Input validation middleware
- [x] CORS configuration
- [x] Security headers (CSP, HSTS, X-Frame-Options)
- [x] Usage tracking with plan limits
- [x] Dashboard with usage stats
- [x] Mobile responsive layout

---

## Section 2: Pre-Deployment Hardening (COMPLETE)

- [x] Security scanning and vulnerability assessment
- [x] SQL injection audit (verify ORM usage)
- [x] Tenant isolation audit (company_id filtering on all queries)
- [x] PostgreSQL Row-Level Security (RLS) implementation
  - Database-enforced tenant isolation via RLS policies
  - JWT middleware extracts company_id and sets `app.current_company_id` session variable
  - All tenant tables have RLS policies filtering by company_id
  - Documents table denormalized with company_id for RLS query performance
  - Verification script to test cross-tenant isolation
- [x] CORS configuration review (add production domains)
- [x] Sample data on signup (welcome matter and getting started conversation)
- [x] Matter-scoped conversations
- [x] Chat history as searchable knowledge (lazy-generated summaries + full-text search)
- [x] Billable hours tracking with AI-written descriptions

---

## Section 3: Beta-Critical Features

_Must complete before beta users can test with real documents_

**RAG Quality (Critical for Beta Feedback):**

- [x] Hybrid search (semantic + BM25 keyword)
  - Lawyers search for exact terms: "Section 12.3", "Smith v. Jones"
  - Vector-only search misses these exact matches
  - Implemented using PostgreSQL tsvector + GIN index with RRF score fusion

- [x] OCR support for scanned documents
  - AWS Textract (production) with Tesseract fallback (local dev)
  - Supports scanned PDFs and image files (PNG, JPG, TIFF)
  - Automatic detection of scanned PDFs based on text density
  - OCR metadata tracked (engine, confidence, pages processed)

- [x] AI document summaries for RAG context enhancement
  - Auto-generates document summary during processing using Claude
  - Summaries included in chat context alongside retrieved chunks
  - Hierarchical summarization for very long documents
  - Internal only (not exposed to users), improves answer quality

**Legal Source Transparency (Addressing Hallucination Concerns):**

_Lawyers fear AI hallucination. Rather than building a full legal research platform, we focus on transparency about knowledge sources and easy verification._

- [ ] Epistemic honesty in Claude prompts
  - Distinguish "from your documents" vs "general legal knowledge"
  - Require Claude to flag unverified legal claims
  - Never invent case names or statute section numbers
  - Explicitly state when verification is needed

- [ ] UI source distinction
  - Visual separation: "From Your Documents" vs "General Legal Knowledge (Verify)"
  - Different styling/icons for each source type
  - Clear indication when AI is uncertain

- [ ] Auto-link statutes to BC Laws
  - Regex detection of statute references (e.g., "Limitation Act, SBC 2012, c 13")
  - Auto-generate links to bclaws.gov.bc.ca for verification
  - No embedding/indexing required - just linking

- [ ] Auto-link cases to CanLII search
  - Regex detection of case citations (e.g., "2024 SCC 15", "2023 BCCA 412")
  - Auto-generate CanLII search links for verification
  - No API key required - just search URL generation

_Future (only if customer demand):_
- BC Laws statute full-text search integration
- CanLII case retrieval with API
- Authority ranking (binding vs persuasive)

**Performance:**

- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Database query optimization
- [ ] API response time benchmarks

**Cost Monitoring (Beta Operations):**

- [x] API usage logging for cost tracking
  - Tracks tokens for Claude (chat, summaries) and OpenAI (embeddings)
  - Estimates costs based on current API pricing
  - Platform admin API endpoints for usage queries
  - Per-company and per-service breakdowns

---

## Section 4: AWS Infrastructure Deployment

_Must complete before beta users can access_

**Database and Cache:**

- [ ] Production PostgreSQL (AWS RDS with automated backups)
- [ ] Production Valkey cluster (AWS ElastiCache)

**Storage:**

- [ ] Production S3 buckets with IAM policies

**Compute:**

- [ ] Backend deployment (AWS ECS or App Runner)
- [ ] Frontend deployment (AWS Amplify: app.bclegaltech.ca)

**Networking and Security:**

- [ ] SSL certificates (AWS ACM)
- [ ] Domain setup (Route 53)
- [ ] Environment configuration (AWS Secrets Manager)

**Environments:**

- [ ] Staging environment (mirrors production)
- [ ] Production environment

**Observability:**

- [ ] Monitoring and alerting (CloudWatch)
- [ ] Log aggregation (CloudWatch Logs)
- [ ] Uptime monitoring
- [x] Local file logging with rotation (app.log, error.log)

---

## Section 5: Support Setup

_Must complete before beta users can access_

**Support:**

- [ ] Support email setup (@bclegaltech.ca)
- [ ] Bug reporting system (can use GitHub Issues initially)
- [ ] Feedback collection form

**Email:**

- [ ] AWS SES setup for transactional emails

---

## BETA PROGRAM STARTS

---

## Section 6: Beta Feedback Implementation

_Implement during beta based on user feedback_

- [ ] New user onboarding flow
- [ ] Empty state improvements with tips
- [ ] Welcome email for new signups

---

## Section 7: MVP Features

_Required for public launch after beta_

**RAG Quality (Differentiators):**

- [x] Confidence scoring on AI responses
  - Question quality scoring based on length, specificity, context
  - Response confidence scoring combining explicit feedback and implicit signals
  - Admin visibility via API endpoints

- [ ] Re-ranking of retrieved chunks
  - Improves answer quality noticeably
  - Differentiates from basic ChatGPT + copy-paste

- [ ] Excel/spreadsheet support
  - Common in corporate/real estate law
  - Financial schedules, closing checklists

**Billing and Payments:**

- [ ] Stripe subscription management
- [ ] Usage tracking and billing metering
- [ ] Plan enforcement and upgrade prompts
- [ ] Billing dashboard

**Admin and Settings:**

- [ ] User management UI (admin)
- [ ] Settings pages (Profile, Company, Billing)
- [ ] Admin panel for platform management

**Document Features:**

- [ ] Document viewer/preview in browser
- [ ] Advanced document search with filters

**Chat Features:**

- [x] Copy-to-clipboard on AI messages
- [x] AI response feedback analytics
  - Explicit feedback with categories (incorrect, irrelevant, wrong question, not detailed, no documents)
  - Implicit behavioral signals (copy events, source clicks, session tracking, rephrase detection)
  - Question quality scoring and response confidence scores
  - Admin API endpoints for stats, alerts, and flagged messages
  - Celery tasks for periodic aggregation and alert checking
- [x] Question improvement suggestions
  - Displays tips to improve question quality after AI responses
  - Uses RAG similarity scores, Claude confidence, and question heuristics
  - Collapsible UI with contextual suggestions
- [ ] Export conversation as PDF/DOCX

**Legal and Compliance:**

- [ ] Privacy policy and terms of service
- [ ] Data Processing Agreement (for enterprise)
- [ ] Get legal review from lawyer
- [ ] GDPR compliance documentation
- [ ] Data retention policies
- [ ] Backup and disaster recovery procedures

**Performance:**

- [ ] Load testing (100+ concurrent users)
- [ ] Frontend performance audit
- [ ] Data encryption at rest

**Analytics:**

- [ ] Analytics setup (Plausible or GA4 with consent)

---

## MVP LAUNCH

---

## Section 8: Post-MVP Enhancements

_Future features after public launch. Prioritize based on customer feedback._

**Authentication (For Firm Adoption):**

- [ ] Google OAuth authentication
- [ ] Microsoft OAuth authentication (Office 365)
- [ ] Role hierarchy (Partner, Associate, Paralegal, Guest)
- [ ] Session management UI (view active sessions, revoke devices)

**AI/ML Optimization:**

- [ ] Evaluate Voyage AI voyage-law-2 embeddings (legal-specific)
  - Would require schema migration (1536 -> 1024 dimensions)
  - Test after sufficient usage data to benchmark

**Agentic RAG (Complex Query Handling):**

- [ ] Query decomposition for multi-part questions
  - Break complex legal questions into sub-queries
  - Aggregate results across multiple retrieval steps
- [ ] Checklist verification against matter documents
  - "Has client provided all required intake documents?"
  - Compare requirements against uploaded documents
- [ ] Compliance gap analysis
  - "What requirements is opposing party not meeting?"
  - Cross-reference legal requirements with matter facts
- [ ] Iterative retrieval for research queries
  - Agent searches, evaluates relevance, refines, searches again
  - Self-correcting search for ambiguous queries

**Document Features:**

- [x] Document timeline (event extraction from documents)
  - Auto-extracts dates and events during document processing
  - Shows chronological timeline view across matters
  - Supports date precision and confidence levels
  - User can create/edit/delete events
- [ ] Bulk upload interface (multiple files at once)
- [ ] Version control API endpoints
- [ ] Document superseding logic
- [ ] Similar document detection
- [ ] Document relationship management UI
- [ ] Type-specific upload forms:
  - Contract Upload (contract type, value, dates, governing law)
  - Pleading Upload (court, case number, judge, opposing counsel)
  - Correspondence Upload (author, recipient, CC, subject)
  - Discovery Upload (type, parties, response due date)
  - Exhibit Upload (exhibit number, related document linking)

**Chat Enhancements:**

- [x] Chat mode redesign with three distinct modes:
  - **Matter Chat**: RAG search within selected matter's documents
  - **AI Discovery**: General legal AI without RAG, auto-detects related matters
  - **Help Desk**: Platform assistance via separate modal (uses Haiku model)
- [x] Matter linking from Discovery mode (AI suggests related matters)
- [ ] Share conversation with colleague
- [ ] Search across all conversations
- [ ] "Ask about this document" button

**Billable Hours and Export:**

- [x] Unbilled work reminders (Dashboard + Matter detail page)
- [ ] Export formats: CSV, PDF, Clio, PracticePanther

**UI/UX Enhancements:**

- [x] Marketing site redesign (refined editorial dark theme with Playfair Display + Sora fonts)
- [ ] Dark mode support
- [ ] In-app tutorials/tooltips
- [ ] Video walkthrough (5-10 min)

**Integrations and Enterprise:**

- [ ] Webhooks for external integrations
- [ ] API key management for programmatic access
- [ ] Custom branding (Enterprise)
- [ ] Practice area specialization (templates, taxonomy)
- [ ] Audit logging UI

**Security Hardening:**

- [ ] Migrate from localStorage JWT to httpOnly cookie sessions
- [ ] CSRF protection (required for cookie-based auth)
- [ ] Penetration testing

**Documentation (when scaling):**

- [ ] API documentation with examples
- [ ] User guide (how to use the platform)
- [ ] FAQ document

**Scale:**

- [ ] CloudFront CDN for global distribution
- [ ] Multi-region deployment
