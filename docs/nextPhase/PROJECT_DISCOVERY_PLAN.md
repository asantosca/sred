# SR&ED Project Discovery System - Implementation Plan

## Overview

Implement an automated project discovery system that identifies potential SR&ED projects from uploaded documents, tags documents to projects, and provides interactive refinement.

## Phase 1: Database Schema Changes

### New Tables (in `sred_ds` schema)

**1. `projects`** - R&D project records
- Standard UUID primary key, company_id/claim_id foreign keys
- SR&ED scoring fields (confidence, signal counts)
- T661 narrative fields (lines 242, 244, 246)
- Team and temporal metadata
- Audit fields (created_at/by, updated_at/by)

**2. `document_project_tags`** - Many-to-many junction
- document_id, project_id with CASCADE deletes
- tagged_by ('ai' or 'user'), confidence_score
- Unique constraint on (document_id, project_id)

**3. `project_discovery_runs`** - Discovery execution history
- Tracks algorithm, parameters, results, timing
- Links to claim_id

**4. `document_upload_batches`** - Change detection
- Batch tracking for incremental uploads
- Impact summary JSON

### Extend Existing Tables

**`documents`** - Add columns:
- `sred_signals` (JSONB) - keyword counts and score
- `temporal_metadata` (JSONB) - dates, people, project names
- `upload_batch_id` (UUID FK)

**`document_chunks`** - Add column:
- `sred_keyword_matches` (JSONB) - per-chunk keyword matches

### Files to Modify
- `backend/alembic/versions/xxx_add_project_discovery.py` (new migration)
- `backend/app/models/models.py` (add new models, extend existing)
- `backend/app/schemas/project.py` (new Pydantic schemas)

---

## Phase 2: SR&ED Signal Detection

### New Service: `sred_signal_detector.py`

**Purpose**: Detect SR&ED eligibility signals using keyword taxonomy

**Implementation**:
- Keyword categories: uncertainty, systematic, failure, advancement, routine (penalty)
- Regex-based matching (compiled patterns for efficiency)
- Weighted scoring algorithm (uncertainty=3.0, failure=2.5, systematic=2.0, advancement=2.0)
- Returns `SREDSignals` dataclass with counts, score, and matched keywords

**Key Difference from Docs**:
- Keep it simple - regex only, no spaCy dependency initially
- Can add Claude-based enhancement later for higher accuracy

### New Service: `entity_extractor.py`

**Purpose**: Extract temporal metadata and entities

**Implementation Options**:
1. **Lightweight (recommended)**: Regex patterns for dates, Jira codes, project names
2. **Enhanced**: Use Claude for NER (batch with existing summarization call)

**Extract**:
- Date references (multiple formats → ISO normalization)
- Project identifiers (Jira codes: ABC-123, "Project Phoenix" patterns)
- Team member names (from email headers, meeting notes)

### Pipeline Integration

**Location**: `backend/app/services/document_processor.py`

**Integration Point**: After chunking, before embedding (Stage 2.5)

```
Extraction → Chunking → [SIGNAL DETECTION] → Embedding → Events → Summary
```

**Modification**:
- Add signal detection step in `process_chunking` or as new `process_sred_signals` method
- Store results in `document.sred_signals` and `document.temporal_metadata`
- Store chunk-level matches in `chunk.sred_keyword_matches`

### Files to Create/Modify
- `backend/app/services/sred_signal_detector.py` (new)
- `backend/app/services/entity_extractor.py` (new)
- `backend/app/services/document_processor.py` (modify)
- `backend/app/tasks/document_processing.py` (modify pipeline)

---

## Phase 3: Project Discovery Algorithm

### New Service: `project_discovery_service.py`

**Purpose**: Cluster documents into potential SR&ED projects

**Algorithm**:
1. Fetch all processed documents for claim (with tenant isolation!)
2. Extract multi-dimensional features:
   - Temporal: document dates (cyclical encoding)
   - Semantic: averaged chunk embeddings (via vector_storage_service, NOT ORM)
   - Team: hash-based team member encoding
3. Cluster using HDBSCAN (min_cluster_size=3)
4. Analyze each cluster:
   - Aggregate SR&ED signals
   - Generate project name (from metadata or Claude)
   - Generate eligibility summary (Claude)
   - Calculate confidence score
5. Categorize by confidence (high/medium/low)
6. Save projects and document tags

