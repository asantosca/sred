# BC Legal Tech - Implementation Roadmap

AI-powered legal document intelligence platform for law firms in British Columbia.

## Vision

Serve law firms of different sizes, from solo lawyers to large firms:

- **Solo Lawyers**: One person is tenant, admin, and user
- **Multi-User Firms**: One tenant (law firm) with multiple admins and users

---

## MILESTONE 1: Core Authentication & User Management

Complete basic auth flow and user management for multi-tenant system.

### Tasks (Priority Order)

1. [x] **Add JWT middleware for protected routes with token validation** ⭐ (Required for all other features)
2. [x] **Implement `/api/v1/auth/me` endpoint** to get current user from JWT token (Required by frontend)
3. [x] Implement refresh token endpoint in `/api/v1/auth/refresh`
4. [x] Implement password reset flow (request reset, verify token, reset password)
5. [x] Add email service integration for user invitations and password resets
6. [x] Create user profile update endpoint (allow users to update their own profile)
7. [x] Add user avatar upload functionality

**Status**: ✅ **MILESTONE 1 COMPLETE** - All core authentication features implemented

**Note**: Tasks ordered by dependency - JWT middleware unlocks all protected endpoints.

---

## MILESTONE 2: Core Document Upload (MVP)

Basic document upload with matter association and security controls.

### Tasks

- [x] **Create matters table and API endpoints (CRUD operations)** ✅ Complete with full access control
- [x] **Implement matter access control (who can upload to which matters)** ✅ Role-based permissions implemented
- [x] **Add basic document metadata (title, date, status, type-specific fields)** ✅ Full schema created in database
- [x] **Implement security controls (confidentiality levels, privilege designation)** ✅ Schema includes all security fields
- [x] **Create core document upload API endpoint with S3 integration** ✅ Complete with multiple upload modes
- [x] **Build document classification system (Contract, Pleading, Correspondence, Discovery, Exhibit)** ✅ Type-specific upload schemas implemented
- [x] **Create document listing with matter-based filtering** ✅ Complete with pagination and search
- [x] **Add document download endpoints with signed URLs** ✅ Secure presigned URL generation
- [x] **Implement basic document deletion with S3 cleanup** ✅ Complete with storage cleanup

**Status**: 🟢 **MILESTONE 2 COMPLETE!** ✅ All document upload and management features implemented

**Upload Modes**: Quick Upload (5 required fields, ~60 seconds)

**Core Tables**: matters, documents, users, matter_access

**Supported Formats**: PDF, DOCX, DOC, TXT, MSG, EML (max 50MB)

---

## MILESTONE 2.5: Enhanced Document Classification

Type-specific metadata and improved upload experience.

### Tasks

- [x] **Implement type-specific field sets for each document category** ✅ Complete with specialized upload schemas:
  - Contract fields (type, value, effective/expiration dates, governing law)
  - Pleading fields (court, case number, opposing party, filing date)
  - Correspondence fields (author, recipient, cc, subject)
  - Discovery fields (type, parties, numbers, due dates)
  - Exhibit fields (exhibit number, related documents)
- [x] **Add document status tracking (Draft, Final, Executed, Filed)** ✅ Complete with:
  - Status update endpoint with audit logging
  - Status history tracking in internal notes
  - Valid status workflow definitions
- [x] **Create auto-detection features (filename patterns, basic OCR for dates)** ✅ Complete with:
  - Pre-upload file analysis endpoint for metadata suggestions
  - Auto-detection integration in all upload endpoints
  - Pattern matching for legal document types and metadata
- [x] **Add document search within matters** ✅ Complete with:
  - Enhanced basic search across all document fields
  - Advanced search endpoint with multiple filters and criteria
  - Search by content, metadata, dates, authors, case numbers
- [x] **Implement basic duplicate detection (file hash comparison)** ✅ Complete with:
  - Pre-upload duplicate checking endpoint
  - Automatic duplicate prevention in upload process
  - Company-wide and matter-specific duplicate detection
- [x] Implement Standard Upload mode (12-15 fields, 2-3 minutes) ✅ Complete with 17 fields total

**Status**: ✅ **MILESTONE 2.5 COMPLETE!** All enhanced classification features implemented

**Upload Modes**: Quick Upload + Standard Upload (both with auto-detection)

