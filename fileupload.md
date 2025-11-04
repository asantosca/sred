# Document Upload UI Specification (Condensed)
## Legal RAG Application - Upload Interface

---

## Quick Overview

**System Purpose**: Document upload interface for legal RAG application with matter-based organization, security controls, and version management.

**Upload Modes**: Quick (60s), Standard (2-3min), Detailed (5+min), Bulk (multiple files)

**Core Flow**: Select Mode → File & Matter → Classification → Security → Additional Details → Confirm → Upload

---

## Screen Flow Summary

```
[1. Mode Selection] 
    → [2. File & Matter]
        → [3. Classification + Type-Specific Fields]
            → [4. Security & Privilege]
                → [5. Additional Details - Expandable]
                    → [6. Review & Confirm]
                        → [7. Upload Progress]
                            → [8. Success]
```

---

## Screen 1: Mode Selection

**Purpose**: Choose upload approach

**Options**:
- **Quick Upload**: 5 required fields (Matter, Type, Date, Status, Confidentiality)
- **Standard Upload**: Quick + Privilege, Parties, Type-specific metadata (DEFAULT)
- **Detailed Upload**: Everything including version control, workflow, relationships
- **Bulk Upload**: Multiple files with shared/individual metadata

**UI Elements**: 4 cards, click to select mode

---

## Screen 2: File & Matter Selection

**Layout**: Drag-drop zone + Matter search

**Fields**:
| Field | Type | Required | Validation | Auto-Detect |
|-------|------|----------|------------|-------------|
| file | File upload | Yes | PDF/DOCX/DOC/TXT/MSG/EML, ≤50MB | - |
| matter_id | Searchable dropdown | Yes | User must have upload permission | - |

**Features**:
- Autocomplete matter search
- Show 4-5 recent matters
- Display matter details once selected
- File analysis progress bar
- [+ Create New Matter] button

---

## Screen 3: Document Classification

**Core Fields** (all document types):

| Field | Type | Required | Options/Format | Auto-Detect |
|-------|------|----------|----------------|-------------|
| document_type | Dropdown | Yes | Contract, Pleading, Correspondence, Discovery, Exhibit, Memo, Other | Filename pattern |
| document_title | Text(500) | Yes | Free text | From filename |
| document_date | Date | Yes | MM/DD/YYYY | OCR header/footer |
| document_status | Radio | Yes | Draft, Final, Executed, Filed | - |

**Type-Specific Field Sets**:

### Contract Fields
| Field | Type | Required | Format |
|-------|------|----------|--------|
| contract_type | Dropdown | No | Service Agreement, NDA, Employment, Lease, etc. |
| contract_value | Currency | No | Decimal(15,2) |
| contract_effective_date | Date | No | MM/DD/YYYY |
| contract_expiration_date | Date | No | MM/DD/YYYY |
| governing_law | Text(100) | No | Free text |

### Pleading Fields
| Field | Type | Required | Format |
|-------|------|----------|--------|
| pleading_type | Dropdown | Yes | Complaint, Answer, Motion, Brief, Order |
| court_jurisdiction | Text(255) | Yes | Free text |
| case_number | Text(100) | Yes | Free text |
| filing_date | Date | No | MM/DD/YYYY |
| judge_name | Text(255) | No | Free text |
| opposing_party | Text(255) | Yes | Free text |
| opposing_counsel | Text(255) | No | Free text |

### Correspondence Fields
| Field | Type | Required | Format |
|-------|------|----------|--------|
| correspondence_type | Dropdown | No | Email, Letter, Memo |
| author | Text(255) | Yes | Free text |
| recipient | Text(255) | Yes | Free text |
| cc | Text(255) | No | Free text |
| subject | Text(500) | No | Free text |

### Discovery Fields
| Field | Type | Required | Format |
|-------|------|----------|--------|
| discovery_type | Dropdown | Yes | Interrogatories, RFP, RFA, Deposition |
| propounding_party | Text(255) | No | Free text |
| responding_party | Text(255) | No | Free text |
| discovery_number | Text(100) | No | Free text |
| response_due_date | Date | No | MM/DD/YYYY |
| response_status | Dropdown | No | Pending, Partial, Complete |

### Exhibit Fields
| Field | Type | Required | Format |
|-------|------|----------|--------|
| exhibit_number | Text(100) | Yes | Free text |
| related_to_document_id | Document picker | No | UUID |

