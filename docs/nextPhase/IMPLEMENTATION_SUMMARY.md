# SR&ED Project Discovery System - Implementation Summary

## What You're Building

Transform your existing SR&ED RAG platform into an **interactive project discovery system** that automatically:

1. **Identifies potential SR&ED projects** from unorganized documents
2. **Tags documents** to projects with confidence scores
3. **Handles incremental uploads** intelligently
4. **Provides interactive refinement** via dashboard + chat

## What You Already Have (Excellent Foundation!)

✅ **Document processing pipeline** - Text extraction, OCR, chunking
✅ **Vector search** - pgvector with hybrid search (semantic + BM25)  
✅ **RAG chat** - Claude-based with streaming and citations
✅ **Claims organization** - Fiscal year tracking, T661 drafting
✅ **Multi-tenancy** - Row-level security via company_id
✅ **Background jobs** - Celery for async processing
✅ **Rich metadata** - 50+ fields on documents

**Overall: ~75% complete already!**

## What's Missing (The 25%)

❌ **Project model** - Sub-organization within Claims
❌ **Document tagging** - Many-to-many relationship
❌ **SR&ED signal detection** - Keyword/NER analysis
❌ **Auto-clustering** - ML-based project discovery
❌ **Interactive UI** - Project dashboard + refinement
❌ **Change detection** - Handle incremental uploads

---

## Implementation Plan: 4 Phases

### Phase 1: Database Schema (Week 1)
**What:** Add Project model, tagging system, discovery tracking

**Files to modify:**
- Create migration: `backend/alembic/versions/xxx_add_projects.py`
- Update models: `backend/app/models/models.py`
- Create schemas: `backend/app/schemas/project.py`

**New tables:**
- `projects` - Project records with SR&ED scores
- `document_project_tags` - Many-to-many document ↔ project
- `project_discovery_runs` - Track discovery executions
- `document_upload_batches` - Track incremental uploads

**Extend existing tables:**
- `documents` - Add sred_signals, temporal_metadata columns
- `document_chunks` - Add sred_keyword_matches column

**See:** `phase1_database_changes.md` (already created)

---

### Phase 2: SR&ED Signal Detection (Week 1-2)
**What:** Detect eligibility signals during document processing

**New services:**
- `backend/app/services/sred_signal_detector.py`
  - Keyword taxonomy (uncertainty, systematic, failure, advancement)
  - Scoring algorithm
  - Batch processing

- `backend/app/services/entity_extractor.py`
  - spaCy NER for people, orgs, dates
  - Project name extraction (Jira codes, feature names)
  - Technical term extraction

**Modify existing:**
- `backend/app/services/document_processor.py`
  - Add signal detection step after text extraction
  - Add entity extraction
  - Store in document.sred_signals, document.temporal_metadata

**Dependencies to add:**
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

**See:** `phase2_sred_signal_detection.md` (already created)

---

### Phase 3: Project Discovery Algorithm (Week 2-3)
**What:** Automatically cluster documents into projects

**New service:**
- `backend/app/services/project_discovery_service.py`
  - Multi-dimensional clustering (temporal + semantic + team)
  - HDBSCAN for variable cluster sizes
  - SR&ED confidence scoring
  - AI-generated project names and summaries

**Algorithm:**
1. Fetch all documents for claim
2. Extract features: temporal (dates), semantic (embeddings), team (people)
3. Cluster using HDBSCAN
4. Analyze each cluster (aggregate signals, generate summary)
5. Score and categorize (high/medium/low confidence)
6. Save projects and create document tags

**Dependencies:**
```bash
pip install scikit-learn hdbscan
```

**See:** `phase3_4_discovery_and_api.md` (already created)

---

### Phase 4: API Endpoints (Week 3)
**What:** Expose discovery and project management via FastAPI

