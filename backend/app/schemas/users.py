# app/schemas/users.py - User management schemas

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import uuid

class UserInvite(BaseModel):
    """Schema for inviting a new user"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    group_ids: List[uuid.UUID] = []  # Groups to assign user to
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserGroupAssignment(BaseModel):
    """Schema for assigning user to groups"""
    group_ids: List[uuid.UUID]

class GroupResponse(BaseModel):
    """Schema for group information"""
    id: uuid.UUID
    name: str
    description: Optional[str]
    permissions_json: List[str]
    
    class Config:
        from_attributes = True

class UserDetailResponse(BaseModel):
    """Detailed user information with groups"""
    id: uuid.UUID
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_admin: bool
    company_id: uuid.UUID
    created_at: datetime
    last_active: Optional[datetime]
    groups: List[GroupResponse] = []
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """List of users with pagination info"""
    users: List[UserDetailResponse]
    total: int
    page: int
    page_size: int