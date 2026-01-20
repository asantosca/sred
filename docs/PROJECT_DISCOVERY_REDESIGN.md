# Project Discovery Redesign

## Overview

This document outlines a redesign of the SR&ED project discovery system to create a more collaborative, AI-assisted workflow for preparing T661 claims.

## Current State (Problems)

### 1. Rigid Discovery Process
- Discovery outputs structured project candidates with fixed fields
- User can only approve/reject - no collaboration
- T661 narratives generated separately as a one-shot operation

### 2. Name-Based Grouping
- Projects identified by looking for "Project X" naming patterns
- Misses R&D work that doesn't follow naming conventions
- Should identify work by **technological uncertainty**, not naming

### 3. Missing SR&ED Context
- Dates are just min/max of document dates, not uncertainty start → resolution
- Contributors extracted from email headers only, missing titles/roles
- No narrative explaining Why/Goal/How during discovery

### 4. No Collaboration
- User cannot iterate on project definitions
- No way to merge/split projects naturally
- No conversation about the projects

---

## New Vision

### Core Concept: Collaborative Markdown Workspace

Instead of structured database fields, projects are defined in a **single markdown file** that the user and AI collaboratively edit through chat.

```
┌─────────────────────────────────────────────────────────────┐
│ Conversation (type="project_workspace")                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ projects.md (source of truth)                          │ │
│  │                                                         │ │
│  │ # Project 1: AURORA - ML Inference Optimization        │ │
│  │ ### Dates                                               │ │
│  │ - Start: Feb 15, 2024 (uncertainty identified)         │ │
│  │ - End: Sep 30, 2024 (resolution achieved)              │ │
│  │ ### Contributors                                        │ │
│  │ - Dr. Sarah Chen, Principal Engineer (Technical Lead)  │ │
│  │ ### Documents                                           │ │
│  │ - [AURORA Kickoff](doc:abc123) - Feb 2024              │ │
│  │ ### Narrative                                           │ │
│  │ **Uncertainty (Why)**: The project addressed...        │ │
│  │ **Objective (Goal)**: Develop a real-time...           │ │
│  │ **Investigation (How)**: The team investigated...      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Chat History                                            │ │
│  │                                                         │ │
│  │ [AI] I found 3 projects in your documents...           │ │
│  │ [User] Merge AURORA and BEACON                          │ │
│  │ [AI] Done. Updated the document...                      │ │
│  │ [User] The start date should be February                │ │
│  │ [AI] Updated AURORA start date to Feb 15...             │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### AI Roles

| Role | When | What |
|------|------|------|
| **Discoverer** | Initial analysis | Find projects from documents using SR&ED signals |
| **Draft Author** | After discovery | Generate markdown with Why/Goal/How narratives |
| **Collaborator** | During review | Edit markdown based on chat, answer questions |
| **Compliance Checker** | Ongoing | Warn about CRA issues |
| **Streamliner** | Before export | Format to T661 specs (word limits, terminology) |

### User Capabilities

- **Edit markdown directly** - Factual corrections, additions
- **Chat with AI** - Request changes, ask questions
- **Merge/split via chat** - "Merge AURORA and BEACON into one project"
- **Adjust dates via chat** - "The start date should be February"
- **Remove projects** - Delete from markdown or ask AI: "Remove Project 3"
- **Export to T661** - Generate CRA-compliant format when ready

### No Approve/Reject Paradigm

The old workflow required users to approve or reject AI-discovered project candidates. This is replaced with **iterative collaboration**:

| Old (Binary) | New (Collaborative) |
|--------------|---------------------|
| AI suggests project → User approves/rejects | AI drafts markdown → User refines with AI |
| Rejected = lost forever | Don't want it? Edit it out or ask AI to remove |
| Approved = locked in database | Everything is editable until export |
| One-shot decision | Continuous refinement |

### No Claim Status Tracking

The workspace does not track claim lifecycle status (draft, submitted, approved, closed, etc.). The workspace is simply a tool for preparing T661 content. Status tracking, if needed, happens outside this system.

---

## User Flow

### 1. Upload Phase
```
User uploads all documents for a claim
→ Documents processed (text extraction, embeddings, SR&ED signals)
```

### 2. Discovery Phase
```
User clicks "Discover Projects"
→ AI analyzes documents using SR&ED signals (not naming patterns)
→ Creates project_workspace conversation
→ Generates initial markdown with:
   • Project names (up to 20)
   • Dates (uncertainty start → resolution)
   • Contributors (with titles/roles)
   • Narrative (Why/Goal/How)
   • Document links