**New endpoints:**
- `POST /api/v1/projects/discover` - Run discovery
- `GET /api/v1/projects/claim/{claim_id}` - List projects
- `GET /api/v1/projects/{project_id}` - Get project details
- `PATCH /api/v1/projects/{project_id}` - Update project
- `POST /api/v1/projects/{project_id}/approve` - Approve project
- `POST /api/v1/projects/{project_id}/reject` - Reject project
- `POST /api/v1/projects/{project_id}/documents/add` - Add docs
- `DELETE /api/v1/projects/{project_id}/documents/{doc_id}` - Remove doc
- `GET /api/v1/projects/{project_id}/documents` - List project docs

**New files:**
- `backend/app/api/v1/endpoints/projects.py`
- `backend/app/schemas/project.py`

**See:** `phase3_4_discovery_and_api.md` (already created)

---

### Phase 5: Frontend Dashboard (Week 4)
**What:** Build interactive project discovery UI

**New React components:**

```
frontend/src/pages/
  ProjectDiscovery.tsx          # Main dashboard
  ProjectDetail.tsx             # Single project view
  
frontend/src/components/projects/
  ProjectCard.tsx               # Project summary card
  ProjectList.tsx               # List with filters
  DocumentAssignment.tsx        # Drag-drop doc assignment
  DiscoveryProgress.tsx         # Real-time progress
  NewDocumentsAlert.tsx         # Change detection UI
```

**Key features:**
- Auto-discovery on claim creation
- Project cards grouped by confidence
- Click to approve/reject/review
- Document browser with tagging
- Chat integration for questions
- Change detection alerts

**API integration:**
```typescript
// Trigger discovery
const { data } = await api.post(`/projects/discover`, { claim_id })

// List projects
const { projects } = await api.get(`/projects/claim/${claimId}`)

// Approve project
await api.post(`/projects/${projectId}/approve`)
```

---

## Specific Action Items for Claude Code

### Step 1: Database Setup
```bash
cd backend

# Create migration
alembic revision -m "add_project_discovery_system"

# Copy SQL from phase1_database_changes.md into migration file
# Then run:
alembic upgrade head

# Verify tables created
psql $DATABASE_URL -c "\dt projects*"
```

### Step 2: Install Dependencies
```bash
# Backend
pip install spacy scikit-learn hdbscan
python -m spacy download en_core_web_sm

# Verify
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✓')"
```

### Step 3: Create Services
```bash
# Copy implementations from phase2 and phase3 documents

# Create files:
touch backend/app/services/sred_signal_detector.py
touch backend/app/services/entity_extractor.py
touch backend/app/services/project_discovery_service.py

# Copy code from markdown files into these files
```

### Step 4: Integrate Signal Detection
```python
# Modify backend/app/services/document_processor.py

# Add imports:
from app.services.sred_signal_detector import SREDSignalDetector
from app.services.entity_extractor import EntityExtractor

# In __init__:
self.sred_detector = SREDSignalDetector()
self.entity_extractor = EntityExtractor()

# In process_document(), after text extraction:
entities = self.entity_extractor.extract_entities(extracted_text)
signals = self.sred_detector.detect_signals(extracted_text)

document.sred_signals = {
    "uncertainty_keywords": signals.uncertainty_count,
    "systematic_keywords": signals.systematic_count,
    "failure_keywords": signals.failure_count,
    "novel_keywords": signals.advancement_count,
    "score": float(signals.score)
}

document.temporal_metadata = {
    "date_references": entities["dates"],
    "team_members": entities["people"],
    "project_names": entities["project_names"]
}
```

### Step 5: Create API Endpoints
```bash
# Create new endpoints file
touch backend/app/api/v1/endpoints/projects.py

# Copy implementation from phase3_4 document

# Register in main API router
# backend/app/api/v1/api.py:
from app.api.v1.endpoints import projects
api_router.include_router(projects.router)
```