**UI Behavior**: Fields appear/hide based on document_type selection

---

## Screen 4: Security & Privilege

**Confidentiality Level** (required):

| Level | Access | Description |
|-------|--------|-------------|
| Standard Confidential | All team members on matter | Default level |
| Highly Confidential | Attorneys on matter only | Sensitive documents |
| Attorney Eyes Only | Lead attorneys & partners | Most sensitive |

**Privilege Designation** (optional checkboxes):
- Attorney-Client Privileged
- Work Product
- Confidential Settlement Communications

**Privilege Warning Modal**: Appears when any privilege checkbox selected
- Requires 2 confirmation checkboxes
- Explains legal requirements
- Must confirm before proceeding

**Fields**:
| Field | Type | Required | Values |
|-------|------|----------|--------|
| confidentiality_level | Radio | Yes | standard_confidential, highly_confidential, attorney_eyes_only |
| privilege_attorney_client | Checkbox | No | Boolean |
| privilege_work_product | Checkbox | No | Boolean |
| privilege_settlement | Checkbox | No | Boolean |

**Auto-computed**: `is_privileged = true` if any privilege checkbox = true

---

## Screen 5: Additional Details (Expandable Sections)

**Default State**: All sections collapsed

### Section A: Parties & Participants
| Field | Type | Required |
|-------|------|----------|
| author | Text(255) | No |
| recipient | Text(255) | No |
| opposing_counsel | Text(255) | No |

### Section B: Version Control
| Field | Type | Required | Conditional |
|-------|------|----------|-------------|
| is_new_version | Radio (Yes/No) | No | - |
| parent_document_id | Document picker | Conditional | If is_new_version=Yes |
| version_label | Text(100) | Conditional | If is_new_version=Yes |
| change_summary | Textarea | Conditional | If is_new_version=Yes |
| mark_superseded | Radio | Conditional | If is_new_version=Yes |

**Features**:
- Search for previous version
- Show similar documents in matter
- Auto-suggest version label (v2.0, v3.0, etc.)
- Option to mark previous as superseded or keep both current

### Section C: Workflow & Review
| Field | Type | Required | Conditional |
|-------|------|----------|-------------|
| needs_review | Radio (Yes/No) | No | - |
| assigned_to | User picker | Conditional | If needs_review=Yes |
| review_deadline | Date | Conditional | If needs_review=Yes |
| priority | Radio | Conditional | If needs_review=Yes |
| review_instructions | Textarea | No | - |

**Options**:
- Priority: Normal, High, Urgent
- User picker shows team members on matter

### Section D: Notes & Tags
| Field | Type | Required | Max |
|-------|------|----------|-----|
| internal_notes | Textarea | No | 5000 chars |
| tags | Text (comma-sep) | No | 50 tags |

**Features**:
- Suggested tags based on document content
- Tag autocomplete from existing tags

### Section E: Related Documents
| Field | Type | Required |
|-------|------|----------|
| related_documents | Multiple relationships | No |

**Relationship Types**:
- Amendment of / Amended by
- Exhibit to / Has exhibit
- Supersedes / Superseded by
- Response to / Has response
- Related to (general)

**UI**: [+ Add Related Document] opens modal with document search and relationship type selector

---

## Screen 6: Review & Confirmation

**Layout**: Summary of all entered data with [Edit] links

**Sections Displayed**:
1. File Details (filename, matter)
2. Classification (type, title, date, status, type-specific fields)
3. Security (confidentiality, privilege)
4. Version Control (if applicable)
5. Workflow (if applicable)
6. What Happens Next (bulleted list of actions)

**Final Confirmation**:
- Checkbox: "I confirm the information above is correct and I have authority to upload this document"
- Required before [Upload] button is enabled

**Fields**:
| Field | Type | Required |
|-------|------|----------|
| final_confirmation | Checkbox | Yes |

---

## Screen 7: Upload Progress

**Progress Steps** (shown sequentially):
1. Uploading file (0-100% progress bar)
2. Creating database record
3. Extracting text
4. Generating AI embeddings
5. Indexing for search
6. Completing workflow tasks

**UI**: Progress bars for each step, estimated time remaining

**Feature**: "Continue Working" button allows navigating away

---

## Screen 8: Success Confirmation

**Display**:
- Success message with document title
- Summary of what was done
- Document ID and direct link
- Notifications sent (if any)
- Next steps

