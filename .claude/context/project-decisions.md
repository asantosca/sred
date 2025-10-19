# BC Legal Tech - Project Decisions & Context

This document captures key decisions, rationale, and context from project discussions.

## Last Updated: 2025-10-19

---

## Strategic Decisions

### Target Market
- **Approach**: Build generic, add practice-specific features later (Milestone 6)
- **Rationale**: Different practice areas (real estate, family law, corporate) mainly affect templates, taxonomy, and compliance requirements - not core functionality
- **Flexibility**: Allows pivoting based on early user feedback

### Competitive Advantage
- **Primary Differentiator**: Best-in-class RAG system for legal documents
- **Focus**: Less susceptible to hallucinations than competitors
- **Why it matters**: Few existing AI legal tech solutions specialize in RAG; this is our moat

### Pricing Strategy
- **Status**: Deferred until after structure is complete
- **Tiers exist**: Starter, Professional, Enterprise
- **Decision point**: After Milestone 5 (MVP complete)

---

## Technical Decisions

### AI/ML Stack

**Embeddings**:
- **Primary Recommendation**: Voyage AI voyage-law-2 (1024 dimensions)
  - Legal-specific training on legal corpus
  - Optimized for legal document retrieval
- **Alternative**: OpenAI text-embedding-3-large (3072 dimensions)
  - Proven, highly accurate
  - Industry standard
- **Current Schema**: Hardcoded to 1536 dimensions (needs update in Milestone 3)

**Chat/Completions**:
- **Choice**: Claude 3.5 Sonnet
- **Rationale**: Superior reasoning, less prone to hallucination vs GPT models
- **Note**: Anthropic Claude does NOT offer embeddings API (as of Jan 2025)

**Search Strategy**:
- **Approach**: Hybrid search (vector similarity + keyword/BM25)
- **Why**: Combines semantic understanding with exact term matching
- **Critical for legal**: Lawyers often search for specific terms, statutes, case names

### Document Processing

**Supported Formats**:
1. PDF (most common legal format)
2. Word/DOCX (drafts, templates)
3. Text files
4. Excel/spreadsheets (special handling needed - preserve table structure)
5. Scanned images (requires OCR)

**Excel Handling**:
- **Question**: Do lawyers query spreadsheet *data* or just need to find them?
- **Approach**: Extract as tables with structure preserved
- **Implementation**: Milestone 3

**Chunking Strategy**:
- **Method**: Semantic chunking (paragraph/section boundaries)
- **NOT**: Fixed-size chunks
- **Why**: Better preserves legal context and meaning

### Anti-Hallucination Measures

**Critical for Legal Industry** - lawyers must verify everything:

1. **Always cite sources** with document name and page number
2. **Confidence scoring** for all responses
3. **"I don't know" responses** when confidence is low or no relevant docs
4. **Show retrieved chunks** vs. generated answer for verification
5. **Clickable links** to jump to source document
6. **Re-ranking** of retrieved chunks for relevance
7. **Hybrid search** prevents missing exact term matches

### Infrastructure

**Cloud Provider**: AWS
- **Storage**: S3 for documents
- **Database**: RDS PostgreSQL with PGvector
- **Cache**: ElastiCache Redis
- **IaC**: Terraform

**Local Development**:
- Docker Compose working ✅
- LocalStack for S3
- PostgreSQL with PGvector
- Redis

---

## Feature Prioritization Decisions

### OAuth Authentication
- **Decision**: Move to Milestone 6 (Advanced Features)
- **Original consideration**: Add Google OAuth in Milestone 1
- **Rationale**:
  - Avoid distraction from core MVP
  - Ship faster with email/password auth
  - Add OAuth after product validation
  - Will implement both Google AND Microsoft OAuth together
  - Can make data-driven decision based on early user feedback (Google Workspace vs Office 365)
- **Benefits of waiting**:
  - Focus on core value prop (document AI + chat)
  - Validate product-market fit first
  - Auth infrastructure will be stable by then

### Development Approach
- **Starting Point**: Milestone 1, Task 1 (JWT middleware)
- **Priority**: Complete Milestones 1-5 for MVP
- **Timeline**: 2-3 months for MVP, 6-9 months for full launch

---

## Product Vision Insights

### User Types

**Scenario 1: Solo Lawyer**
- Same person = tenant + admin + user
- Simplest case
- Target for MVP

**Scenario 2: Multi-User Firm**
- 1 tenant (law firm)
- 1+ administrators
- Multiple users with different roles
- Requires full user management

### Role Hierarchy (Matches Law Firm Structure)
1. Administrators - Full access
2. Partners - High-level access
3. Associates - Standard access
4. Paralegals - Limited access
5. Guests - Read-only

---

## Open Questions / Future Considerations

### To Revisit Later

1. **Pricing Strategy** (post-Milestone 5)
   - Per-user pricing?
   - Storage-based?
   - API call limits?

2. **Practice Area Specialization** (Milestone 6+)
   - Which vertical to target first?
   - Custom templates needed?
   - Practice-specific compliance?

3. **Excel/Spreadsheet Querying** (Milestone 3)
   - Full data extraction vs. just finding files?
   - Table structure preservation approach?

4. **Embedding Model Final Choice** (Before Milestone 3)
   - Test Voyage AI voyage-law-2 vs OpenAI
   - Cost vs. accuracy tradeoff
   - Legal-specific performance benchmark

---

## Success Metrics

### MVP (Post-Milestone 5)
- 10 solo lawyers using the platform
- Core features: auth, documents, basic RAG, chat

### Launch (Post-Milestone 9)
- 50 firms with 500+ total users
- Full feature set including billing, analytics

### Scale (Future)
- 1000+ firms with 10,000+ users
- Multi-region, high availability

---

## Notes for Future Development

- **RAG is the moat** - invest heavily in quality here
- **Lawyers verify everything** - citations and sources are non-negotiable
- **Multi-tenancy from day 1** - don't retrofit later
- **AWS-focused** - leverage AWS services where possible
- **Security-first** - legal industry requires it
- **Start simple** - MVP with solo lawyers, expand to firms

---

*This document should be updated as new strategic decisions are made.*
