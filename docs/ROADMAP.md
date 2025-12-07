# BC Legal Tech - Implementation Roadmap v2

## Vision

Serve law firms of different sizes, from solo lawyers to large firms:

- **Solo Lawyers**: One person is tenant, admin, and user
- **Multi-User Firms**: One tenant (law firm) with multiple admins and users

## Tech Stack (Actual)

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

**Infrastructure**:
AI-powered legal document intelligence platform for law firms in British Columbia.
This is an app that uses PostgreSQL in (AWS RDS with backups)
It uses Valkey cluster for caching and task queue (AWS ElastiCache)
S3 buckets with IAM policies are used for document uploads
Backend deployment (AWS ECS)
Frontend deployment (CloudFront)
Environment configuration (Secrets Manager)
SSL certificates and domain setup
Monitoring and alerting (CloudWatch)
Log aggregation (CloudWatch Logs)

---

The plan is: once the system is deployed to production, recruit 3 to 5 small law firms in BC, onboard each firm (1-2 users per firm), weekly check-ins and feedback sessions, monitor usage and errors, iterate based on feedback.

Our Success Criteria:

- 80% of users successfully upload documents
- 80% of users successfully search documents
- 80% of users successfully use chat
- Average response: "Would recommend to colleague"

How do we get there:
Develop an easy to use system that delivers quality and accurate results.

# BC Legal Tech - Development Roadmap

Implementation order: Each section must complete before the next begins.

---

## Section 1: Core Features (COMPLETE)

_Foundation is ready_

- [x] JWT authentication with refresh token rotation
- [x] Document upload (all form types)
- [x] Semantic search with embeddings
- [x] Chat with RAG and source citations
- [x] Matter management
- [x] Rate limiting (slowapi)
- [x] Input validation middleware
- [x] CORS configuration
- [x] Security headers (CSP, HSTS, X-Frame-Options)
- [x] Usage tracking with plan limits
- [x] Dashboard with usage stats
- [x] Mobile responsive layout

---

## Section 2a: Pre-Deployment Hardening

_Must complete before deploying to AWS_

- [x] Security scanning and vulnerability assessment
- [x] SQL injection audit (verify ORM usage)
- [x] Tenant isolation audit (company_id filtering on all queries)
- [x] CORS configuration review (add production domains)
- [ ] CI/CD pipeline from GitHub (GitHub Actions)
- [ ] Database query optimization
- [ ] API response time benchmarks

---

## Section 2b: Product Differentiation

_Even though these could be done after MVP, they will help differentiate the product_

- [x] Sample data on signup (welcome matter and getting started conversation)
- [x] Matter-scoped conversations (matter_id on conversations)
- [x] Matter dropdown on new conversation
- [x] Show matter badge in conversation list
- [x] Show confidence level on AI responses
- [x] Chat history as searchable knowledge (lazy-generated summaries + full-text search)
- [x] Billable hours: Generate AI-written description of legal work performed
- [x] Billable hours: Calculate session duration from timestamps

---

## Section 3: AWS Infrastructure Deployment

_Must complete before beta users can access_

**Database and Cache:**

- [ ] Production PostgreSQL (AWS RDS with automated backups)
- [ ] Production Valkey cluster (AWS ElastiCache - 20-33% cheaper than Redis)

**Storage:**

- [ ] Production S3 buckets with IAM policies

**Compute:**

- [ ] Backend deployment (AWS ECS or App Runner from GitHub)
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

---

## Section 4: Documentation and Support Setup

_Must complete before beta users can access_

**Documentation:**

- [ ] API documentation with examples
- [ ] User guide (how to use the platform)
- [ ] FAQ document

**Support:**

- [ ] Support email setup (@bclegaltech.ca)
- [ ] Bug reporting system
- [ ] Feedback collection form

**Email:**

- [ ] AWS SES setup for transactional emails

---

## BETA PROGRAM STARTS

---

## Section 5: Beta Feedback and Onboarding

_Implement during beta based on user feedback_

- [ ] New user onboarding flow
- [ ] Empty state improvements with tips
- [ ] Welcome email for new signups

---

## Section 6: MVP Features

_Required for public launch after beta_

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

- [ ] Copy-to-clipboard on AI messages
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

## Section 7: Post-MVP Enhancements

_Future features after public launch. Discuss with customers what makes sense._

**Authentication Enhancements:**

- [ ] Google OAuth authentication
- [ ] Microsoft OAuth authentication (Office 365)
- [ ] Migrate from localStorage JWT to httpOnly cookie sessions
- [ ] Session management UI (view active sessions, revoke devices)
- [ ] CSRF protection (required for cookie-based auth)

**Document Features:**

- [ ] OCR support for scanned documents
- [ ] Hybrid search (semantic + BM25 keyword)
- [ ] Bulk upload with Excel import
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
- [ ] Upload session management (save drafts)

**Chat Enhancements:**

- [ ] Filter RAG retrieval to selected matter's documents
- [ ] Share conversation with colleague
- [ ] Search across all conversations
- [ ] "Ask about this document" button

**Billable Hours and Export:**

- [ ] Export formats: CSV, PDF, Clio, PracticePanther

**UI/UX Enhancements:**

- [ ] Dark mode support
- [ ] In-app tutorials/tooltips
- [ ] Video walkthrough (5-10 min)

**Integrations and Enterprise:**

- [ ] Webhooks for external integrations
- [ ] API key management for programmatic access
- [ ] Custom branding (Enterprise)
- [ ] Analytics dashboard (usage stats)
- [ ] Audit logging UI

**Marketing and Engagement:**

- [ ] Email drip campaign (Day 0, 2, 5, 14)
- [ ] Penetration testing
- [ ] CloudFront CDN for global distribution