**Actions**:
- [View Document]
- [Upload Another]
- [Back to Matter]

---

## Bulk Upload Flow

### Screen: Bulk Upload

**Step 1**: Select matter (same as single upload)

**Step 2**: Upload multiple files (drag-drop, up to 50 files)

**Step 3**: Set common metadata
- Document Type (or "Mixed" to set individually)
- Document Status
- Confidentiality Level
- Privilege checkboxes

**Step 4**: Review & customize individual files
- List of all uploaded files
- Auto-detected metadata for each
- [Edit] button per file
- Warning icons for files missing required fields
- Can remove files from list

**Alternative**: Upload Excel with metadata
- [Download Template] provides Excel file
- Columns: Filename, Document_Type, Document_Date, Document_Status, etc.
- [Upload Metadata File] reads Excel and maps to files

**Excel Template Columns**:
Filename | Document_Type | Document_Title | Document_Date | Document_Status | Confidentiality | Privilege_AC | Privilege_WP | Author | Internal_Notes | Tags

**Step 5**: Upload all (shows progress for each file)

---

## Complete Field Reference

### Universal Fields (All Documents)

| Field Name | DB Column | Type | Length | Required | Default | Validation |
|------------|-----------|------|--------|----------|---------|------------|
| File | - | File | - | Yes | - | Extensions, size ≤50MB |
| Matter | matter_id | UUID | - | Yes | - | User has access |
| Document Type | document_type | VARCHAR | 100 | Yes | - | Valid type |
| Document Title | document_title | VARCHAR | 500 | Yes | From filename | 3-500 chars |
| Document Date | document_date | DATE | - | Yes | - | Valid date |
| Document Status | document_status | VARCHAR | 50 | Yes | 'final' | Valid status |
| Confidentiality | confidentiality_level | VARCHAR | 50 | Yes | 'standard_confidential' | Valid level |

### Security Fields

| Field Name | DB Column | Type | Required | Default |
|------------|-----------|------|----------|---------|
| Attorney-Client | privilege_attorney_client | BOOLEAN | No | false |
| Work Product | privilege_work_product | BOOLEAN | No | false |
| Settlement Comm | privilege_settlement | BOOLEAN | No | false |
| Is Privileged (computed) | is_privileged | BOOLEAN | - | false |

### Version Fields

| Field Name | DB Column | Type | Required | Conditional |
|------------|-----------|------|----------|-------------|
| New Version | - | Radio | No | - |
| Parent Document | parent_document_id | UUID | Conditional | If new version |
| Version Label | version_label | VARCHAR(100) | Conditional | If new version |
| Change Summary | change_summary | TEXT | No | - |
| Version Number | version_number | INTEGER | - | Auto-increment |
| Is Current | is_current_version | BOOLEAN | - | true |
| Effective Date | effective_date | DATE | - | Today |
| Superseded Date | superseded_date | DATE | - | NULL |
| Root Document | root_document_id | UUID | - | Auto-set |

### Workflow Fields

| Field Name | DB Column | Type | Required | Conditional |
|------------|-----------|------|----------|-------------|
| Needs Review | - | Radio | No | - |
| Assigned To | assigned_to | UUID | Conditional | If needs review |
| Review Deadline | review_deadline | DATE | Conditional | If needs review |
| Priority | priority | VARCHAR(20) | Conditional | If needs review |
| Review Instructions | review_instructions | TEXT | No | - |
| Review Status | review_status | VARCHAR(50) | - | 'not_required' |

### Metadata Fields

| Field Name | DB Column | Type | Max | Required |
|------------|-----------|------|-----|----------|
| Internal Notes | internal_notes | TEXT | 5000 | No |
| Tags | tags | TEXT[] | 50 tags | No |

### Type-Specific Fields

**Contract**: contract_type, contract_value, contract_effective_date, contract_expiration_date, governing_law

**Pleading**: pleading_type, court_jurisdiction, case_number, filing_date, judge_name, opposing_party, opposing_counsel

**Correspondence**: correspondence_type, author, recipient, cc, subject

**Discovery**: discovery_type, propounding_party, responding_party, discovery_number, response_due_date, response_status

**Exhibit**: exhibit_number, related_to_document_id

---

## Database Schema

### Table: matters

