# app/schemas/documents.py - Pydantic schemas for documents

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

# Document Upload Schemas
class DocumentUploadBase(BaseModel):
    """Base schema for document upload"""
    matter_id: UUID = Field(..., description="Matter ID to associate document with")
    document_title: str = Field(..., min_length=1, max_length=500, description="Document title")
    document_date: date = Field(..., description="Document date")
    document_status: str = Field(..., description="Document status: draft, final, executed, filed")
    document_type: str = Field(..., description="Document type: contract, pleading, correspondence, etc.")
    document_subtype: Optional[str] = Field(None, max_length=100, description="Document subtype")
    
    # Security fields
    confidentiality_level: str = Field(default="standard_confidential", description="Confidentiality level")
    privilege_attorney_client: bool = Field(default=False, description="Attorney-client privileged")
    privilege_work_product: bool = Field(default=False, description="Work product privileged")
    privilege_settlement: bool = Field(default=False, description="Settlement communication privileged")
    
    # Optional metadata
    description: Optional[str] = Field(None, description="Document description")
    internal_notes: Optional[str] = Field(None, max_length=5000, description="Internal notes")
    tags: Optional[List[str]] = Field(default_factory=list, description="Document tags")

class DocumentUploadResponse(BaseModel):
    """Response schema for document upload"""
    document_id: UUID
    filename: str
    original_filename: str
    file_size_bytes: int
    document_title: str
    document_type: str
    matter_id: UUID
    storage_path: str
    file_hash: str
    upload_status: str
    message: str
    
    # Auto-detection results
    auto_detection_applied: bool = Field(default=False, description="Whether auto-detection was applied")
    detected_enhancements: Optional[List[str]] = Field(default_factory=list, description="List of fields enhanced by auto-detection")

# Quick Upload (5 required fields)
class QuickDocumentUpload(BaseModel):
    """Quick upload schema - minimal required fields"""
    matter_id: UUID
    document_type: str
    document_title: str
    document_date: date
    confidentiality_level: str = Field(default="standard_confidential")

# Standard Upload (includes security and basic metadata)
class StandardDocumentUpload(DocumentUploadBase):
    """Standard upload schema with common fields"""
    # Author/recipient info
    author: Optional[str] = Field(None, max_length=255)
    recipient: Optional[str] = Field(None, max_length=255)
    
    # Date fields
    date_received: Optional[date] = None
    filed_date: Optional[date] = None

# Type-specific upload schemas
class ContractUpload(StandardDocumentUpload):
    """Upload schema for contracts"""
    contract_type: Optional[str] = Field(None, max_length=100)
    contract_value: Optional[float] = Field(None, ge=0)
    contract_effective_date: Optional[date] = None
    contract_expiration_date: Optional[date] = None
    governing_law: Optional[str] = Field(None, max_length=100)

class PleadingUpload(StandardDocumentUpload):
    """Upload schema for pleadings"""
    court_jurisdiction: str = Field(..., max_length=255, description="Court jurisdiction")
    case_number: str = Field(..., max_length=100, description="Case number")
    opposing_party: str = Field(..., max_length=255, description="Opposing party")
    judge_name: Optional[str] = Field(None, max_length=255)
    opposing_counsel: Optional[str] = Field(None, max_length=255)

class CorrespondenceUpload(StandardDocumentUpload):
    """Upload schema for correspondence"""
    correspondence_type: str = Field(default="email", max_length=50)
    author: str = Field(..., max_length=255, description="Author/sender")
    recipient: str = Field(..., max_length=255, description="Recipient")
    cc: Optional[str] = Field(None, max_length=255, description="CC recipients")
    subject: Optional[str] = Field(None, max_length=500, description="Subject line")

class DiscoveryUpload(StandardDocumentUpload):
    """Upload schema for discovery documents"""
    discovery_type: str = Field(..., max_length=100, description="Type of discovery")
    propounding_party: Optional[str] = Field(None, max_length=255)
    responding_party: Optional[str] = Field(None, max_length=255)
    discovery_number: Optional[str] = Field(None, max_length=100)
    response_due_date: Optional[date] = None
    response_status: str = Field(default="pending", max_length=50)

class ExhibitUpload(StandardDocumentUpload):
    """Upload schema for exhibits"""
    exhibit_number: str = Field(..., max_length=100, description="Exhibit number")
    related_to_document_id: Optional[UUID] = Field(None, description="Related document ID")

# Document Response Schemas
class DocumentBase(BaseModel):
    """Base document schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    matter_id: UUID
    filename: str
    original_filename: str
    file_extension: str
    file_size_bytes: int
    file_hash: str
    mime_type: Optional[str]
    
    # Classification
    document_type: str
    document_subtype: Optional[str]
    document_title: str
    document_date: date
    document_status: str
    
    # Security
    confidentiality_level: str
    is_privileged: bool
    
    # Processing status
    processing_status: str
    text_extracted: bool
    indexed_for_search: bool
    
    # Audit
    created_at: datetime
    created_by: UUID
    updated_at: Optional[datetime]
    updated_by: UUID

class Document(DocumentBase):
    """Full document schema for API responses"""
    # All optional metadata fields
    description: Optional[str] = None
    date_received: Optional[date] = None
    filed_date: Optional[date] = None
    
    # Version control
    is_current_version: bool
    version_label: Optional[str] = None
    version_number: int
    parent_document_id: Optional[UUID] = None
    root_document_id: Optional[UUID] = None
    
    # Security details
    privilege_attorney_client: bool
    privilege_work_product: bool
    privilege_settlement: bool
    
    # Metadata
    internal_notes: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Type-specific fields (will be null if not applicable)
    author: Optional[str] = None
    recipient: Optional[str] = None
    opposing_counsel: Optional[str] = None
    opposing_party: Optional[str] = None
    court_jurisdiction: Optional[str] = None
    case_number: Optional[str] = None
    judge_name: Optional[str] = None
    contract_type: Optional[str] = None
    contract_value: Optional[float] = None
    contract_effective_date: Optional[date] = None
    contract_expiration_date: Optional[date] = None
    governing_law: Optional[str] = None
    discovery_type: Optional[str] = None
    propounding_party: Optional[str] = None
    responding_party: Optional[str] = None
    discovery_number: Optional[str] = None
    response_due_date: Optional[date] = None
    response_status: Optional[str] = None
    exhibit_number: Optional[str] = None
    correspondence_type: Optional[str] = None
    cc: Optional[str] = None
    subject: Optional[str] = None

class DocumentWithMatter(Document):
    """Document schema with matter information"""
    matter_number: str
    client_name: str
    matter_status: str

class DocumentListResponse(BaseModel):
    """Response schema for document list with pagination"""
    documents: List[DocumentWithMatter]
    total: int
    page: int
    size: int
    pages: int
    matter_id: Optional[UUID] = None

# File operation schemas
class DocumentDownloadResponse(BaseModel):
    """Response schema for document download"""
    download_url: str
    expires_at: datetime
    filename: str
    file_size_bytes: int
    mime_type: str

class FileValidationResult(BaseModel):
    """Schema for file validation results"""
    valid: bool
    errors: List[str]
    file_extension: str
    mime_type: str
    file_size: int