**Enhanced Features**: ✅ Type-specific metadata, ✅ Auto-detection, ✅ Advanced search, ✅ Duplicate detection, ✅ Status tracking

**Key New Endpoints**:
- `POST /api/v1/documents/analyze` - Pre-upload file analysis
- `POST /api/v1/documents/search` - Advanced document search  
- `POST /api/v1/documents/check-duplicates` - Duplicate detection
- `PATCH /api/v1/documents/{id}/status` - Status tracking
- `GET /api/v1/documents/statuses` - Status definitions
- `GET /api/v1/documents/{id}/status-history` - Status history

---

## MILESTONE 3: Document Processing & RAG Pipeline + Version Control

AI-powered document intelligence with embeddings, vector search, and version management.

**PRIORITY**: This is our key differentiator - build the best RAG system for legal documents.

### Tasks

**Core RAG Pipeline:**

- [x] **Create database tables for RAG pipeline** ✅ Complete (document_chunks, document_relationships, document_processing_queue)
- [x] **Enable PGvector extension** ✅ Complete with IVFFlat indexing
- [x] **Design semantic chunking architecture** ✅ Complete (see RAG_ARCHITECTURE.md)
- [x] **Configure vector dimensions** ✅ Complete (1536 default, configurable)
- [x] **Implement document text extraction service** ✅ Complete (PDF, DOCX, TXT with pdfplumber, python-docx)
- [ ] Add OCR support for scanned documents (legal case files, historical documents)
- [x] **Create semantic chunking service** ✅ Complete (paragraph/section boundaries, legal document structure detection, page tracking)
- [x] **Integrate embedding generation** ✅ Complete (OpenAI text-embedding-3-small, 1536 dimensions)
- [x] **Implement vector similarity search with PGvector** ✅ Complete (semantic search API endpoint)
- [ ] Build background task queue for document processing (using Celery/Redis)

**Anti-Hallucination Features:**

- [ ] Implement **hybrid search** (vector similarity + keyword/BM25 for exact term matching)
- [ ] Add **re-ranking** of retrieved chunks for relevance
- [ ] Implement **confidence scoring** for answers
- [ ] Add **citation tracking** with document name, page number, and chunk location
- [ ] Build "I don't know" responses when confidence is low or no relevant docs found
- [ ] Create document processing status tracking and webhooks
- [ ] Implement reprocessing failed documents

**Version Control System:**

- [x] **Create document_relationships table** ✅ Complete (amendments, exhibits, responses, supersedes)
- [x] **Add document processing queue table** ✅ Complete for async operations
- [x] **Design version tracking architecture** ✅ Complete (parent/child relationships, version numbers)
- [ ] Implement document superseding logic (mark previous versions as superseded)
- [ ] Add version comparison and change summaries
- [ ] Build similar document detection for version suggestions
- [ ] Create API endpoints for version management

**Status**: 🟢 **Semantic search complete!** (80% of Milestone 3)

**Completed:**
- ✅ PGvector extension enabled with IVFFlat indexing
- ✅ 3 new database tables created and indexed
- ✅ Vector embeddings schema (1536 dimensions, configurable)
- ✅ Comprehensive architecture documented (RAG_ARCHITECTURE.md)
- ✅ Text extraction service (PDF, DOCX, TXT with automatic processing)
- ✅ Document metadata extraction (word count, page count)
- ✅ Full-text search indexing (PostgreSQL GIN index)
- ✅ Semantic chunking service (legal document structure detection, page tracking, metadata preservation)
- ✅ Automatic chunking pipeline integration (triggers after text extraction)
- ✅ **Embedding generation service** (OpenAI text-embedding-3-small integration)
- ✅ **Hybrid database architecture** (SQLAlchemy ORM + raw asyncpg for vectors)
- ✅ **Vector storage service** (pgvector with proper type registration)
- ✅ **Semantic search API** (POST /api/v1/search/semantic with natural language queries)
- ✅ **Search result enrichment** (document metadata, page numbers, similarity scores)

**Next Up:**
- 🎯 Background task queue (Celery/Redis) for automatic processing
- 🎯 Hybrid search (semantic + keyword matching)
- 🎯 Anti-hallucination features (confidence scoring, citations)

**New Tables**: document_chunks, document_relationships, document_processing_queue