**Critical Patterns to Follow**:
- Use `vector_storage_service` for embedding retrieval (raw asyncpg)
- Filter ALL queries by `company_id`
- Fully async methods
- Proper error handling with rollback

### Dependencies to Add
```
scikit-learn>=1.3.0
hdbscan>=0.8.33
```

### Files to Create
- `backend/app/services/project_discovery_service.py` (new)

---

## Phase 4: API Endpoints

### New Endpoint Module: `projects.py`

**Endpoints**:
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/projects/discover` | Run discovery for claim |
| GET | `/api/v1/projects/claim/{claim_id}` | List projects for claim |
| GET | `/api/v1/projects/{project_id}` | Get project details |
| PATCH | `/api/v1/projects/{project_id}` | Update project |
| POST | `/api/v1/projects/{project_id}/approve` | Approve discovered project |
| POST | `/api/v1/projects/{project_id}/reject` | Reject discovered project |
| POST | `/api/v1/projects/{project_id}/documents/add` | Add docs to project |
| DELETE | `/api/v1/projects/{project_id}/documents/{doc_id}` | Remove doc |
| GET | `/api/v1/projects/{project_id}/documents` | List project docs |

**Patterns to Follow**:
- Use `Depends(get_current_user)` for auth
- Use `Depends(get_db)` for session
- Filter by `current_user.company_id` in all queries
- Rate limiting with `@limiter.limit()`
- Proper error handling with HTTPException

### Files to Create/Modify
- `backend/app/api/v1/endpoints/projects.py` (new)
- `backend/app/api/v1/api.py` (register router)
- `backend/app/schemas/project.py` (request/response models)

---

## Phase 5: Background Task Integration

### Celery Task for Discovery

**Location**: `backend/app/tasks/` (new file or extend existing)

**Purpose**: Run discovery as background task for large document sets

**Implementation**:
- `discover_projects_task(claim_id, user_id)`
- Progress tracking via discovery run record
- Error handling with status updates

### Optional: Backfill Task

**Purpose**: Populate SR&ED signals for existing documents

**Implementation**:
- Batch processing (100 docs at a time)
- Idempotent (skip if already has signals)

---

## Implementation Order & Progress

### Phase 1: Database Migration
- [x] Create migration file `b3c4d5e6f7a8_add_project_discovery_system.py`
- [x] Add `projects` table
- [x] Add `document_project_tags` table
- [x] Add `project_discovery_runs` table
- [x] Add `document_upload_batches` table
- [x] Extend `documents` table (sred_signals, temporal_metadata, upload_batch_id)
- [x] Extend `document_chunks` table (sred_keyword_matches)
- [x] Add SQLAlchemy models to `models.py`
- [x] Run migration, verify schema

### Phase 2: SR&ED Signal Detection
- [x] Create `sred_signal_detector.py` service
- [x] Create `entity_extractor.py` service (lightweight regex version)
- [x] Integrate into `document_processor.py`
- [x] Update Celery pipeline in `document_processing.py`
- [ ] Test with sample documents

### Phase 3: Project Discovery Algorithm
- [x] Add sklearn, hdbscan to `requirements.txt`
- [x] Create `project_discovery_service.py`
- [x] Implement feature extraction (temporal, semantic, team)
- [x] Implement HDBSCAN clustering
- [x] Implement cluster analysis and scoring
- [x] Implement project name/summary generation (from metadata)
- [ ] Test clustering with existing documents

### Phase 4: API Endpoints
- [x] Create `backend/app/schemas/project.py` (request/response models)
- [x] Create `backend/app/api/v1/endpoints/projects.py`
- [x] Implement POST `/projects/discover`
- [x] Implement GET `/projects/claim/{claim_id}`
- [x] Implement GET/PATCH `/projects/{project_id}`
- [x] Implement POST `/projects/{project_id}/approve` and `/reject`
- [x] Implement document management endpoints
- [x] Register router in `api.py`
- [ ] Test endpoints via Swagger

### Phase 5: Background Tasks & Polish
- [x] Create Celery task for async discovery (`discover_projects_task`)
- [x] Auto-discovery trigger after document processing completes
- [ ] Create backfill script for existing documents
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] End-to-end manual testing

### Phase 6: Interactive Workflow Enhancements (Backend)
- [x] Create `change_detection_service.py` for incremental uploads
- [x] Add API endpoints for batch analysis (`/projects/analyze-batch`)
- [x] Add API endpoint to apply document additions (`/projects/apply-additions`)
- [x] Add project context to chat RAG queries (`project_id` filter)
- [ ] WebSocket notifications for discovery progress

### Phase 7: Frontend Implementation

#### 7.1 Upload & Processing UI (Stage 1)
- [ ] Create `UploadProgressPanel` component
  - Document count by stage (uploaded, extracted, analyzed)
  - Progress bars with percentages
  - "Discovering projects..." status indicator
  - Estimated time remaining
- [ ] Add processing status polling to document upload flow
- [ ] Add auto-redirect to dashboard when discovery completes

#### 7.2 Project Discovery Dashboard (Stage 2)
- [ ] Create `ProjectDiscoveryDashboard` page (`/claims/{id}/projects`)
  - Header: Claim info, status, potential tax credit estimate
  - AI summary banner ("I found 6 potential projects...")
- [ ] Create `ProjectTierSection` component (collapsible)
  - HIGH CONFIDENCE (green) - expanded by default
  - NEEDS REVIEW (yellow) - collapsed
  - LOW CONFIDENCE (red) - collapsed
- [ ] Create `ProjectCard` component
  - Project name, date range, doc count, spend estimate, SR&ED score
  - AI eligibility summary (💬 tooltip/expandable)
  - Signal badges (Uncertainty, Experiments, Failures, Advancement)
  - Team members list
  - Action buttons: Approve, Reject, Review Docs, Edit, Ask About
- [ ] Create `UnassignedDocumentsCard` component
  - Count display with "View Documents" link

#### 7.3 Project Document Review Page (Stage 3B)
- [ ] Create `ProjectReviewPage` page (`/projects/{id}/review`)
  - Header: Project name, back button, approve/reject/edit actions
  - Tab navigation: Documents | Timeline | Team | Evidence Summary
- [ ] Create `DocumentFilterBar` component
  - Filter dropdowns: All, Uncertainty, Experiments, Advancements
  - Sort options: Confidence, Date, Relevance, Name
  - Search input
- [ ] Create `ProjectDocumentCard` component
  - Filename, confidence badge, tagged by indicator
  - "Also in: [other projects]" cross-reference
  - Relevant page ranges
  - AI Insight quote (💬)
  - Key Signals Found (bullet list)
  - Actions: View Full, Remove from Project, Ask Why, Edit Tags
- [ ] Create `AddDocumentsModal` component
  - Unassigned documents list with checkboxes
  - Search/filter within modal
  - "Add Selected" bulk action
- [ ] Create `QuickActionsPanel` component
  - Suggested queries: "Show failed experiments", "Find gaps", etc.

#### 7.4 Project-Scoped Chat (Stage 3C)
- [ ] Modify existing `ChatSidebar` component
  - Add project context header when project_id is set
  - Pass `project_id` to chat API calls
- [ ] Add "View Supporting Documents" button to chat responses
- [ ] Add "Add to T661 Narrative" action button
- [ ] Create context-aware suggested questions based on project

#### 7.5 Change Detection UI (Stage 4)
- [ ] Create `NewDocumentsAlert` banner component
  - Document count, upload date
  - Action buttons: Analyze, Review First, Later
- [ ] Create `ChangeAnalysisResultsPage` page
  - Three sections with distinct styling:
- [ ] Create `SafeAdditionsSection` component (green)
  - List of projects with documents to add
  - Per-project: AI explanation, doc count, preview button
  - "Add to Project" individual action
- [ ] Create `ReviewNeededSection` component (yellow/orange)
  - Narrative impact warnings with severity
  - Quote comparison (current vs new evidence)
  - AI recommendation text
  - Actions: Review Document, Revise Narrative, Discuss
- [ ] Create `NewProjectDiscoveredSection` component (blue)
  - Project card similar to dashboard
  - Actions: Add as Project, Review Evidence, Ignore
- [ ] Create `UnassignedBatchSection` component
  - Count and link to review
- [ ] Add "Accept All Safe Additions" bulk action button

#### 7.6 T661 Narrative Editor (Stage 5)
- [ ] Create `NarrativeEditorPage` page (`/projects/{id}/narrative`)
  - Project header with status
- [ ] Create `NarrativeSection` component (reusable for 242, 244, 246)
  - Section title (e.g., "LINE 242: Scientific or Technological Uncertainties")
  - Word count indicator with limit (e.g., "287 / 350 ✓")
  - Expandable/collapsible narrative text area
  - Source citations panel (linked documents)
  - Actions: Edit Manually, Regenerate, Approve
- [ ] Create `NarrativeTextEditor` component
  - Rich text editing (or plain with markdown preview)
  - Word count live update
  - Character limit warning
- [ ] Create `SourceCitationsPanel` component
  - List of source documents with page numbers
  - Click to view document
- [ ] Add "Export to T661 Form" functionality
- [ ] Add "Preview Full Form" modal
- [ ] Add "Save Draft" with auto-save

#### 7.7 State Management & API Integration
- [ ] Create `useProjectDiscovery` hook
  - Fetch projects by claim
  - Run discovery mutation
  - Save projects mutation
- [ ] Create `useChangeDetection` hook
  - Analyze batch mutation
  - Apply additions mutation
- [ ] Create `useProjectDocuments` hook
  - Fetch project documents
  - Add/remove document mutations
- [ ] Create `useNarratives` hook
  - Generate narrative mutation
  - Update narrative mutation
- [ ] Add Zustand store for project discovery state (or use React Query)

#### 7.8 Real-time Updates
- [ ] Implement WebSocket connection for processing status
- [ ] Add SSE/WebSocket for discovery progress updates
- [ ] Add optimistic UI updates for approve/reject actions
- [ ] Add toast notifications for background operations

---

## Verification Plan

### Unit Tests
- `test_sred_signal_detector.py` - keyword detection, scoring
- `test_entity_extractor.py` - date/project name extraction
- `test_project_discovery.py` - clustering, confidence scoring

### Integration Tests
- Upload documents → verify signals populated
- Run discovery → verify projects created
- API endpoints → full CRUD operations

### Manual Testing
1. Upload 20+ documents to test claim
2. Verify `sred_signals` populated in database
3. Call `POST /projects/discover`
4. Verify projects created with correct document tags
5. Test approve/reject/update via API
6. Verify tenant isolation (can't access other company's projects)

---

## Key Files Summary

**New Backend Files**:
- `backend/alembic/versions/b3c4d5e6f7a8_add_project_discovery_system.py` - Migration
- `backend/app/services/sred_signal_detector.py` - SR&ED keyword detection
- `backend/app/services/entity_extractor.py` - Date/name/Jira code extraction
- `backend/app/services/project_discovery_service.py` - HDBSCAN clustering
- `backend/app/services/change_detection_service.py` - Incremental upload analysis
- `backend/app/api/v1/endpoints/projects.py` - Project API endpoints
- `backend/app/schemas/project.py` - Pydantic request/response models

**Modified Backend Files**:
- `backend/app/models/models.py` - Added Project, DocumentProjectTag, etc.
- `backend/app/services/document_processor.py` - Added signal detection methods
- `backend/app/services/vector_storage.py` - Added project_id filter to search
- `backend/app/services/chat_service.py` - Added project context to RAG
- `backend/app/schemas/chat.py` - Added project_id to ChatRequest
- `backend/app/tasks/document_processing.py` - Auto-discovery trigger, Celery task
- `backend/app/api/v1/api.py` - Registered projects router
- `backend/requirements.txt` - Added sklearn, hdbscan

**New Frontend Files (Phase 7)**:
- `frontend/src/pages/ProjectDiscoveryDashboard.tsx`
- `frontend/src/pages/ProjectReviewPage.tsx`
- `frontend/src/pages/NarrativeEditorPage.tsx`
- `frontend/src/pages/ChangeAnalysisResultsPage.tsx`
- `frontend/src/components/projects/ProjectCard.tsx`
- `frontend/src/components/projects/ProjectTierSection.tsx`
- `frontend/src/components/projects/ProjectDocumentCard.tsx`
- `frontend/src/components/projects/AddDocumentsModal.tsx`
- `frontend/src/components/projects/NarrativeSection.tsx`
- `frontend/src/components/projects/ChangeDetection/*.tsx`
- `frontend/src/hooks/useProjectDiscovery.ts`
- `frontend/src/hooks/useChangeDetection.ts`
- `frontend/src/hooks/useProjectDocuments.ts`
- `frontend/src/hooks/useNarratives.ts`

---

## Design Decisions

1. **Entity Extraction**: Regex-only (lightweight, no spaCy dependency)
2. **Discovery Trigger**: Manual only (user clicks "Discover Projects" button)
3. **Backfill Strategy**: During discovery (populate missing signals when discovery runs)
