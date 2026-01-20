# Interactive Project Discovery Workflow - Complete User Experience

## Overview

This document describes the **complete interactive workflow** - how users interact with the system from claim creation through project approval, including all the UI states, user actions, and system responses we designed.

---

## Complete User Journey

### Stage 1: Claim Creation & Document Upload

**User Actions:**
```
1. User creates new claim
   - Company: TechCorp Inc.
   - Fiscal Year End: Dec 31, 2024
   - Upload documents OR connect to systems
   
2. User uploads 487 documents (or connects Jira, GitHub, Google Drive)
   
3. User clicks "Create Claim & Start Analysis"
```

**System Response:**
```
Background Processing (Automatic):
├── Upload documents to S3
├── Extract text (pdfplumber, python-docx, OCR)
├── Detect SR&ED signals (NEW in Phase 2)
│   ├── Keyword matching (uncertainty, systematic, failure, advancement)
│   ├── Extract entities (people, dates, project names)
│   └── Store in document.sred_signals, document.temporal_metadata
├── Chunk text (semantic chunking, 500-800 tokens)
├── Generate embeddings (OpenAI text-embedding-3-small)
└── Store in pgvector

Status shown to user:
┌─────────────────────────────────────────┐
│ Processing your documents...            │
│ ✅ Uploaded: 487/487                    │
│ ✅ Extracted: 487/487                   │
│ ✅ Analyzed: 487/487                    │
│ 🔄 Discovering projects... (30 sec)     │
└─────────────────────────────────────────┘
```

**What happens behind the scenes:**
```python
# After document upload completes
async def on_upload_complete(claim_id: UUID):
    # Automatically trigger project discovery
    discovery_service = ProjectDiscoveryService()
    results = await discovery_service.discover_projects(claim_id)
    
    # Save discovered projects to database
    await discovery_service.save_discovered_projects(claim_id, results)
    
    # Create document tags (many-to-many relationships)
    for project in results.all_projects:
        for doc_id in project.documents:
            tag = DocumentProjectTag(
                document_id=doc_id,
                project_id=project.id,
                tagged_by="ai",
                confidence_score=project.confidence
            )
            db.add(tag)
```

---

### Stage 2: Project Discovery Results (Main Dashboard)

**System automatically transitions to:**

```
┌──────────────────────────────────────────────────────────────────────┐
│  TechCorp Inc. - 2024 SR&ED Claim              [💬 Ask Claude]       │
│  Status: Discovery Complete                    [⚙️  Settings]        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ✨ I found 6 potential SR&ED projects                              │
│     3 show strong eligibility, 2 need review, 1 appears routine     │
│                                                                      │
│  Potential tax credit: ~$298,000                                    │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  HIGH CONFIDENCE ✅ (Likely Eligible)                                │
│                                                                      │
│  📊 Project 1: ML Fraud Detection System                            │
│     Jan 15 - Aug 30, 2024 • 89 docs • $320K • Score: 0.92          │
│                                                                      │
│     💬 This project shows clear technological uncertainty around    │
│        achieving sub-50ms ML inference latency. Evidence includes   │
│        23 mentions of uncertainty, 15 documented experiments, and   │
│        8 failed approaches before achieving breakthrough.           │
│                                                                      │
│     Signals: ⭐ Uncertainty (23) ⭐ Experiments (15) ⭐ Failures (8) │
│     Team: Sarah Kim, Mike Chen, James Park (8 members)             │
│                                                                      │
│     [✓ Approve Project]  [📄 Review 89 Docs]  [💬 Ask About This]  │
│     [✗ Reject]           [✏️  Edit]                                  │
│                                                                      │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  📊 Project 2: Real-time Data Pipeline                              │
│     Mar 1 - Nov 15, 2024 • 67 docs • $280K • Score: 0.85           │
│     [Same layout as above...]                                       │
│                                                                      │
│  📊 Project 3: Zero-Knowledge Proof Implementation                  │
│     Jun 1 - Dec 31, 2024 • 34 docs • $180K • Score: 0.81          │
│     [Same layout...]                                                │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  NEEDS REVIEW ⚠️  (2 projects)                                       │
│  [Collapsed - click to expand]                                      │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  LOW CONFIDENCE ❌ (Likely Not Eligible)                             │
│  [Collapsed - click to expand]                                      │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  📋 Unassigned Documents: 123                                        │
│     [View Documents]                                                 │
└──────────────────────────────────────────────────────────────────────┘
```

