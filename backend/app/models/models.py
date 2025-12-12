# app/models/models.py - Fixed database models for BC Legal Tech

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, Date, BigInteger, DECIMAL, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TSVECTOR
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.sql import func
import uuid
from pgvector.sqlalchemy import Vector

from app.db.session import Base

class Company(Base):
    """Company/Tenant model"""
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=True)
    plan_tier = Column(String(50), default="starter")
    tenancy_type = Column(String(50), default="shared_rls")
    settings = Column(JSON, default=dict)
    subscription_status = Column(String(50), default="trial")
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="company", cascade="all, delete-orphan")

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    profile_picture = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    user_groups = relationship("UserGroup", foreign_keys="UserGroup.user_id", back_populates="user", cascade="all, delete-orphan")

class Group(Base):
    """Group model for RBAC"""
    __tablename__ = "groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    permissions_json = Column(JSON, nullable=False, default=list)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="groups")
    user_groups = relationship("UserGroup", back_populates="group", cascade="all, delete-orphan")

class UserGroup(Base):
    """Many-to-many relationship between users and groups"""
    __tablename__ = "user_groups"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), primary_key=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    # Fixed relationships with explicit foreign_keys
    user = relationship("User", foreign_keys=[user_id], back_populates="user_groups")
    group = relationship("Group", back_populates="user_groups")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])

class RefreshToken(Base):
    """Refresh token model for JWT token rotation"""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")

class PasswordResetToken(Base):
    """Password reset token model for secure password resets"""
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")

