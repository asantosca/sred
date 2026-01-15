# PwC SR&ED Intelligence Platform - Project Decisions & Context

This document captures key strategic decisions and rationale. For implementation details and task tracking, see [ROADMAP.md](./ROADMAP.md).

## Last Updated: 2025-01-14

---

## Strategic Decisions

### Target Market
- **Primary Client**: PwC SR&ED consulting practice
- **Users**: SR&ED consultants (teams of up to 10)
- **POC Focus**: Demonstrate value with document analysis and T661 drafting

### Competitive Advantage
- **Primary Differentiator**: Best-in-class RAG system for SR&ED documents
- **Focus**: Accurate eligibility analysis with clear source citations
- **Why it matters**: Reduces time on document review, improves consistency

### Product Positioning
- **Not a replacement** for consultant expertise
- **Augmentation tool** that accelerates analysis and drafting
- **Quality focus** over speed - accuracy is paramount for tax credits

---

## Technical Decisions

### AI/ML Stack

**Embeddings**:
- **Decision**: OpenAI text-embedding-3-small (1536 dimensions)
- **Rationale**: Proven, reliable, cost-effective
- **Future**: Evaluate domain-specific models if needed

**Chat/Completions**:
- **Decision**: Claude (claude-3-7-sonnet)
- **Rationale**: Superior reasoning, better at following complex instructions
- **Key feature**: Epistemic honesty - clearly distinguishes sources

**Search Strategy**:
- **Decision**: Hybrid search (vector + BM25)
- **Rationale**: Consultants search for exact terms ("Phase 2 testing", "Q3 2024")
- **Implementation**: PostgreSQL tsvector + GIN index with RRF score fusion

### Document Processing

**Supported Formats**:
- PDF (pdfplumber) - most common for technical reports
- DOCX (python-docx) - project plans, meeting notes
- TXT (charset detection) - plain text

**OCR Support**: AWS Textract (production) with Tesseract fallback (local dev)

**Chunking Strategy**:
- **Decision**: Semantic chunking (paragraph/section boundaries)
- **Parameters**: MIN=100, TARGET=500, MAX=800 tokens per chunk
- **Rationale**: Preserves context for technical documentation

### SR&ED-Specific Decisions

**Eligibility Analysis**:
- Use five-question test framework from CRA
- Score each criterion (STRONG/MODERATE/WEAK/INSUFFICIENT)
- Always cite specific document sources

**T661 Form Drafting**:
- Generate drafts for Parts 3, 4, 5, 6 (the narrative sections)
- Include source citations in brackets
- Flag areas needing consultant review

**Document Categories**:
- Map to SR&ED expenditure types
- Track project association
- Support fiscal year filtering

### Infrastructure

**Decision**: AWS-focused stack
- **Database**: PostgreSQL 15 + pgvector (RDS in production)
- **Cache/Broker**: Valkey (Redis-compatible)
- **Storage**: S3
- **IaC**: Terraform

### Authentication

**Decision**: JWT with email/password for POC
- **Current**: JWT with refresh token rotation
- **Future**: Microsoft OAuth for PwC integration
- **Rationale**: Simple for POC, enterprise-ready path

### Multi-Tenancy

**Decision**: Row-level security from day 1
- **Implementation**: company_id filtering on all queries
- **Rationale**: Each PwC client is isolated, critical for confidentiality

---

## Open Questions

### To Revisit Post-POC

1. **PwC Integration**
   - SSO requirements?
   - Existing tool integrations?
   - Data retention policies?

2. **Scaling**
   - Expected claim volume?
   - Concurrent user expectations?
   - Geographic distribution?

3. **Advanced Features**
   - Multi-project claims?
   - Expenditure calculations?
   - CRA filing integration?

---

## Key Principles

1. **Accuracy over speed** - Tax credits require precision
2. **Source transparency** - Always cite where information comes from
3. **Consultant augmentation** - Tool assists, doesn't replace expertise
4. **Security-first** - Client data confidentiality is paramount
5. **Start simple** - POC with core value, expand based on feedback

---

*For implementation timeline and task tracking, see [ROADMAP.md](./ROADMAP.md)*