**Database State After Discovery:**

```sql
-- 6 Projects created
SELECT * FROM projects WHERE claim_id = 'claim-uuid';
/*
id        | project_name           | confidence | status     | ai_suggested
----------|------------------------|------------|------------|-------------
proj-1    | ML Fraud Detection     | 0.92       | discovered | true
proj-2    | Real-time Data Pipeline| 0.85       | discovered | true
proj-3    | Zero-Knowledge Proofs  | 0.81       | discovered | true
proj-4    | Security Framework     | 0.65       | discovered | true
proj-5    | API Gateway            | 0.58       | discovered | true
proj-6    | Mobile App UI          | 0.32       | discovered | true
*/

-- 364 Document-Project tags created (many docs tagged to multiple projects)
SELECT COUNT(*) FROM document_project_tags WHERE project_id IN (SELECT id FROM projects WHERE claim_id = 'claim-uuid');
-- Result: 364 tags for 487 documents (some docs in multiple projects)

-- Tag breakdown
SELECT 
  project_id,
  COUNT(*) as doc_count,
  AVG(confidence_score) as avg_confidence,
  tagged_by
FROM document_project_tags
WHERE project_id IN (SELECT id FROM projects WHERE claim_id = 'claim-uuid')
GROUP BY project_id, tagged_by;
/*
project_id | doc_count | avg_confidence | tagged_by
-----------|-----------|----------------|----------
proj-1     | 89        | 0.87           | ai
proj-2     | 67        | 0.82           | ai
proj-3     | 34        | 0.79           | ai
proj-4     | 45        | 0.61           | ai
proj-5     | 38        | 0.55           | ai
proj-6     | 23        | 0.35           | ai
(plus 68 overlapping docs tagged to multiple projects)
*/
```

---

### Stage 3A: Quick Path - User Approves Projects

**User clicks:** `[✓ Approve Project]` on Project 1

**System Response:**
```python
# API call
POST /api/v1/projects/{project_id}/approve

# Backend updates
async def approve_project(project_id: UUID):
    project = await db.get(Project, project_id)
    project.project_status = "approved"
    project.user_confirmed = True
    project.updated_by = current_user.id
    await db.commit()
    
    return {"status": "approved"}
```

**UI Updates:**
```
Project 1 moves to "Approved" section:

┌──────────────────────────────────────────────────────────────┐
│  ✅ APPROVED PROJECTS (1)                                     │
│                                                              │
│  ✓ Project 1: ML Fraud Detection System                     │
│    89 docs • $320K • Ready for narrative generation         │
│    [📝 Generate T661 Narrative]  [📄 View Docs]             │
└──────────────────────────────────────────────────────────────┘
```

**User continues approving:**
- Project 2: ✓ Approve
- Project 3: ✓ Approve
- Project 4: [Reviews documents first...]

---

### Stage 3B: Thorough Path - User Reviews Documents

**User clicks:** `[📄 Review 89 Docs]` on Project 1

**New view appears:**