```sql
CREATE TABLE matters (
    matter_id UUID PRIMARY KEY,
    matter_number VARCHAR(50) UNIQUE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    case_type VARCHAR(100) NOT NULL,
    matter_status VARCHAR(50) DEFAULT 'active',
    description TEXT,
    opened_date DATE NOT NULL,
    closed_date DATE,
    lead_attorney_user_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID NOT NULL
);

CREATE INDEX idx_matter_number ON matters(matter_number);
CREATE INDEX idx_client_name ON matters(client_name);
CREATE INDEX idx_matter_status ON matters(matter_status);
```

### Table: documents

```sql
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    matter_id UUID NOT NULL REFERENCES matters(matter_id),
    
    -- File Info
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    mime_type VARCHAR(100),
    
    -- Classification
    document_type VARCHAR(100) NOT NULL,
    document_subtype VARCHAR(100),
    document_title VARCHAR(500) NOT NULL,
    document_date DATE NOT NULL,
    date_received DATE,
    filed_date DATE,
    document_status VARCHAR(50) NOT NULL,
    
    -- Version Control
    is_current_version BOOLEAN DEFAULT TRUE,
    version_label VARCHAR(100),
    version_number INTEGER DEFAULT 1,
    parent_document_id UUID REFERENCES documents(document_id),
    root_document_id UUID REFERENCES documents(document_id),
    effective_date DATE,
    superseded_date DATE,
    change_summary TEXT,
    
    -- Security
    confidentiality_level VARCHAR(50) NOT NULL DEFAULT 'standard_confidential',
    is_privileged BOOLEAN DEFAULT FALSE,
    privilege_attorney_client BOOLEAN DEFAULT FALSE,
    privilege_work_product BOOLEAN DEFAULT FALSE,
    privilege_settlement BOOLEAN DEFAULT FALSE,
    
    -- Parties
    author VARCHAR(255),
    recipient VARCHAR(255),
    opposing_counsel VARCHAR(255),
    opposing_party VARCHAR(255),
    
    -- Court Info (Pleadings)
    court_jurisdiction VARCHAR(255),
    case_number VARCHAR(100),
    judge_name VARCHAR(255),
    
    -- Contract Info
    contract_type VARCHAR(100),
    contract_value DECIMAL(15,2),
    contract_effective_date DATE,
    contract_expiration_date DATE,
    governing_law VARCHAR(100),
    
    -- Discovery Info
    discovery_type VARCHAR(100),
    propounding_party VARCHAR(255),
    responding_party VARCHAR(255),
    discovery_number VARCHAR(100),
    response_due_date DATE,
    response_status VARCHAR(50),
    
    -- Exhibit Info
    exhibit_number VARCHAR(100),
    
    -- Correspondence Info
    correspondence_type VARCHAR(50),
    cc VARCHAR(255),
    subject VARCHAR(500),
    
    -- Workflow
    review_status VARCHAR(50) DEFAULT 'not_required',
    assigned_to UUID,
    review_deadline DATE,
    priority VARCHAR(20) DEFAULT 'normal',
    review_instructions TEXT,
    
    -- Metadata
    internal_notes TEXT,
    tags TEXT[],
    
    -- Processing
    processing_status VARCHAR(50) DEFAULT 'pending',
    text_extracted BOOLEAN DEFAULT FALSE,
    indexed_for_search BOOLEAN DEFAULT FALSE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID NOT NULL
);

CREATE INDEX idx_matter_documents ON documents(matter_id, document_date DESC);
CREATE INDEX idx_document_type ON documents(document_type);
CREATE INDEX idx_current_versions ON documents(matter_id, is_current_version) WHERE is_current_version = TRUE;
CREATE INDEX idx_version_chains ON documents(root_document_id, version_number);
CREATE INDEX idx_file_hash ON documents(file_hash);
CREATE INDEX idx_privilege ON documents(is_privileged) WHERE is_privileged = TRUE;
CREATE INDEX idx_review_status ON documents(review_status, assigned_to);
```

### Table: users

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(255) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    user_role VARCHAR(50) NOT NULL,
    is_attorney BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_user_role ON users(user_role);
