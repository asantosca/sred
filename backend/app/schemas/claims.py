# app/schemas/claims.py - Pydantic schemas for SR&ED claims

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

# Project types for SR&ED
PROJECT_TYPES = [
    "Software Development",
    "Manufacturing Process",
    "Product Design",
    "Chemical/Biological",
    "Engineering",
    "Other"
]

# Claim statuses
CLAIM_STATUSES = [
    "draft",
    "in_progress",
    "under_review",
    "submitted",
    "approved",
    "rejected"
]


class ClaimBase(BaseModel):
    """Base claim schema with common fields"""
    claim_number: str = Field(..., min_length=1, max_length=50, description="Unique claim number")
    company_name: str = Field(..., min_length=1, max_length=255, description="Client company name")
    project_type: str = Field(..., min_length=1, max_length=100, description="Type of R&D project")
    claim_status: str = Field(default="draft", max_length=50, description="Claim status")
    description: Optional[str] = Field(None, description="Claim description")
    opened_date: date = Field(..., description="Date claim was opened")
    closed_date: Optional[date] = Field(None, description="Date claim was closed")
    lead_consultant_user_id: Optional[UUID] = Field(None, description="Lead consultant user ID")

    # SR&ED-specific fields
    fiscal_year_end: Optional[date] = Field(None, description="Company's fiscal year end date")
    naics_code: Optional[str] = Field(None, max_length=10, description="NAICS industry code")
    cra_business_number: Optional[str] = Field(None, max_length=15, description="CRA business number")
    total_eligible_expenditures: Optional[Decimal] = Field(None, description="Total eligible SR&ED expenditures")
    federal_credit_estimate: Optional[Decimal] = Field(None, description="Estimated federal ITC")
    provincial_credit_estimate: Optional[Decimal] = Field(None, description="Estimated provincial credit")

    # Project-specific fields (for AI context in T661 generation)
    project_title: Optional[str] = Field(None, max_length=255, description="Short name for the specific R&D project")
    project_objective: Optional[str] = Field(None, description="1-2 sentences describing the technical goal")
    technology_focus: Optional[str] = Field(None, max_length=500, description="Specific technology area and keywords")


class ClaimCreate(ClaimBase):
    """Schema for creating a new claim"""
    pass


class ClaimUpdate(BaseModel):
    """Schema for updating a claim"""
    claim_number: Optional[str] = Field(None, min_length=1, max_length=50)
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    project_type: Optional[str] = Field(None, min_length=1, max_length=100)
    claim_status: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    opened_date: Optional[date] = None
    closed_date: Optional[date] = None
    lead_consultant_user_id: Optional[UUID] = None

    # SR&ED-specific fields
    fiscal_year_end: Optional[date] = None
    naics_code: Optional[str] = Field(None, max_length=10)
    cra_business_number: Optional[str] = Field(None, max_length=15)
    total_eligible_expenditures: Optional[Decimal] = None
    federal_credit_estimate: Optional[Decimal] = None
    provincial_credit_estimate: Optional[Decimal] = None

    # Project-specific fields (for AI context in T661 generation)
    project_title: Optional[str] = Field(None, max_length=255)
    project_objective: Optional[str] = None
    technology_focus: Optional[str] = Field(None, max_length=500)


class ClaimInDB(ClaimBase):
    """Schema for claim as stored in database"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    created_at: datetime
    created_by: UUID
    updated_at: Optional[datetime]
    updated_by: UUID


class Claim(ClaimInDB):
    """Schema for claim response"""
    pass


class ClaimWithDetails(Claim):
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


# Claim Access Schemas
class ClaimAccessBase(BaseModel):
    """Base claim access schema"""
    user_id: UUID
    access_role: str = Field(..., max_length=50, description="User role for this claim")
    can_upload: bool = Field(default=True, description="Can upload documents")
    can_edit: bool = Field(default=True, description="Can edit documents")
    can_delete: bool = Field(default=False, description="Can delete documents")


class ClaimAccessCreate(ClaimAccessBase):
    """Schema for creating claim access"""
    pass


class ClaimAccessUpdate(BaseModel):
    """Schema for updating claim access"""
    access_role: Optional[str] = Field(None, max_length=50)
    can_upload: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None


class ClaimAccessInDB(ClaimAccessBase):
    """Schema for claim access as stored in database"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    granted_at: datetime
    granted_by: UUID


class ClaimAccess(ClaimAccessInDB):
    """Schema for claim access response"""
    pass


class ClaimAccessWithDetails(ClaimAccess):
    """Claim access with user details"""
    user_name: str
    user_email: str
    granted_by_name: str


# List responses
class ClaimListResponse(BaseModel):
    """Response schema for claim list with pagination"""
    claims: List[ClaimWithDetails]
    total: int
    page: int
    size: int
    pages: int


class ClaimAccessListResponse(BaseModel):
    """Response schema for claim access list"""
    access_list: List[ClaimAccessWithDetails]
    claim_id: UUID
    claim_number: str
    company_name: str