```
┌──────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                Project: ML Fraud Detection      │
│                                     [✓ Approve] [✗ Reject] [✏️ Edit]  │
├──────────────────────────────────────────────────────────────────────┤
│  Documents (89) | Timeline | Team Members | Evidence Summary         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Filter: [All ▼] [Uncertainty] [Experiments] [Advancements]         │
│  Sort: [Confidence ▼] [Date] [Relevance] [Name]                     │
│  Search: [_________________________________]                         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 📄 technical_meeting_2024-03-15.pdf                            │ │
│  │    Confidence: High (92%) • Tagged by: AI                      │ │
│  │    Also in: Data Pipeline Project                              │ │
│  │    Pages: 1-5 relevant to this project                         │ │
│  │                                                                 │ │
│  │    💬 AI Insight: This document contains key evidence of       │ │
│  │       technological uncertainty. Quote: "No existing           │ │
│  │       architecture can achieve <50ms latency with our          │ │
│  │       accuracy requirements."                                  │ │
│  │                                                                 │ │
│  │    Key Signals Found:                                          │ │
│  │    • Uncertainty: "no existing solution", "unclear how to"     │ │
│  │    • Systematic: "hypothesis", "experiment"                    │ │
│  │                                                                 │ │
│  │    [📖 View Full Document]  [✗ Remove from Project]            │ │
│  │    [💬 Why is this relevant?]  [🏷️  Edit Tags]                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 📊 experiment_log_march_april.xlsx                             │ │
│  │    Confidence: Very High (95%) • Tagged by: AI                 │ │
│  │    Rows: 15-47 relevant                                        │ │
│  │                                                                 │ │
│  │    💬 AI Insight: Perfect evidence of systematic investigation.│ │
│  │       Shows 12 experiments with hypothesis-test-result cycles. │ │
│  │                                                                 │ │
│  │    Evidence for T661 Line 244:                                 │ │
│  │    ✓ Hypothesis formulation                                    │ │
│  │    ✓ Experimental methodology                                  │ │
│  │    ✓ Failed attempts documented                                │ │
│  │                                                                 │ │
│  │    [📖 View]  [✗ Remove]  [💬 Ask]  [📋 Use in Narrative]      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ... (87 more documents)                                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 📁 Unassigned Documents (123)                                  │ │
│  │    [+ Add Documents to This Project]                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  💬 Quick Actions:                                                  │
│     • "Show me all failed experiments"                             │
│     • "Find documents mentioning latency problems"                 │
│     • "Are there any gaps in the documentation?"                   │
│     • "Which documents support Line 242 (uncertainty)?"            │
└──────────────────────────────────────────────────────────────────────┘
```

**User Actions on This Page:**

**Remove irrelevant document:**
```
User clicks: [✗ Remove from Project]

System: DELETE FROM document_project_tags 
        WHERE document_id = 'doc-15' AND project_id = 'proj-1'

UI: Document disappears from list
    Document count updates: 89 → 88
```

**Add document from unassigned:**
```
User clicks: [+ Add Documents to This Project]

Modal appears:
┌──────────────────────────────────────────┐
│  Add Documents to Project                │
├──────────────────────────────────────────┤
│  Showing 123 unassigned documents        │
│                                          │
│  [x] security_review_june.pdf            │
│  [ ] marketing_deck.pptx                 │
│  [x] architecture_v2.pdf                 │
│  ...                                     │
│                                          │
│  [Cancel]  [Add Selected (2)]            │
└──────────────────────────────────────────┘

System: INSERT INTO document_project_tags (document_id, project_id, tagged_by, created_by)
        VALUES ('doc-150', 'proj-1', 'user', current_user_id)

UI: Document count updates: 88 → 90
```

---

### Stage 3C: Conversational Path - User Asks Questions

**User clicks:** `[💬 Ask About This]` on Project 1

**Chat sidebar opens:**