CREATE INDEX idx_is_attorney ON users(is_attorney);
```

### Table: matter_access

```sql
CREATE TABLE matter_access (
    access_id UUID PRIMARY KEY,
    matter_id UUID NOT NULL REFERENCES matters(matter_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    access_role VARCHAR(50) NOT NULL,
    can_upload BOOLEAN DEFAULT TRUE,
    can_edit BOOLEAN DEFAULT TRUE,
    can_delete BOOLEAN DEFAULT FALSE,
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by UUID NOT NULL REFERENCES users(user_id),
    UNIQUE (matter_id, user_id)
);

CREATE INDEX idx_user_matters ON matter_access(user_id);
CREATE INDEX idx_matter_users ON matter_access(matter_id);
```

### Table: document_relationships

```sql
CREATE TABLE document_relationships (
    relationship_id UUID PRIMARY KEY,
    source_document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    target_document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL
);

CREATE INDEX idx_source_relationships ON document_relationships(source_document_id);
CREATE INDEX idx_target_relationships ON document_relationships(target_document_id);
```

### Table: document_access_log

```sql
CREATE TABLE document_access_log (
    log_id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id),
    action VARCHAR(50) NOT NULL,
    access_timestamp TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255)
);

CREATE INDEX idx_document_access ON document_access_log(document_id, access_timestamp DESC);
CREATE INDEX idx_user_activity ON document_access_log(user_id, access_timestamp DESC);
```

### Table: upload_sessions

```sql
CREATE TABLE upload_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    matter_id UUID REFERENCES matters(matter_id),
    upload_mode VARCHAR(50) NOT NULL,
    current_step INTEGER DEFAULT 1,
    session_data JSONB,
    status VARCHAR(50) DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_user_sessions ON upload_sessions(user_id, status);
