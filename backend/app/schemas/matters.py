# app/schemas/matters.py - Pydantic schemas for matters

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

class MatterBase(BaseModel):
    """Base matter schema with common fields"""
    claim_number: str = Field(..., min_length=1, max_length=50, description="Unique claim number")
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    project_type: str = Field(..., min_length=1, max_length=100, description="Type of SR&ED project")
    claim_status: str = Field(default="active", max_length=50, description="Claim status")
    description: Optional[str] = Field(None, description="Claim description")
    opened_date: date = Field(..., description="Date claim was opened")
    closed_date: Optional[date] = Field(None, description="Date claim was closed")
    fiscal_year_end: Optional[date] = Field(None, description="Fiscal year end date")
    lead_consultant_user_id: Optional[UUID] = Field(None, description="Lead consultant user ID")

class MatterCreate(MatterBase):
    """Schema for creating a new matter"""
    pass

class MatterUpdate(BaseModel):
    """Schema for updating a claim"""
    claim_number: Optional[str] = Field(None, min_length=1, max_length=50)
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    project_type: Optional[str] = Field(None, min_length=1, max_length=100)
    claim_status: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    opened_date: Optional[date] = None
    closed_date: Optional[date] = None
    fiscal_year_end: Optional[date] = None
    lead_consultant_user_id: Optional[UUID] = None

class MatterInDB(MatterBase):
    """Schema for matter as stored in database"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    company_id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: Optional[datetime]
    updated_by: UUID

class Matter(MatterInDB):
    """Schema for matter response"""
    pass

class MatterWithDetails(Matter):
    """Claim with additional details like user names and current user's permissions"""
    lead_consultant_name: Optional[str] = None
    created_by_name: str
    updated_by_name: str
    document_count: int = 0
    team_member_count: int = 0
    # Current user's permissions for this claim
    user_can_upload: bool = False
    user_can_edit: bool = False
    user_can_delete: bool = False

# Matter Access Schemas
class MatterAccessBase(BaseModel):
    """Base matter access schema"""
    user_id: UUID
    access_role: str = Field(..., max_length=50, description="User role for this matter")
    can_upload: bool = Field(default=True, description="Can upload documents")
    can_edit: bool = Field(default=True, description="Can edit documents")
    can_delete: bool = Field(default=False, description="Can delete documents")

class MatterAccessCreate(MatterAccessBase):
    """Schema for creating matter access"""
    pass

class MatterAccessUpdate(BaseModel):
    """Schema for updating matter access"""
    access_role: Optional[str] = Field(None, max_length=50)
    can_upload: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None

class MatterAccessInDB(MatterAccessBase):
    """Schema for matter access as stored in database"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    matter_id: UUID
    granted_at: datetime
    granted_by: UUID

class MatterAccess(MatterAccessInDB):
    """Schema for matter access response"""
    pass

class MatterAccessWithDetails(MatterAccess):
    """Matter access with user details"""
    user_name: str
    user_email: str
    granted_by_name: str

# List responses
class MatterListResponse(BaseModel):
    """Response schema for claim list with pagination"""
    claims: List[MatterWithDetails]
    total: int
    page: int
    size: int
    pages: int

class MatterAccessListResponse(BaseModel):
    """Response schema for claim access list"""
    access_list: List[MatterAccessWithDetails]
    claim_id: UUID
    claim_number: str
    company_name: str