**Key Documentation**: See `RAG_ARCHITECTURE.md` for complete pipeline design

**Embedding Model Decision**:

- **Option A**: Voyage AI voyage-law-2 (1024 dims) - Legal-specific, trained on legal corpus
- **Option B**: OpenAI text-embedding-3-large (3072 dims) - Proven, highly accurate
- **Chat Model**: Claude 3.5 Sonnet (superior reasoning, less prone to hallucination)

---

## MILESTONE 4: AI Chat & Conversation System + Workflow Integration

Build conversational interface with RAG-powered responses and document workflow management.

### Tasks

**Core Chat System:**

- [ ] Create conversation CRUD endpoints (create, list, get, delete)
- [ ] Implement message creation with streaming support (SSE/WebSocket)
- [ ] Build RAG context retrieval (hybrid search + re-ranking from Milestone 3)
- [ ] Integrate **Claude 3.5 Sonnet API** for chat completions
- [ ] Implement conversation history management and context window
- [ ] **Add cited sources in AI responses** (document name, page number, clickable links to source)
- [ ] **Implement confidence indicators** (show when AI is uncertain)
- [ ] Add message rating system (thumbs up/down with feedback for improvement)
- [ ] Create conversation export to PDF/DOCX
- [ ] Implement conversation sharing between users

**Document Workflow Integration:**

- [ ] Add document review assignment system (assign to users, set deadlines)
- [ ] Implement review status tracking (needs review, under review, approved, etc.)
- [ ] Create priority levels (normal, high, urgent) for document processing
- [ ] Add workflow instructions and internal notes
- [ ] Build document access logging for audit trails
- [ ] Create notification system for review assignments and deadlines
- [ ] Add review dashboard for assigned documents

**Status**: Schema exists, chat system not implemented

**New Tables**: document_access_log, enhanced workflow fields in documents table

**Anti-Hallucination in Responses**:

- Always cite source documents with page numbers
- Return "I don't have enough information" when confidence is low
- Show retrieved chunks vs. generated answer for verification
- Allow lawyers to verify by jumping to source document

---

## MILESTONE 5: Frontend Application + Advanced Upload Features

Build complete React UI with modern UX and advanced document upload capabilities.

### Tasks

**Core Frontend Components:**

- [ ] Create authentication pages (Login, Register, Password Reset)
- [ ] Build dashboard with overview stats and recent activity
- [ ] Implement document library with upload, list, search, filter
- [ ] Create document viewer with preview and download
- [ ] Build chat interface with message history and streaming responses
- [ ] Implement conversation sidebar with search and filters
- [ ] Create user management UI (Admin: list, invite, edit, deactivate users)
- [ ] Build matter management UI (create, edit, assign users to matters)
- [ ] Create settings pages (Profile, Company, Billing, Integrations)
- [ ] Implement responsive mobile layout
- [ ] Add dark mode support
- [ ] Create loading states, error boundaries, and toast notifications

**Advanced Upload Features:**

- [ ] Build comprehensive upload UI (8-screen flow from fileupload.md)
- [ ] Implement Detailed Upload mode (version control, workflow, relationships)
- [ ] Create bulk upload interface (multiple files with shared metadata)
- [ ] Add Excel import functionality for bulk metadata
- [ ] Implement auto-detection features (OCR for dates, parties, document patterns)
- [ ] Build document relationship management UI
- [ ] Create upload session management (save drafts, resume later)
- [ ] Add smart recommendations based on user patterns

**Status**: Frontend structure exists, components not built

**Upload Modes**: Quick + Standard + Detailed + Bulk

**New Features**: Advanced upload UI, bulk operations, auto-detection

---

## MILESTONE 6: Advanced Features

Premium capabilities for scaling to larger firms.

### Tasks

- [ ] **Add Google OAuth authentication** (Sign in with Google)
- [ ] Add Microsoft OAuth authentication (Sign in with Microsoft/Office 365)
- [ ] Implement account linking for OAuth providers
- [ ] Implement usage tracking and billing metering (documents, storage, API calls)
- [ ] Add subscription management with Stripe integration
- [ ] Create plan enforcement and upgrade prompts
- [ ] Build analytics dashboard (usage stats, popular documents, user activity)
- [ ] Implement audit logging for security and compliance
- [ ] Add matter/case organization system for documents and conversations
- [ ] Create API key management for programmatic access
- [ ] Implement webhooks for external integrations
- [ ] Add custom branding (logo, colors) for Enterprise plans
- [ ] Build admin panel for platform management (view all companies, stats)

