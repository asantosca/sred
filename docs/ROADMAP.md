# PwC SR&ED Intelligence Platform - Implementation Roadmap

## Vision

Provide PwC SR&ED consulting teams with AI-powered document analysis tools to:
- Accelerate eligibility assessments
- Generate high-quality T661 form drafts
- Reduce time spent on document review
- Improve consistency across claims

## Tech Stack

### Backend
- **Framework**: FastAPI (Python) with async support
- **Database**: PostgreSQL 15 with pgvector extension
- **ORM**: SQLAlchemy 2.0 (async)
- **Cache/Broker**: Valkey (Redis-compatible)
- **Storage**: AWS S3 (LocalStack for local dev)
- **Background Jobs**: Celery + Valkey
- **Migrations**: Alembic

### AI/ML
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Chat**: Claude claude-3-7-sonnet-20250219
- **Vector DB**: PostgreSQL + pgvector
- **Search**: Hybrid (Semantic + BM25 keyword)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **State Management**: Zustand + TanStack React Query

### Infrastructure
- **Cloud**: AWS (RDS, ElastiCache, S3, ECS)
- **IaC**: Terraform
- **Monitoring**: Sentry + CloudWatch

---

## POC Phase (Current)

_Demonstrate core value proposition to PwC_

### Core Features
- [x] JWT authentication with refresh token rotation
- [x] Document upload (PDF, DOCX, TXT)
- [x] OCR support for scanned documents
- [x] Semantic search with embeddings
- [x] Hybrid search (semantic + BM25 keyword)
- [x] Chat with RAG and source citations
- [x] Claim management with access control
- [x] Rate limiting and security headers
- [x] Usage tracking

### SR&ED-Specific Features
- [x] AI prompts tuned for SR&ED domain
- [ ] Eligibility report generation
- [x] T661 form drafting (Box 242, 244, 246 - aligned with CRA nomenclature)
- [x] Fiscal year filtering for multi-year projects (AI extracts work within claim period)
- [x] Claim date validation (fiscal year end in past, opened after FYE, within 18-month CRA deadline)
- [x] Project context fields for AI guidance (project title, objective, technology focus)
- [ ] Project timeline with R&D milestones
- [ ] Five-question test analysis

### Project Discovery & Workspace (NEW)
- [x] Automated project discovery from uploaded documents
- [x] SR&ED signal detection (uncertainty, systematic, advancement keywords)
- [x] Entity extraction (team members, project names, dates)
- [x] HDBSCAN clustering for document grouping (with fallback for missing embeddings)
- [x] Confidence scoring for discovered projects (high/medium/low)
- [x] Markdown workspace with split view (editor + chat)
- [x] AI-generated T661 narratives (Lines 242, 244, 246) per project
- [x] Summary statistics dashboard (signal strength, review status)
- [x] Status indicators (Ready for T661 / Needs Review)
- [x] Workspace chat for AI-assisted editing

### UI/UX Improvements
- [x] Consistent terminology (Claims, not Matters) throughout frontend
- [x] Document upload from claim detail page auto-selects claim
- [x] Celery worker queue configuration for document processing
- [x] Streamlined claim detail page with focused quick actions
- [x] Run Discovery button on claim page (navigates to workspace)
- [x] View Workspace button (appears after discovery run)
- [x] View Documents button with claim filtering
- [x] Removed redundant UI elements (old discovery dashboard, T661 modal, chat button)

### POC Deliverables
- [ ] Demo environment for PwC evaluation
- [ ] Sample claims with test documents
- [ ] Eligibility report examples
- [x] T661 draft examples (via workspace narratives)

---

## Beta Phase

_Pilot with select PwC SR&ED teams_

### Enhanced Analysis
- [ ] Multi-project claim support
- [ ] Expenditure tracking and categorization
- [ ] Contractor vs employee analysis
- [ ] Materials consumption tracking

### Collaboration Features
- [ ] Multi-user access per claim
- [ ] Consultant assignment and handoff
- [ ] Review and approval workflows
- [ ] Comments and annotations

### Integration
- [ ] Document versioning
- [ ] Bulk upload interface
- [ ] Export to common formats (PDF, DOCX)
- [ ] API for integration with existing tools

### Quality Improvements
- [ ] Confidence scoring on AI outputs
- [ ] Re-ranking of retrieved chunks
- [ ] Excel/spreadsheet support

---

## Production Phase

_Full rollout to PwC SR&ED practice_

### Enterprise Features
- [ ] SSO integration (Microsoft OAuth)
- [ ] Role-based access control (Partner, Manager, Analyst)
- [ ] Audit logging
- [ ] Data retention policies

### Advanced AI
- [ ] Query decomposition for complex questions
- [ ] Iterative retrieval for research queries
- [ ] Cross-claim pattern analysis
- [ ] Similar project identification

### Reporting
- [ ] Claim status dashboard
- [ ] Team productivity metrics
- [ ] Billing time tracking
- [ ] Client reporting

### Scale
- [ ] Multi-region deployment
- [ ] Performance optimization
- [ ] Load testing (100+ concurrent users)

---

## Document Types

### Supported for POC
| Type | Extension | Use Case |
|------|-----------|----------|
| PDF | .pdf | Technical reports, formal documentation (up to 500MB) |
| Word | .docx | Project plans, meeting notes |
| Text | .txt | Plain text documents |
| Images | .png, .jpg, .tiff | Scanned lab notebooks, diagrams (with OCR) |

### Planned for Beta
| Type | Extension | Use Case |
|------|-----------|----------|
| Excel | .xlsx | Timesheets, financial data |
| PowerPoint | .pptx | Project presentations |

---

## SR&ED Document Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `project_plan` | Technical project documentation | Project proposals, technical specifications |
| `timesheet` | Labor hour records | Weekly timesheets, resource allocation |
| `email` | Email communications | Project updates, technical discussions |
| `financial` | Financial records | Budgets, expense reports |
| `technical_report` | Technical/scientific reports | Test results, analysis documents |
| `lab_notebook` | R&D notes | Experiment logs, design iterations |
| `invoice` | Contractor invoices | Third-party R&D costs |

---

## Success Metrics

### POC Phase
- Demo completed with positive feedback
- 3+ sample claims processed successfully
- Eligibility reports meet PwC quality standards
- T661 drafts require <50% revision

### Beta Phase
- 5+ PwC teams actively using platform
- 80% of users rate experience as "good" or "excellent"
- 30% reduction in claim preparation time
- <5% error rate in AI-generated content

### Production Phase
- 50+ claims processed per month
- 99.9% uptime
- <2 second average response time
- NPS score >40
