# Phase 1: Database Schema Changes

## New Tables to Add

### 1. Projects Table

```sql
-- Add to backend/alembic/versions/xxx_add_projects.py

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Project Identity
    project_name VARCHAR(255) NOT NULL,
    project_code VARCHAR(50),  -- e.g., "FRAUD-DET", "ML-OPT"
    
    -- SR&ED Classification
    sred_confidence_score DECIMAL(3,2),  -- 0.00 to 1.00
    project_status VARCHAR(50) DEFAULT 'discovered',  
    -- Values: 'discovered', 'user_reviewed', 'approved', 'rejected', 'merged'
    
    -- Discovery Metadata
    discovery_method VARCHAR(50),  -- 'ai_clustering', 'user_created', 'manual'
    ai_suggested BOOLEAN DEFAULT false,
    user_confirmed BOOLEAN DEFAULT false,
    
    -- Temporal Info
    project_start_date DATE,
    project_end_date DATE,
    
    -- Team Info
    team_members TEXT[],  -- Array of names extracted from docs
    team_size INTEGER,
    
    -- Financial
    estimated_spend DECIMAL(15,2),
    eligible_expenditures DECIMAL(15,2),
    
    -- SR&ED Signals (aggregated from documents)
    uncertainty_signal_count INTEGER DEFAULT 0,
    systematic_signal_count INTEGER DEFAULT 0,
    failure_signal_count INTEGER DEFAULT 0,
    advancement_signal_count INTEGER DEFAULT 0,
    
    -- AI-Generated Summaries
    ai_summary TEXT,
    uncertainty_summary TEXT,  -- For T661 Line 242
    work_summary TEXT,         -- For T661 Line 244
    advancement_summary TEXT,  -- For T661 Line 246
    
    -- Narrative Status
    narrative_status VARCHAR(50) DEFAULT 'not_started',
    -- Values: 'not_started', 'draft', 'complete', 'needs_revision'
    narrative_line_242 TEXT,
    narrative_line_244 TEXT,
    narrative_line_246 TEXT,
    narrative_word_count_242 INTEGER,
    narrative_word_count_244 INTEGER,
    narrative_word_count_246 INTEGER,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    -- Indexes
    CONSTRAINT fk_claim FOREIGN KEY (claim_id) REFERENCES claims(id),
    CONSTRAINT fk_company FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX idx_projects_claim ON projects(claim_id);
CREATE INDEX idx_projects_company ON projects(company_id);
CREATE INDEX idx_projects_status ON projects(project_status);
CREATE INDEX idx_projects_confidence ON projects(sred_confidence_score DESC);
```

### 2. Document Tags Table (Junction Table)

```sql
-- Many-to-many: Documents <-> Projects

CREATE TABLE document_project_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Tag Metadata
    tagged_by VARCHAR(50) NOT NULL,  -- 'ai' or 'user'
    confidence_score DECIMAL(3,2),   -- If tagged by AI
    
    -- Granular Tagging (for multi-project documents)
    page_ranges TEXT,  -- JSON: [{"start": 1, "end": 5}, {"start": 10, "end": 15}]
    relevance_notes TEXT,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    -- Constraints
    UNIQUE(document_id, project_id)
);

CREATE INDEX idx_doc_tags_document ON document_project_tags(document_id);
CREATE INDEX idx_doc_tags_project ON document_project_tags(project_id);
CREATE INDEX idx_doc_tags_confidence ON document_project_tags(confidence_score DESC);
```

### 3. Project Discovery History Table

```sql
-- Track discovery runs and their results

CREATE TABLE project_discovery_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    
    -- Discovery Parameters
    total_documents_analyzed INTEGER,
    discovery_algorithm VARCHAR(50),  -- 'temporal_topic_clustering', etc.
    parameters JSONB,  -- Algorithm-specific params
    
    -- Results
    projects_discovered INTEGER,
    high_confidence_count INTEGER,
    medium_confidence_count INTEGER,
    low_confidence_count INTEGER,
    
    -- Execution
    execution_time_seconds DECIMAL(10,2),
    status VARCHAR(50),  -- 'running', 'completed', 'failed'
    error_message TEXT,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_discovery_claim ON project_discovery_runs(claim_id);
CREATE INDEX idx_discovery_created ON project_discovery_runs(created_at DESC);
```