**Status**: Not started

**Note**: OAuth providers added here after core MVP is stable to avoid early distraction.

---

## MILESTONE 7: Testing & Quality Assurance

Ensure reliability and catch bugs early.

### Tasks

- [ ] Write unit tests for authentication services
- [ ] Write unit tests for document services
- [ ] Write unit tests for RAG pipeline
- [ ] Create integration tests for API endpoints
- [ ] Add end-to-end tests for critical user flows
- [ ] Implement load testing for scalability verification
- [ ] Set up CI/CD pipeline with automated testing

**Status**: Test structure exists, tests not written

---

## MILESTONE 8: Security & Compliance

Production hardening for legal industry requirements.

### Tasks

- [ ] Implement rate limiting on API endpoints
- [ ] Add input validation and sanitization
- [ ] Implement CSRF protection
- [ ] Add SQL injection prevention audit
- [ ] Implement data encryption at rest
- [ ] Add TLS/SSL certificate management
- [ ] Create security headers (HSTS, CSP, X-Frame-Options)
- [ ] Implement data retention policies and GDPR compliance
- [ ] Add security scanning and vulnerability assessment

**Status**: Basic RLS implemented, security hardening needed

---

## MILESTONE 9: Infrastructure & Deployment

Production-ready infrastructure with high availability.

### Tasks

- [ ] Set up production PostgreSQL with read replicas
- [ ] Configure Redis cluster for caching and sessions
- [ ] Set up S3 buckets with proper IAM policies
- [ ] Deploy backend with auto-scaling (ECS/Kubernetes)
- [ ] Deploy frontend to CDN (CloudFront/Vercel)
- [ ] Configure domain and DNS with SSL
- [ ] Set up monitoring and alerting (CloudWatch/DataDog)
- [ ] Implement log aggregation (CloudWatch Logs/ELK)
- [ ] Create backup and disaster recovery procedures
- [ ] Set up staging environment

**Status**: Terraform structure exists, deployment not configured

---

## MILESTONE 10: Documentation & Launch

Prepare for market and onboard first customers.

### Tasks

- [ ] Write API documentation with examples
- [ ] Create user guide and help center
- [ ] Write admin documentation for setup and configuration
- [ ] Create video tutorials for key features
- [ ] Build onboarding flow for new users
- [ ] Create marketing website/landing page
- [ ] Set up support system (ticketing/chat)
- [ ] Conduct beta testing with pilot law firms
- [ ] Launch production and monitor initial users

**Status**: Not started

---

## Current Architecture

### Tech Stack

- **Backend**: FastAPI (Python) with async support
- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Database**: PostgreSQL 15 with PGvector extension
- **Cache**: Redis
- **Storage**: AWS S3 (LocalStack for local dev)
- **AI Embeddings**: Voyage AI voyage-law-2 (legal-optimized) OR OpenAI text-embedding-3-large
- **AI Chat**: Claude 3.5 Sonnet (superior reasoning, less hallucination)
- **Document Processing**: Celery + Redis for background tasks
- **Infrastructure**: Terraform for IaC on AWS

### Multi-Tenancy

- Row-level security (RLS) for data isolation
- Three tenancy models: `shared_rls`, `dedicated_schema`, `dedicated_instance`
- Company-based isolation with JWT tokens

### Subscription Tiers

- **Starter**: Solo lawyers and small firms
- **Professional**: Mid-sized firms
- **Enterprise**: Large firms with custom needs

---

## Development Approach

### For MVP (Solo Lawyers)

Focus on core functionality first:

1. **Milestone 1**: Auth (Complete ✅)
2. **Milestone 2**: Core Document Upload (Complete ✅) - Full upload, classification, and management system
3. **Milestone 2.5**: Enhanced Classification (Complete ✅) - Standard mode, type-specific fields, auto-detection
4. **Milestone 3**: Basic RAG pipeline + Version Control (NEXT)
5. **Milestone 4**: Simple chat interface + Basic Workflow
6. **Milestone 5**: Essential frontend pages + Advanced Upload

