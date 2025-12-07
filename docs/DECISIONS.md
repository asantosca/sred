# BC Legal Tech - Project Decisions & Context

This document captures key strategic decisions and rationale. For implementation details and task tracking, see [ROADMAP.md](./ROADMAP.md).

## Last Updated: 2025-12-07

---

## Strategic Decisions

### Target Market
- **Approach**: Build generic, add practice-specific features later (post-MVP)
- **Rationale**: Different practice areas (real estate, family law, corporate) mainly affect templates, taxonomy, and compliance requirements - not core functionality
- **Flexibility**: Allows pivoting based on early user feedback
- **MVP Target**: Solo lawyers and small firms (1-5 users)

### Competitive Advantage
- **Primary Differentiator**: Best-in-class RAG system for legal documents
- **Focus**: Less susceptible to hallucinations than competitors
- **Why it matters**: Few existing AI legal tech solutions specialize in RAG; this is our moat

### Pricing Strategy
- **Status**: Deferred until after MVP
- **Tiers**: Starter, Professional, Enterprise (plan_tier field exists)
- **Decision point**: After beta feedback

---

## Technical Decisions

### AI/ML Stack

**Embeddings**:
- **Decision**: OpenAI text-embedding-3-small (1536 dimensions)
- **Rationale**: Proven, reliable, cost-effective for MVP
- **Future**: Evaluate Voyage AI voyage-law-2 post-MVP with real usage data

**Chat/Completions**:
- **Decision**: Claude (currently claude-3-7-sonnet-20250219)
- **Rationale**: Superior reasoning, less prone to hallucination vs GPT models
- **Note**: Anthropic does NOT offer embeddings API

**Search Strategy**:
- **Current**: Vector similarity search only (pgvector cosine similarity)
- **Beta Requirement**: Add hybrid search (vector + BM25) before beta
- **Rationale**: Lawyers search for exact terms ("Section 12.3", "Smith v. Jones") that vector search misses

### Document Processing

**Supported Formats**:
- PDF (pdfplumber) - most common legal format
- DOCX (python-docx) - drafts, templates
- TXT (charset detection) - plain text

**Beta Requirement**: Add OCR for scanned documents (many court filings are scanned)

**MVP Requirement**: Add Excel support (common in corporate/real estate law)

**Chunking Strategy**:
- **Decision**: Semantic chunking (paragraph/section boundaries)
- **NOT**: Fixed-size chunks
- **Rationale**: Better preserves legal context and meaning
- **Parameters**: MIN=100, TARGET=500, MAX=800 tokens per chunk

### Anti-Hallucination Measures

| Measure | Priority | Status |
|---------|----------|--------|
| Source citations ([Source X]) | Beta | Done |
| "I don't know" responses | Beta | Done |
| Hybrid search (exact terms) | Beta | Planned |
| OCR (scanned docs) | Beta | Planned |
| Confidence scoring | MVP | Planned |
| Re-ranking of chunks | MVP | Planned |

### Infrastructure

**Decision**: AWS-focused stack
- **Database**: PostgreSQL 15 + pgvector (RDS in production)
- **Cache/Broker**: Valkey (20-33% cheaper than Redis on ElastiCache)
- **Storage**: S3
- **IaC**: Terraform

**Rationale**: Enterprise-ready, scalable, familiar to ops teams

### Authentication

**Decision**: JWT with email/password first, OAuth later
- **Current**: JWT with refresh token rotation
- **Post-MVP**: Add Google and Microsoft OAuth together
- **Rationale**: Focus on core value prop first; most firms use Microsoft 365

### Multi-Tenancy

**Decision**: Row-level security from day 1
- **Implementation**: company_id filtering on all queries
- **Rationale**: Don't retrofit later; security-critical for legal industry

### Role-Based Access Control

**Current**: Simplified (is_admin boolean + Groups with JSON permissions)
- **Post-MVP**: Full role hierarchy (Partner, Associate, Paralegal, Guest)
- **Rationale**: Solo lawyers (MVP target) don't need complex roles

---

## Open Questions

### To Revisit Post-MVP

1. **Pricing Model**
   - Per-user pricing?
   - Storage-based?
   - API call limits?

2. **Voyage AI Embeddings**
   - Legal-specific model may improve retrieval
   - Requires schema migration (1536 -> 1024 dimensions)
   - Need usage data to benchmark improvement

3. **Practice Area Specialization**
   - Which vertical to target first?
   - Custom templates needed?
   - Practice-specific compliance?

---

## Key Principles

1. **RAG is the moat** - invest heavily in retrieval quality
2. **Lawyers verify everything** - citations and sources are non-negotiable
3. **Security-first** - legal industry requires it
4. **Start simple** - MVP with solo lawyers, expand to firms
5. **Don't over-engineer** - ship, get feedback, iterate

---

*For implementation timeline and task tracking, see [ROADMAP.md](./ROADMAP.md)*