### 4. Document Change Log

```sql
-- Track when documents added to claims (for change detection)

CREATE TABLE document_upload_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    
    -- Batch Info
    batch_number INTEGER,  -- Incremental per claim
    document_count INTEGER,
    total_size_bytes BIGINT,
    
    -- Analysis Status
    analyzed BOOLEAN DEFAULT false,
    analysis_run_id UUID REFERENCES project_discovery_runs(id),
    
    -- Impact Summary (JSON)
    impact_summary JSONB,
    -- Structure:
    -- {
    --   "new_projects_discovered": 2,
    --   "docs_added_to_existing": {"project_id": count, ...},
    --   "narrative_impacts": [{"project_id": "...", "severity": "high"}, ...]
    -- }
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_upload_batch_claim ON document_upload_batches(claim_id);
CREATE INDEX idx_upload_batch_analyzed ON document_upload_batches(analyzed);
```

## Modifications to Existing Tables

### 1. Extend Document Model

```sql
-- Add to existing documents table (migration)

ALTER TABLE documents
  ADD COLUMN sred_signals JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN temporal_metadata JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN upload_batch_id UUID REFERENCES document_upload_batches(id);

-- sred_signals structure:
-- {
--   "uncertainty_keywords": 5,
--   "systematic_keywords": 12,
--   "failure_keywords": 8,
--   "novel_keywords": 3,
--   "score": 0.73
-- }

-- temporal_metadata structure:
-- {
--   "date_references": ["2024-03-15", "2024-04-20"],
--   "team_members": ["Sarah Kim", "Mike Chen"],
--   "project_names": ["fraud-detection", "ML-optimization"]
-- }

CREATE INDEX idx_documents_batch ON documents(upload_batch_id);
CREATE INDEX idx_documents_sred_score ON documents((sred_signals->>'score'));
```

### 2. Extend Document Chunks

```sql
-- Add to existing document_chunks table

ALTER TABLE document_chunks
  ADD COLUMN sred_keyword_matches JSONB DEFAULT '{}'::jsonb;

-- Structure:
-- {
--   "uncertainty": ["uncertain", "unknown"],
--   "systematic": ["hypothesis", "experiment"],
--   "failure": ["failed", "didn't work"],
--   "advancement": ["novel", "breakthrough"]
-- }
```

## Alembic Migration Example

```python
# backend/alembic/versions/xxx_add_project_discovery.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_project_discovery'
down_revision = 'previous_migration_id'

def upgrade():
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('claim_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_name', sa.String(255), nullable=False),
        sa.Column('project_code', sa.String(50)),
        sa.Column('sred_confidence_score', sa.DECIMAL(3,2)),
        sa.Column('project_status', sa.String(50), default='discovered'),
        # ... (add all other columns)
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_projects_claim', 'projects', ['claim_id'])
    op.create_index('idx_projects_company', 'projects', ['company_id'])
    # ... (other indexes)
    
    # Create document_project_tags table
    op.create_table('document_project_tags', ...)
    
    # Create project_discovery_runs table
    op.create_table('project_discovery_runs', ...)
    
    # Create document_upload_batches table
    op.create_table('document_upload_batches', ...)
    
    # Extend existing tables
    op.add_column('documents', sa.Column('sred_signals', postgresql.JSONB))
    op.add_column('documents', sa.Column('temporal_metadata', postgresql.JSONB))
    op.add_column('documents', sa.Column('upload_batch_id', postgresql.UUID))
    
    op.add_column('document_chunks', sa.Column('sred_keyword_matches', postgresql.JSONB))

def downgrade():
    # Remove in reverse order
    op.drop_column('document_chunks', 'sred_keyword_matches')
    op.drop_column('documents', 'upload_batch_id')
    op.drop_column('documents', 'temporal_metadata')
    op.drop_column('documents', 'sred_signals')
    
    op.drop_table('document_upload_batches')
    op.drop_table('project_discovery_runs')
    op.drop_table('document_project_tags')
    op.drop_table('projects')
```