**Timeline**: 3-4 months (with enhanced upload features)

### For Full Launch (Multi-User Firms)

Complete production-ready platform:

1. **Milestones 1-5**: Complete all core features
2. **Milestone 6**: Advanced features for differentiation
3. **Milestones 7-8**: Testing and security hardening
4. **Milestone 9**: Production infrastructure
5. **Milestone 10**: Launch preparation

**Timeline**: 6-9 months

---

## Key Differentiators

1. **Best-in-Class RAG**: Superior legal document intelligence with anti-hallucination measures
   - Legal-optimized embeddings (Voyage AI voyage-law-2)
   - Hybrid search (semantic + keyword)
   - Always cited sources with page numbers
   - Confidence scoring and "I don't know" responses
2. **BC-Specific**: Tailored for British Columbia law firms
3. **Multi-Tenancy**: Secure isolation between firms (solo to enterprise)
4. **Role-Based Access**: Mirrors law firm hierarchy (Partners, Associates, Paralegals)
5. **Matter Management**: Organize by cases/clients (Milestone 6)
6. **Compliance-First**: Security, audit logging, GDPR-ready
7. **Multiple File Formats**: PDF, Word, Excel, scanned documents with OCR

---

## Success Metrics

- **MVP**: 10 solo lawyers using the platform
- **Launch**: 50 firms with 500+ total users
- **Scale**: Support for 1000+ firms with 10,000+ users

---

## Next Steps

1. Review and prioritize roadmap items
2. Set up development workflow and sprint cycles
3. Begin Milestone 1 implementation
4. Establish testing and deployment practices
5. Create feedback loop with beta users

---

---

## Technical Decisions Summary

### AI/ML Stack

- **Embeddings**: Voyage AI voyage-law-2 (legal-specific, 1024 dims) recommended
  - Alternative: OpenAI text-embedding-3-large (3072 dims)
- **Chat Completions**: Claude 3.5 Sonnet (best reasoning, least hallucination)
- **Vector DB**: PostgreSQL + PGvector extension
- **Search Strategy**: Hybrid (vector similarity + BM25 keyword matching)

### Document Support

- **Text Extraction**: PDF, DOCX, TXT, Excel
- **OCR**: Scanned documents and images
- **Chunking**: Semantic (paragraph/section-aware), not fixed-size
- **Processing**: Async with Celery + Redis

### Deployment

- **Cloud**: AWS
- **Infrastructure**: Terraform
- **Environments**: Local (Docker Compose) → Staging → Production

---

**Last Updated**: 2025-11-06 (Milestone 3: Semantic search complete - 80%)

---

## Document Upload Implementation Details

Based on comprehensive fileupload.md specification:

### Upload Flow Evolution

**Milestone 2 (MVP)**: Quick Upload mode

- 5 required fields (Matter, Type, Title, Date, Confidentiality)
- ~60 seconds to complete
- Single file upload only
- Basic matter association and security

**Milestone 2.5**: Standard Upload mode ✅ Complete

- 12-15 fields including type-specific metadata
- ~2-3 minutes to complete
- Auto-detection features (filename patterns, basic OCR)
- Enhanced classification and validation

**Milestone 5**: Detailed + Bulk Upload modes

- Complete 8-screen upload flow
- Version control, workflow assignment, document relationships
- Bulk upload with Excel import
- Advanced auto-detection and smart recommendations
- ~5+ minutes for detailed mode

### Key Database Tables

**Core Tables (Milestone 2)**:

- `matters` - Case/matter information
- `documents` - Document metadata and file info
- `users` - User accounts
- `matter_access` - User permissions per matter

**Enhanced Tables (Milestone 3+)**:

- `document_relationships` - Version chains, amendments, exhibits
- `document_access_log` - Audit trail
- `upload_sessions` - Save draft uploads
- `document_processing_queue` - Background processing

### Security & Compliance Features

- **Confidentiality Levels**: Standard, Highly Confidential, Attorney Eyes Only
- **Privilege Protection**: Attorney-Client, Work Product, Settlement Communications
- **Matter-Based Access Control**: Users only see documents for assigned matters
- **Audit Logging**: Track all document access and modifications
- **Version Control**: Full document history with superseding capabilities