```

### 3. Collaboration Phase
```
User reviews markdown + chats with AI
→ User can edit markdown directly
→ User can request changes via chat
→ AI edits markdown, explains changes in chat
→ All changes tracked in chat history (audit trail)
```

### 4. Document Changes
```
If documents are added/removed after discovery:
→ AI detects changes on next chat interaction
→ AI notifies user: "3 documents were added since last discovery"
→ AI offers to re-run discovery on all documents
→ Markdown is regenerated (chat history preserved as audit)
```

### 5. Export Phase
```
User clicks "Export to T661"
→ AI streamlines markdown for CRA compliance:
   • Word limits (242: 350, 244: 700, 246: 350)
   • SR&ED terminology
   • Source citations
→ Generates T661 format
→ User downloads/copies for use in actual filing
```

---

## Key Design Decisions

### 1. SR&ED-First Discovery (Already Implemented)
Instead of grouping by project names, identify documents by SR&ED signals:
- Find documents with **technological uncertainty** keywords
- Cluster those documents semantically (by topic)
- Use project names for **labeling**, not grouping

### 2. SR&ED Dates (Already Implemented)
- **Start Date**: Earliest document with uncertainty signals
- **End Date**: Latest document with advancement OR failure signals
- Fallback to document date range if no signals

### 3. Contributor Extraction (Already Implemented)
- Extract names with titles from documents
- Classify roles: technical, management, support
- Flag qualified personnel for SR&ED
- Score contributions: authors > recipients > mentioned

### 4. Markdown as Source of Truth
- Single markdown file contains all project information
- Human and machine readable
- Easy to edit, version, share
- AI can parse and update

### 5. Chat-Driven Actions
- Merge, split, adjust dates via natural language
- No complex form UIs
- AI handles the complexity
- Everything auditable in chat history

### 6. Document Change Handling
- AI detects added/removed documents
- Notifies user on next interaction
- Offers full re-discovery
- Chat history preserves previous decisions

### 7. No Project Table Required
The `projects` and `project_document_tags` tables are **not needed** in this design:
- Markdown contains all project attributes (name, dates, contributors, narrative, document links)
- Parse markdown on-demand when structured data is needed
- No synchronization issues between markdown and database
- Simpler architecture with single source of truth

**When structured data is needed:**
- **T661 Generation**: Parse markdown to extract narratives for Lines 242, 244, 246
- **API Responses**: Parse markdown to return project list with metadata
- **Validation**: Parse markdown to check CRA compliance (word limits, 20 project max)

---

## Data Model Changes

### Conversation Model Updates

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id: UUID
    claim_id: UUID
    user_id: UUID
    title: str

    # NEW FIELDS
    conversation_type: str = "general"  # "general" | "project_workspace"
    workspace_md: Optional[str] = None  # Markdown (project_workspace only)
    last_discovery_at: Optional[datetime] = None  # When discovery last ran
    known_document_ids: Optional[List[UUID]] = None  # Docs at last discovery

    created_at: datetime
    updated_at: datetime
```

### Constraints
- Each claim has exactly ONE conversation with `type="project_workspace"`
- Other conversations (`type="general"`) can exist for general Q&A

---

## Markdown Structure

```markdown
# SR&ED Claim: {Company Name} FY{Year}

*Last updated: {date}*
*Documents analyzed: {count}*

---

## Project 1: {Project Name}

### Dates
- **Start**: {date} ({how uncertainty was identified})
- **End**: {date} ({how resolved or abandoned})

### Contributors
- {Name}, {Title} ({Role - e.g., Technical Lead})
- {Name}, {Title}
- {Name}, {Title}

### Documents
- [{filename}](doc:{uuid}) - {date} - {brief description}
- [{filename}](doc:{uuid}) - {date} - {brief description}

### Narrative

**Technological Uncertainty (Why)**
{2-3 paragraphs explaining what was unknown and why standard
approaches couldn't solve it}

**Objective (Goal)**
{1-2 paragraphs explaining what the project aimed to achieve}

**Systematic Investigation (How)**
{2-3 paragraphs explaining the methodology, experiments,
iterations, and what was learned}

**Outcome**
{1 paragraph on resolution or why abandoned}

---

## Project 2: {Project Name}
...

---

## Orphan Documents
Documents not yet assigned to a project:
- [{filename}](doc:{uuid}) - {date}
```

---

## Implementation Plan

### Phase 1: Data Model Updates
**Files to modify:**
- `backend/app/models/models.py` - Add fields to Conversation model
- `backend/alembic/versions/` - Migration for new fields

**Tasks:**
1. Add `conversation_type` field (default: "general")
2. Add `workspace_md` field (nullable text)
3. Add `last_discovery_at` field (nullable datetime)
4. Add `known_document_ids` field (nullable JSON array)
5. Create and run migration

**Note:** No changes to `projects` or `project_document_tags` tables - they will be deprecated

### Phase 2: Discovery Markdown Generation
**Files to modify:**
- `backend/app/services/project_discovery_service.py` - Generate markdown
- `backend/app/schemas/project.py` - Update response schemas

**Tasks:**
1. Create `_generate_project_markdown()` method
2. Generate full narrative (Why/Goal/How) using AI
3. Include dates, contributors, document links
4. Update discovery endpoint to create/update workspace conversation
5. Store markdown in `workspace_md` field