## SQLAlchemy Models

Add these to `backend/app/models/models.py`:

```python
from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    project_name = Column(String(255), nullable=False)
    project_code = Column(String(50))
    
    sred_confidence_score = Column(DECIMAL(3,2))
    project_status = Column(String(50), default="discovered")
    
    discovery_method = Column(String(50))
    ai_suggested = Column(Boolean, default=False)
    user_confirmed = Column(Boolean, default=False)
    
    project_start_date = Column(Date)
    project_end_date = Column(Date)
    
    team_members = Column(ARRAY(Text))
    team_size = Column(Integer)
    
    estimated_spend = Column(DECIMAL(15,2))
    eligible_expenditures = Column(DECIMAL(15,2))
    
    uncertainty_signal_count = Column(Integer, default=0)
    systematic_signal_count = Column(Integer, default=0)
    failure_signal_count = Column(Integer, default=0)
    advancement_signal_count = Column(Integer, default=0)
    
    ai_summary = Column(Text)
    uncertainty_summary = Column(Text)
    work_summary = Column(Text)
    advancement_summary = Column(Text)
    
    narrative_status = Column(String(50), default="not_started")
    narrative_line_242 = Column(Text)
    narrative_line_244 = Column(Text)
    narrative_line_246 = Column(Text)
    narrative_word_count_242 = Column(Integer)
    narrative_word_count_244 = Column(Integer)
    narrative_word_count_246 = Column(Integer)
    
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    claim = relationship("Claim", back_populates="projects")
    company = relationship("Company")
    document_tags = relationship("DocumentProjectTag", back_populates="project", cascade="all, delete-orphan")


class DocumentProjectTag(Base):
    __tablename__ = "document_project_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    tagged_by = Column(String(50), nullable=False)  # 'ai' or 'user'
    confidence_score = Column(DECIMAL(3,2))
    
    page_ranges = Column(Text)  # JSON string
    relevance_notes = Column(Text)
    
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    document = relationship("Document", back_populates="project_tags")
    project = relationship("Project", back_populates="document_tags")


class ProjectDiscoveryRun(Base):
    __tablename__ = "project_discovery_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    
    total_documents_analyzed = Column(Integer)
    discovery_algorithm = Column(String(50))
    parameters = Column(JSONB)
    
    projects_discovered = Column(Integer)
    high_confidence_count = Column(Integer)
    medium_confidence_count = Column(Integer)
    low_confidence_count = Column(Integer)
    
    execution_time_seconds = Column(DECIMAL(10,2))
    status = Column(String(50))
    error_message = Column(Text)
    
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    claim = relationship("Claim")


class DocumentUploadBatch(Base):
    __tablename__ = "document_upload_batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    
    batch_number = Column(Integer)
    document_count = Column(Integer)
    total_size_bytes = Column(BigInteger)
    
    analyzed = Column(Boolean, default=False)
    analysis_run_id = Column(UUID(as_uuid=True), ForeignKey("project_discovery_runs.id"))
    
    impact_summary = Column(JSONB)
    
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    claim = relationship("Claim")
    analysis_run = relationship("ProjectDiscoveryRun")


# Update existing models with new relationships

# In Claim model, add:
class Claim(Base):
    # ... existing fields ...
    projects = relationship("Project", back_populates="claim", cascade="all, delete-orphan")

# In Document model, add:
class Document(Base):
    # ... existing fields ...
    sred_signals = Column(JSONB, default={})
    temporal_metadata = Column(JSONB, default={})
    upload_batch_id = Column(UUID(as_uuid=True), ForeignKey("document_upload_batches.id"))
    
    project_tags = relationship("DocumentProjectTag", back_populates="document", cascade="all, delete-orphan")
    upload_batch = relationship("DocumentUploadBatch")

# In DocumentChunk model, add:
class DocumentChunk(Base):
    # ... existing fields ...
    sred_keyword_matches = Column(JSONB, default={})
```

## Next Steps

After running this migration:

1. Test that all tables created successfully
2. Verify foreign key constraints work
3. Test RLS policies still work with new tables
4. Update Pydantic schemas in `backend/app/schemas/`
5. Create API endpoints for projects