### Step 6: Test End-to-End
```python
# Create test script: backend/test_discovery.py

import asyncio
from app.core.database import SessionLocal
from app.services.project_discovery_service import ProjectDiscoveryService
from app.services.embeddings import EmbeddingsService
from uuid import UUID

async def test_discovery():
    db = SessionLocal()
    
    # Use an existing claim ID from your database
    claim_id = UUID("YOUR-CLAIM-ID-HERE")
    
    # Run discovery
    embeddings = EmbeddingsService()
    discovery = ProjectDiscoveryService(embeddings)
    
    results = await discovery.discover_projects(claim_id, db)
    
    print(f"High confidence: {len(results['high_confidence'])}")
    print(f"Medium confidence: {len(results['medium_confidence'])}")
    print(f"Low confidence: {len(results['low_confidence'])}")
    
    for project in results['high_confidence']:
        print(f"\nProject: {project.name}")
        print(f"  SR&ED Score: {project.sred_score:.2f}")
        print(f"  Confidence: {project.confidence:.2f}")
        print(f"  Documents: {len(project.documents)}")
        print(f"  Summary: {project.summary}")

if __name__ == "__main__":
    asyncio.run(test_discovery())
```

Run test:
```bash
cd backend
python test_discovery.py
```

### Step 7: Frontend Integration
```typescript
// frontend/src/pages/ProjectDiscovery.tsx

import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function ProjectDiscovery({ claimId }: { claimId: string }) {
  // Run discovery
  const discoverMutation = useMutation({
    mutationFn: () => api.post('/projects/discover', { claim_id: claimId })
  })
  
  // Load projects
  const { data: projects } = useQuery({
    queryKey: ['projects', claimId],
    queryFn: () => api.get(`/projects/claim/${claimId}`)
  })
  
  return (
    <div>
      <button onClick={() => discoverMutation.mutate()}>
        Discover Projects
      </button>
      
      {projects?.high_confidence.map(project => (
        <ProjectCard 
          key={project.id}
          project={project}
          onApprove={...}
          onReject={...}
        />
      ))}
    </div>
  )
}
```

---

## Testing Strategy

### Unit Tests
```bash
# Test signal detection
pytest backend/tests/test_sred_detector.py

# Test entity extraction
pytest backend/tests/test_entity_extractor.py

# Test clustering
pytest backend/tests/test_project_discovery.py
```

### Integration Tests
```bash
# Test full pipeline
pytest backend/tests/test_discovery_pipeline.py -v
```

### Manual Testing
1. Upload 20+ documents to a test claim
2. Trigger discovery via API: `POST /projects/discover`
3. Verify projects created in database
4. Check document tags created
5. Test frontend displays results

---

## Migration Strategy for Existing Data

### Backfill SR&ED Signals
```python
# Script: backend/scripts/backfill_sred_signals.py

from app.models.models import Document
from app.services.sred_signal_detector import SREDSignalDetector
from app.services.entity_extractor import EntityExtractor

detector = SREDSignalDetector()
extractor = EntityExtractor()

# Process all documents
docs = db.query(Document).filter(
    Document.processing_status == 'complete'
).all()

for doc in docs:
    if doc.extracted_text:
        # Detect signals
        signals = detector.detect_signals(doc.extracted_text)
        entities = extractor.extract_entities(doc.extracted_text)
        
        # Update document
        doc.sred_signals = {
            "score": signals.score,
            "uncertainty_keywords": signals.uncertainty_count,
            # ...
        }
        doc.temporal_metadata = {
            "team_members": entities["people"],
            # ...
        }
        
        if len(docs) % 100 == 0:
            db.commit()
            print(f"Processed {len(docs)} documents")

db.commit()
print("Backfill complete!")
```

---

## Production Deployment Checklist

- [ ] Run database migrations
- [ ] Install Python dependencies (spacy, sklearn, hdbscan)
- [ ] Download spaCy model
- [ ] Backfill existing documents with SR&ED signals
- [ ] Test discovery on sample claims
- [ ] Deploy API endpoints
- [ ] Build and deploy frontend
- [ ] Monitor Celery workers for background tasks
- [ ] Set up error tracking (Sentry)
- [ ] Create admin interface for discovery runs