```

### Table: document_processing_queue

```sql
CREATE TABLE document_processing_queue (
    queue_id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    processing_step VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_document_processing ON document_processing_queue(document_id, processing_step);
CREATE INDEX idx_queue_status ON document_processing_queue(status, created_at);
```

---

## Validation Rules

### File Validation
- **Max Size**: 50MB (52,428,800 bytes)
- **Allowed Extensions**: .pdf, .docx, .doc, .txt, .msg, .eml
- **Allowed MIME Types**: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/msword, text/plain, application/vnd.ms-outlook, message/rfc822

### Required Field Logic

**Always Required**:
- matter_id
- document_type
- document_title
- document_date
- document_status
- confidentiality_level

**Conditionally Required**:
- If document_type = "pleading": court_jurisdiction, case_number, opposing_party
- If document_type = "correspondence": author, recipient
- If document_type = "discovery": discovery_type
- If document_type = "exhibit": exhibit_number
- If is_new_version = true: parent_document_id, version_label
- If needs_review = true: assigned_to, review_deadline

**Date Validation**:
- All dates must be valid MM/DD/YYYY format
- contract_expiration_date must be ≥ contract_effective_date
- review_deadline must be future date

**Privilege Validation**:
- If any privilege checkbox = true, user must check both confirmation boxes in warning modal
- Automatically set is_privileged = true when any privilege checkbox = true

**Text Length**:
- document_title: 3-500 characters
- internal_notes: max 5000 characters
- change_summary: max 2000 characters
- tags: max 50 tags, each max 50 characters

---

## Smart Features

### Auto-Detection

**Filename Patterns**:
- "*Agreement*.pdf" → Contract
- "Complaint*.pdf" → Pleading (Complaint)
- "Letter*.pdf" → Correspondence
- "Interrogatories*.pdf" → Discovery

**Date Extraction**: OCR scan first 3 pages for dates in headers/footers/signature blocks

**Party Extraction**: OCR letterhead, captions, signature blocks

### Duplicate Detection
- Calculate SHA-256 hash on upload
- Check if hash exists in database
- If found, show warning with options: new version / different document / duplicate

### Similar Document Suggestions
- Search matter for documents with similar filenames
- Offer to link as version

### Smart Recommendations
- Based on user's historical patterns for matter/client/document type
- Suggest confidentiality level, assigned reviewer, priority
- [Apply These Defaults] button

### Draft Saving
- [Save Draft] button in Detailed mode
- Store in upload_sessions table
- Resume later from "Drafts" section

---

## Implementation Priority

**Phase 1 (MVP)**:
- Screens 2-4: File, Classification, Security
- Core tables: matters, documents, users, matter_access
- Single file upload only
- Basic validation

**Phase 2**:
- Screen 5: Additional Details (all sections)
- Tables: document_relationships, upload_sessions
- Version control
- Workflow assignment

**Phase 3**:
- Bulk upload
- Excel import
- Auto-detection features
- Smart recommendations

**Phase 4**:
- Advanced features
- Mobile interface
- Enhanced validation

---

## Key Enums and Constants

### Document Types
Contract, Pleading, Correspondence, Discovery, Exhibit, Memo, Research, Other

### Document Status
Draft, Final, Executed, Filed

### Confidentiality Levels
standard_confidential, highly_confidential, attorney_eyes_only

### Review Status
not_required, needs_review, under_review, reviewed, approved, rejected

### Priority Levels
normal, high, urgent

### User Roles
partner, attorney, associate, paralegal, legal_assistant, admin

### Access Roles (Matter)
lead_attorney, associate, paralegal, read_only

### Processing Steps
text_extraction, ocr, embedding_generation, vector_indexing, metadata_enhancement

### Relationship Types
amendment_of, amended_by, exhibit_to, has_exhibit, supersedes, superseded_by, response_to, has_response, related_to

---

## Sample Data Flow

**User uploads Service Agreement**:

1. Screen 1: Select "Standard Upload"
2. Screen 2: Upload "ServiceAgreement_Final.pdf", select matter "2024-042-ACME"
3. Screen 3:
   - Type: Contract
   - Title: Service Agreement (auto-detected)
   - Date: 01/15/2024 (auto-detected via OCR)
   - Status: Final
   - Contract Type: Service Agreement
   - Contract Value: $125,000
   - Effective: 01/15/2024, Expires: 01/14/2025
4. Screen 4:
   - Confidentiality: Standard Confidential
   - Privilege: None
5. Screen 5 (Additional Details):
   - Version Control: Yes, replaces "ServiceAgreement_v1.pdf"
   - Version Label: v2.0
   - Change Summary: "Modified payment terms in Section 3.2"
   - Workflow: Assign to Sarah Chen, deadline 01/25/2024
6. Screen 6: Review and confirm
7. Upload creates record in documents table:

```json
{
  "document_id": "650e8400...",
  "matter_id": "550e8400...",
  "filename": "ServiceAgreement_Final_2024.pdf",
  "document_type": "contract",
  "document_title": "Service Agreement",
  "document_date": "2024-01-15",
  "document_status": "final",
  "is_current_version": true,
  "version_label": "v2.0",
  "version_number": 2,
  "parent_document_id": "[v1.0 UUID]",
  "confidentiality_level": "standard_confidential",
  "contract_value": 125000.00,
  "review_status": "needs_review",
  "assigned_to": "[Sarah Chen UUID]",
  "review_deadline": "2024-01-25",
  "created_by": "[Current user UUID]"
}
```

8. Background process:
   - Queues text_extraction in document_processing_queue
   - Extracts text from PDF
   - Generates embeddings
   - Indexes in vector database
   - Updates parent document: is_current_version = false, superseded_date = today
   - Creates entry in document_access_log
   - Sends notification to Sarah Chen

---

## Error Handling

**File Validation Errors**:
- File too large → "File exceeds 50MB limit. Please compress or split."
- Invalid type → "File type not supported. Please upload PDF, DOCX, DOC, TXT, MSG, or EML."

**Permission Errors**:
- No matter access → "You don't have permission to upload to this matter. Contact lead attorney."
- No upload permission → "You have read-only access to this matter."

**Validation Errors**:
- Missing required fields → "Please complete required fields: [list]"
- Invalid date → "Please enter a valid date in MM/DD/YYYY format"
- Invalid contract dates → "Expiration date must be on or after effective date"

**Upload Errors**:
- Network error → "Upload failed. Check connection and retry."
- Server error → "Server error. Contact support if problem persists."
- Storage error → "Failed to save file. Retry or contact support."

---

## Summary

**8 Main Screens**: Mode Selection → File & Matter → Classification → Security → Additional Details → Review → Progress → Success

**60+ Fields**: Type-specific fields appear based on document_type selection

**8 Database Tables**: matters, documents, users, matter_access, document_relationships, document_access_log, upload_sessions, document_processing_queue

**Key Features**: Auto-detection, version control, privilege warnings, workflow assignment, bulk upload, smart recommendations

**Validation**: File type/size, required fields by type, conditional requirements, privilege confirmations

This condensed spec provides all essential information for implementation while being easier to parse than the full version.