```
┌────────────────────────────────────────┐
│  💬 Chat with Claude                   │
│  Context: ML Fraud Detection Project   │
├────────────────────────────────────────┤
│                                        │
│ You: Why does this project qualify    │
│      for SR&ED? I'm not sure about    │
│      the "uncertainty" part.           │
│                                        │
│ Claude: Great question! This project  │
│ clearly qualifies based on 3 key      │
│ factors:                               │
│                                        │
│ 1. **Technological Uncertainty**      │
│    Your team faced an uncertain       │
│    problem: how to achieve <50ms ML   │
│    inference while maintaining 95%    │
│    accuracy. I found evidence in:     │
│                                        │
│    - Meeting notes (Mar 15): "No      │
│      existing framework can do this"  │
│    - Email from Sarah: "Tried all     │
│      standard approaches, none work"  │
│    - Design doc: "Unclear if          │
│      technically possible"            │
│                                        │
│    This wasn't routine optimization - │
│    it was genuinely uncertain whether │
│    the goal was achievable.           │
│                                        │
│ 2. **Systematic Investigation**       │
│    The experiment log shows 12        │
│    distinct approaches tested:        │
│    • Approach 1: Standard LSTM (failed│
│      - 250ms latency)                 │
│    • Approach 2: Quantization (failed │
│      - 30% accuracy loss)             │
│    ... [8 more attempts]              │
│    • Approach 12: Hybrid architecture │
│      (success - 45ms, 97% accuracy)   │
│                                        │
│    Each had a hypothesis, test, and   │
│    documented result. Textbook        │
│    systematic investigation!          │
│                                        │
│ 3. **Advancement Achieved**           │
│    The final solution represents a    │
│    technological advancement - no     │
│    prior work achieved real-time ML   │
│    inference at this scale.           │
│                                        │
│ [📄 View Supporting Documents]        │
│ [📝 Add to T661 Narrative]            │
│                                        │
│ Would you like me to draft the Line   │
│ 242 (uncertainty) section based on    │
│ this evidence?                         │
│                                        │
│ You: ___________________________      │
└────────────────────────────────────────┘
```

**Behind the scenes:**
```python
# Chat API call
POST /api/v1/chat/message
{
  "claim_id": "claim-uuid",
  "context": {
    "current_project": "proj-1",
    "project_name": "ML Fraud Detection",
    "recent_action": "reviewing_project"
  },
  "message": "Why does this project qualify for SR&ED?"
}

# System retrieves relevant evidence
evidence = await vector_service.search(
    query="technological uncertainty systematic investigation ML fraud detection",
    filter={"project_id": "proj-1"},
    top_k=10
)

# Claude API called with context
response = anthropic.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[{
        "role": "user",
        "content": f"""Project: {project.name}
        
        User question: Why does this qualify for SR&ED?
        
        Evidence: {evidence}
        
        Explain eligibility focusing on uncertainty, systematic investigation, and advancement."""
    }]
)
```

---

### Stage 4: Incremental Document Upload (Change Detection)

**Scenario:** User uploads 150 more documents on Day 3

**System Detects Change:**
```
┌──────────────────────────────────────────────────────────────┐
│  TechCorp Inc. - 2024 SR&ED Claim                            │
│  Status: 3 approved, 2 under review                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  🔔 NEW DOCUMENTS DETECTED (150 files)                       │
│                                                              │
│  💬 I found 150 new documents uploaded on Jan 18, 2025.     │
│     Would you like me to analyze how they relate to your    │
│     existing projects?                                       │
│                                                              │
│  Analysis will check if they:                               │
│  • Add evidence to existing approved projects               │
│  • Reveal new potential projects                            │
│  • Affect completed narratives                              │
│                                                              │
│  [🔍 Analyze New Documents]  [📋 Review First]  [⏸️ Later]   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**User clicks:** `[🔍 Analyze New Documents]`

**Backend Process:**
```python
# Create upload batch record
batch = DocumentUploadBatch(
    claim_id=claim_id,
    batch_number=2,  # Second batch
    document_count=150
)

# Process new documents (same pipeline as initial upload)
for doc in new_documents:
    extract_text(doc)
    detect_sred_signals(doc)
    extract_entities(doc)
    chunk_and_embed(doc)

# Analyze impact on existing projects
impact_service = ChangeDetectionService()
impact = await impact_service.analyze_impact(claim_id, new_doc_ids)

