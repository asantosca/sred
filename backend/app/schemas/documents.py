# app/schemas/documents.py - Document management schemas

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import uuid

class DocumentUpload(BaseModel):
    """Schema for document upload metadata"""
    access_groups: List[uuid.UUID] = []  # Which groups can access (empty = all)
    tags: List[str] = []  # Optional tags for organization
    
    @validator('tags')
    def validate_tags(cls, v):
        # Ensure tags are lowercase and trimmed
        return [tag.lower().strip() for tag in v if tag.strip()]

class DocumentResponse(BaseModel):
    """Schema for document information"""
    id: uuid.UUID
    filename: str
    original_filename: str
    file_size: Optional[int]
    content_type: Optional[str]
    s3_path: str
    company_id: uuid.UUID
    uploaded_by: uuid.UUID
    access_groups_json: List[str]
    tags: List[str] = []
    processing_status: str
    error_message: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    """List of documents with pagination"""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int

class DocumentUpdate(BaseModel):
    """Schema for updating document metadata"""
    access_groups: Optional[List[uuid.UUID]] = None
    tags: Optional[List[str]] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            return [tag.lower().strip() for tag in v if tag.strip()]
        return v