### Phase 3: Workspace API Endpoints
**Files to create/modify:**
- `backend/app/api/v1/endpoints/workspace.py` - New endpoints

**Endpoints:**
1. `GET /claims/{id}/workspace` - Get workspace markdown + chat
2. `PUT /claims/{id}/workspace` - Update markdown (user direct edit)
3. `POST /claims/{id}/workspace/chat` - Chat with AI about projects
4. `POST /claims/{id}/workspace/discover` - Run/re-run discovery

### Phase 4: AI Chat Integration
**Files to modify:**
- `backend/app/services/chat_service.py` - Workspace-aware chat

**Tasks:**
1. Detect document changes since last discovery
2. Parse markdown to understand current state
3. Edit markdown based on user requests
4. Explain changes in chat responses
5. Handle merge/split/adjust commands

### Phase 5: Markdown Parser & T661 Generation
**Files to create/modify:**
- `backend/app/services/workspace_parser.py` - NEW: Parse markdown to structured data
- `backend/app/services/t661_service.py` - Generate from parsed markdown

**Markdown Parser Tasks:**
1. Parse project sections (## Project N: Name)
2. Extract dates from ### Dates section
3. Extract contributors from ### Contributors section
4. Extract document links (doc:uuid format)
5. Extract narratives (Why/Goal/How/Outcome)
6. Return list of structured `ParsedProject` objects

**T661 Generation Tasks:**
1. Use parser to get structured project data
2. Map narratives to T661 lines (Uncertainty→242, Investigation→244, Outcome→246)
3. Streamline narratives to CRA word limits (242: 350, 244: 700, 246: 350)
4. Validate CRA compliance (max 20 projects, required fields)
5. Generate T661 format output

### Phase 6: Frontend Updates
**Files to modify:**
- `frontend/src/pages/` - New workspace page
- `frontend/src/components/` - Markdown editor + chat panel

**Tasks:**
1. Create workspace page with split view (markdown + chat)
2. Markdown editor with syntax highlighting
3. Chat panel for AI interaction
4. Document change notifications
5. Finalize/export to T661 button

### Phase 7: Deprecate Old Project System
**Files to remove/modify:**
- `backend/app/api/v1/endpoints/projects.py` - Remove or deprecate
- `backend/app/schemas/project.py` - Keep only schemas used by workspace
- `backend/app/services/project_discovery_service.py` - Refactor for markdown generation
- `backend/alembic/versions/` - Migration to drop tables

**Tasks:**
1. Remove `/projects/*` endpoints
2. Drop `projects` table
3. Drop `project_document_tags` table
4. Drop `discovery_runs` table (if not needed for audit)
5. Clean up unused schemas and services

---

## Migration Strategy

### Existing Projects Table
- The `projects` and `project_document_tags` tables become **obsolete**
- Option 1: Delete tables after migration (clean break)
- Option 2: Keep tables read-only for historical reference
- Decision: **Clean break** - remove tables once workspace is stable

### Existing Project Data
- Any existing projects can be exported to markdown format during migration
- Or users can re-run discovery to regenerate from documents
- Historical data preserved in git/backups if needed

### Existing Conversations
- All existing conversations get `type="general"` by default
- No disruption to current functionality

### Existing Endpoints
- `/projects/*` endpoints deprecated
- New `/claims/{id}/workspace` endpoints replace them
- Frontend updated to use workspace workflow

---

## Open Questions

1. **Word limits during discovery** - Should AI try to stay within T661 limits from the start, or write freely and streamline at the end?

2. **Multiple workspaces** - Should users be able to have multiple workspace drafts? Or strictly one per claim?

3. **Collaboration** - Multiple users editing the same workspace? Lock mechanism?

4. **Export formats** - Besides T661, what other export formats needed?

---

## Architecture Summary

### What's Changing

| Before | After |
|--------|-------|
| `projects` table stores project data | Markdown in `workspace_md` is source of truth |
| `project_document_tags` links docs to projects | Document links embedded in markdown (`doc:uuid`) |
| Structured forms for editing | Direct markdown editing + chat-driven changes |
| T661 generated from database fields | T661 generated by parsing markdown |
| Multiple endpoints for CRUD | Single workspace endpoint + chat |

### Why Markdown?

1. **Flexibility**: AI and humans can both edit naturally
2. **Auditability**: Chat history shows all changes and reasoning
3. **Simplicity**: No sync issues between markdown and database
4. **Portability**: Easy to export, share, version control
5. **AI-Friendly**: LLMs work well with structured markdown

---

## Next Steps

1. Review this document
2. Finalize any open questions
3. Begin Phase 1 implementation (data model)
4. Iterate through phases 2-7

---

*Document created: Session discussion on collaborative SR&ED workflow*
*Updated: Removed Project table dependency - markdown is sole source of truth*