# Returns:
{
  "additions_to_existing": [
    {"project_id": "proj-1", "doc_ids": [23 docs], "confidence": "high"},
    {"project_id": "proj-2", "doc_ids": [15 docs], "confidence": "high"},
  ],
  "new_projects_discovered": [
    {"project_name": "API Rate Limiter", "doc_ids": [56 docs], "confidence": 0.84}
  ],
  "narrative_impacts": [
    {"project_id": "proj-2", "severity": "high", "type": "contradiction"}
  ]
}
```

**Results Shown to User:**

```
┌──────────────────────────────────────────────────────────────────┐
│  Analysis Complete: New Documents Impact                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ SAFE TO ADD (Strengthens existing projects)                  │
│                                                                  │
│  ✓ ML Fraud Detection (APPROVED)                                │
│    +23 documents added                                          │
│    💬 Found 12 more experiment logs that strengthen your Line   │
│       244 evidence. The systematic investigation is now even    │
│       better documented.                                        │
│    [✓ Add to Project]  [Preview Docs]                           │
│                                                                  │
│  ✓ Real-time Data Pipeline (APPROVED)                           │
│    +15 documents added                                          │
│    💬 Additional architecture docs and performance benchmarks.  │
│    [✓ Add to Project]  [Preview Docs]                           │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ⚠️  REVIEW NEEDED                                               │
│                                                                  │
│  ⚠️  Real-time Data Pipeline - NARRATIVE IMPACT                  │
│     +8 documents contain important information                  │
│                                                                  │
│     ⚠️  WARNING: One email (from Sarah, Nov 12) suggests the    │
│         "novel architecture" in your narrative was adapted      │
│         from an open-source project (etcd's Raft consensus).    │
│                                                                  │
│     Current narrative states:                                   │
│     "developed a novel distributed coordination protocol"       │
│                                                                  │
│     New evidence:                                               │
│     "We adapted Raft consensus from etcd for our streaming      │
│      data use case..."                                          │
│                                                                  │
│     📝 RECOMMENDATION: Revise narrative to emphasize the        │
│        novel ADAPTATION not the base algorithm. Focus on        │
│        what was new: applying Raft to streaming data with       │
│        ACID guarantees.                                         │
│                                                                  │
│     [📖 Review Email]  [✏️  Revise Narrative]  [💬 Discuss]     │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🆕 NEW PROJECT DISCOVERED                                       │
│                                                                  │
│  🆕 API Rate Limiting System                                     │
│     56 documents • Oct-Dec 2024 • Est. $95K                     │
│     SR&ED Score: High (0.84)                                    │
│                                                                  │
│     💬 The new documents reveal a 4th SR&ED project you didn't  │
│        mention initially. Strong evidence of novel distributed  │
│        rate limiting algorithm development.                     │
│                                                                  │
│     Key signals:                                                │
│     • Technological uncertainty: "No existing rate limiter      │
│       handles our edge cases"                                   │
│     • Systematic investigation: 8 different approaches tested   │
│     • Advancement: Custom algorithm achieving 10x throughput    │
│                                                                  │
│     [✓ Add as 4th Project]  [📄 Review Evidence]  [✗ Ignore]   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ℹ️  UNASSIGNED: 48 documents                                    │
│     Don't clearly belong to any project                         │
│                                                                  │
│  [Accept All Safe Additions]  [Review Each Change]              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**User Actions:**
```
1. [✓ Add to Project] on safe additions
   → System creates new document_project_tags (tagged_by='ai')
   
2. [✏️ Revise Narrative] on Data Pipeline
   → Opens narrative editor with highlighted section
   → Shows suggested revision
   
3. [✓ Add as 4th Project] on API Rate Limiter
   → System creates new Project record
   → Creates document tags for 56 documents
   → Project appears in dashboard
   
4. [Accept All Safe Additions]
   → Batch creates all tags for additions
   → Updates project document counts
```

---

### Stage 5: Narrative Generation (After Projects Approved)

**User clicks:** `[📝 Generate T661 Narrative]` on approved Project 1

**System Process:**
```python
# Evidence extraction for each T661 section
line_242_evidence = await get_line_242_evidence(project_id)
# Returns:
{
  "evidence_chunks": [
    {
      "text": "No existing ML framework could achieve sub-50ms latency...",
      "document": "technical_meeting_2024-03-15.pdf",
      "page": 3,
      "confidence": 0.92
    },
    # ... 9 more chunks
  ],
  "suggested_narrative": "The project encountered technological uncertainty..."
}

line_244_evidence = await get_line_244_evidence(project_id)
# Returns hypothesis-test cycles chronologically

line_246_evidence = await get_line_246_evidence(project_id)
# Returns advancement metrics and comparisons

# Generate narratives using Claude
narrative_242 = await generate_narrative(project_id, line=242, evidence=line_242_evidence)
narrative_244 = await generate_narrative(project_id, line=244, evidence=line_244_evidence)
narrative_246 = await generate_narrative(project_id, line=246, evidence=line_246_evidence)

# Save to project
project.narrative_line_242 = narrative_242.text
project.narrative_line_244 = narrative_244.text
project.narrative_line_246 = narrative_246.text
project.narrative_status = "draft"
```

**UI Shows:**

```
┌──────────────────────────────────────────────────────────────────┐
│  Project: ML Fraud Detection System                             │
│  T661 Form Narratives - DRAFT                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LINE 242: Scientific or Technological Uncertainties            │
│  Word Count: 287 / 350  ✓                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ The project encountered technological uncertainty regarding │ │
│  │ achieving real-time machine learning inference with         │ │
│  │ sub-50-millisecond latency while maintaining 95% detection  │ │
│  │ accuracy for fraud patterns. At the project's inception in  │ │
│  │ January 2024, no existing ML framework or architecture      │ │
│  │ could achieve this combination of speed and accuracy...     │ │
│  │                                                              │ │
│  │ [Full narrative - click to expand]                          │ │
│  │                                                              │ │
│  │ 📎 Sources:                                                  │ │
│  │ • technical_meeting_2024-03-15.pdf (p.3)                    │ │
│  │ • email_sarah_uncertainty.eml                               │ │
│  │ • architecture_requirements.docx (p.2)                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│  [✏️  Edit Manually]  [🔄 Regenerate]  [✓ Approve]              │
│                                                                  │
│  LINE 244: Work Performed                                       │
│  Word Count: 612 / 700  ✓                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ The team conducted systematic investigation through twelve  │ │
│  │ distinct experimental approaches between January and August │ │
│  │ 2024. The first hypothesis proposed that standard LSTM...   │ │
│  │                                                              │ │
│  │ [Full narrative]                                            │ │
│  │                                                              │ │
│  │ 📎 Sources: (12 documents)                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│  [✏️  Edit]  [🔄 Regenerate]  [✓ Approve]                       │
│                                                                  │
│  LINE 246: Advancements Achieved                               │
│  Word Count: 298 / 350  ✓                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ The project achieved a technological advancement by...      │ │
│  │ [Full narrative]                                            │ │
│  │ 📎 Sources: (6 documents)                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│  [✏️  Edit]  [🔄 Regenerate]  [✓ Approve]                       │
│                                                                  │
│  [Export to T661 Form]  [Save Draft]  [Preview Full Form]      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Database State Throughout Journey

### After Initial Discovery
```sql
-- Claims table
claim_id | company_name  | fiscal_year_end | claim_status
---------|---------------|-----------------|-------------
claim-1  | TechCorp Inc. | 2024-12-31     | in_progress

-- Projects table  
project_id | claim_id | project_name        | confidence | status     | user_confirmed
-----------|----------|---------------------|------------|------------|---------------
proj-1     | claim-1  | ML Fraud Detection  | 0.92       | discovered | false
proj-2     | claim-1  | Real-time Pipeline  | 0.85       | discovered | false
proj-3     | claim-1  | ZK Proofs           | 0.81       | discovered | false
proj-4     | claim-1  | Security Framework  | 0.65       | discovered | false
proj-5     | claim-1  | API Gateway         | 0.58       | discovered | false
proj-6     | claim-1  | Mobile App UI       | 0.32       | discovered | false

-- Document tags (sample)
tag_id | document_id | project_id | tagged_by | confidence
-------|-------------|------------|-----------|------------
tag-1  | doc-1       | proj-1     | ai        | 0.89
tag-2  | doc-1       | proj-2     | ai        | 0.45  -- Same doc in 2 projects!
tag-3  | doc-2       | proj-1     | ai        | 0.91
...
```

### After User Approves Projects 1, 2, 3
```sql
UPDATE projects 
SET project_status = 'approved', user_confirmed = true 
WHERE project_id IN ('proj-1', 'proj-2', 'proj-3');

-- Result:
proj-1  | approved  | true
proj-2  | approved  | true
proj-3  | approved  | true
proj-4  | discovered| false
```

### After User Removes/Adds Documents
```sql
-- User removes doc-15 from proj-1
DELETE FROM document_project_tags 
WHERE document_id = 'doc-15' AND project_id = 'proj-1';

-- User adds doc-150 and doc-151 to proj-1
INSERT INTO document_project_tags (document_id, project_id, tagged_by, created_by)
VALUES 
  ('doc-150', 'proj-1', 'user', 'user-123'),
  ('doc-151', 'proj-1', 'user', 'user-123');
```

### After Incremental Upload and Analysis
```sql
-- New batch created
INSERT INTO document_upload_batches (claim_id, batch_number, document_count)
VALUES ('claim-1', 2, 150);

-- New project discovered
INSERT INTO projects (claim_id, project_name, confidence, status, discovery_method)
VALUES ('claim-1', 'API Rate Limiter', 0.84, 'discovered', 'ai_clustering_incremental');

-- New tags for batch 2 documents
INSERT INTO document_project_tags (document_id, project_id, tagged_by, upload_batch_id)
SELECT id, 'proj-1', 'ai', 'batch-2' 
FROM documents 
WHERE id IN (SELECT document_id FROM batch_2_additions_to_proj_1);
```

### After Narratives Generated
```sql
UPDATE projects 
SET 
  narrative_line_242 = 'The project encountered technological uncertainty...',
  narrative_line_244 = 'The team conducted systematic investigation...',
  narrative_line_246 = 'The project achieved technological advancement...',
  narrative_status = 'draft',
  narrative_word_count_242 = 287,
  narrative_word_count_244 = 612,
  narrative_word_count_246 = 298
WHERE project_id = 'proj-1';
```

---

## Summary: Complete Data Flow

```
1. User uploads documents
   ↓
   documents table populated (with sred_signals, temporal_metadata)
   
2. System runs discovery
   ↓
   projects table populated (6 projects)
   document_project_tags table populated (364 tags)
   project_discovery_runs table (1 run record)
   
3. User reviews and refines
   ↓
   projects.status updated (approved/rejected)
   document_project_tags modified (add/remove)
   
4. User uploads more documents (batch 2)
   ↓
   document_upload_batches table (batch record)
   documents table (150 new rows)
   
5. System analyzes batch 2
   ↓
   project_discovery_runs table (2nd run)
   projects table (1 new project)
   document_project_tags table (updates for new docs)
   
6. System generates narratives
   ↓
   projects.narrative_* fields populated
   
7. User exports to T661
   ↓
   Generate PDF/Word with all narratives and citations
```

---

## Key Interactive Features Summary

✅ **Auto-Discovery** - Projects created automatically after upload
✅ **Tag-Based Organization** - Documents stay in place, virtual organization via tags
✅ **Multi-Project Documents** - Same doc can belong to multiple projects
✅ **AI Confidence Scores** - Every tag has confidence, user can review low-confidence
✅ **Interactive Refinement** - Add/remove docs, approve/reject projects
✅ **Conversational Interface** - Ask questions about any project
✅ **Change Detection** - Handles incremental uploads intelligently
✅ **Impact Analysis** - Shows how new docs affect existing projects
✅ **Narrative Generation** - Auto-draft T661 sections with citations
✅ **Source Tracking** - Every claim backed by specific documents

This is the complete interactive workflow that integrates all the components from Phases 1-4!