class Matter(Base):
    """Matter/Case model for organizing documents and work"""
    __tablename__ = "matters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    matter_number = Column(String(50), nullable=False)
    client_name = Column(String(255), nullable=False)
    matter_type = Column(String(100), nullable=False)
    matter_status = Column(String(50), nullable=False, default="active")
    description = Column(Text, nullable=True)
    
    # Dates
    opened_date = Column(Date, nullable=False)
    closed_date = Column(Date, nullable=True)
    
    # Lead attorney
    lead_attorney_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    company = relationship("Company")
    lead_attorney = relationship("User", foreign_keys=[lead_attorney_user_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    matter_access = relationship("MatterAccess", back_populates="matter", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="matter", cascade="all, delete-orphan")

class MatterAccess(Base):
    """User access control for matters"""
    __tablename__ = "matter_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id = Column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    access_role = Column(String(50), nullable=False)  # lead_attorney, associate, paralegal, read_only
    
    # Permissions
    can_upload = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=True)
    can_delete = Column(Boolean, default=False)
    
    # Audit fields
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    matter = relationship("Matter", back_populates="matter_access")
    user = relationship("User", foreign_keys=[user_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])

class Document(Base):
    """Document metadata and file information"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id = Column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=False)
    
    # File Information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_extension = Column(String(10), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    storage_path = Column(String(1000), nullable=False)
    file_hash = Column(String(64), nullable=False)
    mime_type = Column(String(100), nullable=True)
    
    # Classification
    document_type = Column(String(100), nullable=False)
    document_subtype = Column(String(100), nullable=True)
    document_title = Column(String(500), nullable=False)
    document_date = Column(Date, nullable=False)
    date_received = Column(Date, nullable=True)
    filed_date = Column(Date, nullable=True)
    document_status = Column(String(50), nullable=False)
    
    # Version Control
    is_current_version = Column(Boolean, default=True)
    version_label = Column(String(100), nullable=True)
    version_number = Column(Integer, default=1)
    parent_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    root_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    effective_date = Column(Date, nullable=True)
    superseded_date = Column(Date, nullable=True)
    change_summary = Column(Text, nullable=True)
    
    # Security
    confidentiality_level = Column(String(50), nullable=False, default="standard_confidential")
    is_privileged = Column(Boolean, default=False)
    privilege_attorney_client = Column(Boolean, default=False)
    privilege_work_product = Column(Boolean, default=False)
    privilege_settlement = Column(Boolean, default=False)
    
    # Parties
    author = Column(String(255), nullable=True)
    recipient = Column(String(255), nullable=True)
    opposing_counsel = Column(String(255), nullable=True)
    opposing_party = Column(String(255), nullable=True)
    
    # Court Info (for pleadings)
    court_jurisdiction = Column(String(255), nullable=True)
    case_number = Column(String(100), nullable=True)
    judge_name = Column(String(255), nullable=True)
    
    # Contract Info
    contract_type = Column(String(100), nullable=True)
    contract_value = Column(DECIMAL(15, 2), nullable=True)
    contract_effective_date = Column(Date, nullable=True)
    contract_expiration_date = Column(Date, nullable=True)
    governing_law = Column(String(100), nullable=True)
    
    # Discovery Info
    discovery_type = Column(String(100), nullable=True)
    propounding_party = Column(String(255), nullable=True)
    responding_party = Column(String(255), nullable=True)
    discovery_number = Column(String(100), nullable=True)
    response_due_date = Column(Date, nullable=True)
    response_status = Column(String(50), nullable=True)
    
    # Exhibit Info
    exhibit_number = Column(String(100), nullable=True)
    
    # Correspondence Info
    correspondence_type = Column(String(50), nullable=True)
    cc = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=True)
    
    # Workflow
    review_status = Column(String(50), default="not_required")
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_deadline = Column(Date, nullable=True)
    priority = Column(String(20), default="normal")
    review_instructions = Column(Text, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    
    # Processing
    processing_status = Column(String(50), default="pending")
    text_extracted = Column(Boolean, default=False)
    indexed_for_search = Column(Boolean, default=False)

    # Text Extraction (for RAG pipeline)
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    extraction_method = Column(String(50), nullable=True)
    extraction_date = Column(DateTime(timezone=True), nullable=True)
    extraction_error = Column(Text, nullable=True)

    # OCR Processing (for scanned PDFs)
    ocr_applied = Column(Boolean, default=False)
    ocr_engine = Column(String(50), nullable=True)  # 'textract'
    ocr_pages_processed = Column(Integer, nullable=True)
    ocr_confidence_avg = Column(Float, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    matter = relationship("Matter", back_populates="documents")
    parent_document = relationship("Document", remote_side=[id], foreign_keys=[parent_document_id])
    root_document = relationship("Document", remote_side=[id], foreign_keys=[root_document_id])
    assigned_to_user = relationship("User", foreign_keys=[assigned_to])
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    """Document chunks for RAG vector search"""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # Using pgvector's Vector type for proper vector(1536) support
    # Deferred loading to avoid type registration issues until needed
    embedding = deferred(Column(Vector(1536), nullable=True))
    embedding_model = Column(String(100), nullable=True)
    # Full-text search vector for hybrid search (BM25 keyword matching)
    # Auto-populated by database trigger on insert/update
    search_vector = deferred(Column(TSVECTOR, nullable=True))
    chunk_metadata = Column("metadata", JSON, nullable=True)
    token_count = Column(Integer, nullable=True)
    char_count = Column(Integer, nullable=False)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")


class DocumentEvent(Base):
    """Timeline events extracted from documents"""
    __tablename__ = "document_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    matter_id = Column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True)

    # Event data
    event_date = Column(Date, nullable=False)
    event_description = Column(Text, nullable=False)

    # Date precision and confidence
    date_precision = Column(String(10), nullable=False, default="day")  # day, month, year, unknown
    confidence = Column(String(10), nullable=False, default="high")  # high, medium, low
    raw_date_text = Column(String(255), nullable=True)  # original text from document

    # User overrides
    is_user_created = Column(Boolean, default=False)
    is_user_modified = Column(Boolean, default=False)
    user_notes = Column(Text, nullable=True)

    # Versioning - track which document version this came from
    document_version = Column(Integer, nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    company = relationship("Company")
    matter = relationship("Matter")
    document = relationship("Document")
    chunk = relationship("DocumentChunk")
    created_by_user = relationship("User", foreign_keys=[created_by])


class Conversation(Base):
    """Conversation model for AI chat"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    matter_id = Column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=True)
    title = Column(String(500), nullable=True)  # Auto-generated from first message
    summary = Column(Text, nullable=True)  # AI-generated summary for search
    summary_generated_at = Column(DateTime(timezone=True), nullable=True)
    is_pinned = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    matter = relationship("Matter")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """Message model for AI chat"""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Citations/sources (for assistant messages)
    sources = Column(JSON, nullable=True)  # List of {document_id, chunk_id, title, page, similarity}
    
    # Context used (for debugging/audit)
    context_chunks = Column(JSON, nullable=True)  # Chunks used to generate response
    
    # Message metadata
    token_count = Column(Integer, nullable=True)
    model_name = Column(String(100), nullable=True)  # e.g., "claude-3-5-sonnet-20241022"
    finish_reason = Column(String(50), nullable=True)  # e.g., "end_turn", "max_tokens"
    
    # User feedback
    rating = Column(Integer, nullable=True)  # 1-5 stars, or -1/1 for thumbs down/up
    feedback_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class BillableSession(Base):
    """Billable session model for tracking time spent on conversations"""
    __tablename__ = "billable_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    matter_id = Column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=True)

    # Session timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # Calculated or manually adjusted

    # AI-generated description (editable by user)
    ai_description = Column(Text, nullable=True)  # Auto-generated from conversation
    description = Column(Text, nullable=True)  # User-edited version (if changed)

    # Billing details
    activity_code = Column(String(50), nullable=True)  # e.g., "A101" for Research
    is_billable = Column(Boolean, default=True)
    is_exported = Column(Boolean, default=False)
    exported_at = Column(DateTime(timezone=True), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    conversation = relationship("Conversation")
    matter = relationship("Matter")


class DailyBriefing(Base):
    """AI-generated daily briefing for users"""
    __tablename__ = "daily_briefings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Briefing content
    briefing_date = Column(Date, nullable=False)  # Date the briefing is for
    content = Column(Text, nullable=False)  # Markdown content

    # Generation metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    model_name = Column(String(100), nullable=True)
    token_count = Column(Integer, nullable=True)

    # Context used for generation (for debugging)
    context_summary = Column(JSON, nullable=True)  # Summary of data used

    # Relationships
    user = relationship("User")
    company = relationship("Company")


class WaitlistSignup(Base):
    """Waitlist signup model for marketing site"""
    __tablename__ = "waitlist_signups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)

    # Tracking
    source = Column(String(100), nullable=True)  # 'landing_page', 'contact_page', etc.
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)

    # CASL Consent Tracking (Canada Anti-Spam Legislation)
    consent_marketing = Column(Boolean, default=False, nullable=False)  # Express consent for CEMs
    consent_date = Column(DateTime(timezone=True), nullable=True)  # When consent was given

    # Conversion tracking
    converted_to_user = Column(Boolean, default=False, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