---

## Performance Considerations

### Discovery Algorithm Performance

| Documents | Cluster Time | Full Discovery |
|-----------|-------------|----------------|
| 100       | ~5 sec      | ~30 sec        |
| 500       | ~20 sec     | ~2 min         |
| 1000      | ~45 sec     | ~4 min         |
| 5000      | ~3 min      | ~15 min        |

**Optimization strategies:**
- Run discovery as background Celery task
- Cache embeddings (already done in your system)
- Use approximate nearest neighbors for very large datasets
- Batch process document signal detection

### Database Indexes

Already included in migration, but verify:
```sql
-- Critical indexes
CREATE INDEX idx_projects_claim ON projects(claim_id);
CREATE INDEX idx_projects_confidence ON projects(sred_confidence_score DESC);
CREATE INDEX idx_doc_tags_document ON document_project_tags(document_id);
CREATE INDEX idx_doc_tags_project ON document_project_tags(project_id);
CREATE INDEX idx_documents_sred_score ON documents((sred_signals->>'score'));
```

---

## Success Metrics

Track these to measure impact:

### Technical Metrics
- ✅ Project discovery accuracy (% approved by users)
  - Target: >70% of AI-suggested projects approved
  
- ✅ Document tagging accuracy
  - Target: >85% of auto-tagged docs confirmed as relevant
  
- ✅ Processing time
  - Target: <3 min for 500 documents

### Business Metrics
- ✅ Time to complete claim
  - Baseline: 45-64 hours (from your discussion)
  - Target: <20 hours
  
- ✅ Projects identified
  - Track: # of projects that wouldn't have been claimed otherwise
  
- ✅ User satisfaction
  - Target: NPS >8/10

---

## Troubleshooting

### Common Issues

**Issue:** Discovery finds 0 projects
- **Check:** Do documents have sred_signals populated?
- **Fix:** Run signal detection first
- **Check:** Verify documents have embeddings
- **Fix:** Re-run embedding generation

**Issue:** All projects in "low confidence"
- **Check:** Date ranges in documents
- **Fix:** Ensure document_date or created_at is set correctly
- **Check:** SR&ED signals
- **Fix:** Review keyword taxonomy, may need tuning for your domain

**Issue:** Too many projects (over-clustering)
- **Fix:** Increase `min_cluster_size` parameter in HDBSCAN
- **Tune:** Adjust feature weights (temporal vs semantic vs team)

**Issue:** Projects seem unrelated
- **Check:** Embedding quality
- **Fix:** Verify documents are being chunked semantically
- **Check:** Team member extraction
- **Fix:** Improve NER accuracy with custom patterns

---

## Next Steps After Implementation

Once basic discovery works:

1. **Tune clustering parameters** based on real data
2. **Add project splitting/merging UI** for user refinement
3. **Build change detection** for incremental uploads
4. **Add narrative generation** from discovered projects
5. **Implement learned re-ranker** to improve over time
6. **Create analytics dashboard** showing discovery insights

---

## Questions to Ask Before Starting

Ask Claude Code to verify:

1. **Database:** What PostgreSQL version are you using? (Need 11+ for pgvector)
2. **Python:** What version? (Need 3.10+ for some type hints)
3. **Celery:** Is Redis/Valkey already configured for task queue?
4. **Embeddings:** Are document embeddings already generated for all docs?
5. **Permissions:** Do you have row-level security policies to update?

---

## Summary

You have a **strong foundation** (~75% complete). The missing 25% is:

1. **Week 1:** Database schema + SR&ED detection
2. **Week 2:** Clustering algorithm
3. **Week 3:** API endpoints
4. **Week 4:** Frontend dashboard

**Total effort:** ~4 weeks for a complete, production-ready project discovery system.

The implementation builds entirely on what you already have - just extending existing services, adding new models, and creating a new UI layer.

**Start with Phase 1 (database) and Phase 2 (signals), test thoroughly, then move to discovery algorithm.**
