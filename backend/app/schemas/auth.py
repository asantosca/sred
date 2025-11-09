# app/schemas/auth.py - Authentication schemas

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import uuid

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile

    Note: Email changes are not permitted through self-service.
    Users must contact support/admin to change their email address.
    This is a security measure for legal/compliance platforms.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @validator('first_name', 'last_name')
    def validate_name_fields(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Name fields cannot be empty')
        return v.strip() if v else v

class AvatarUploadResponse(BaseModel):
    """Response after uploading avatar"""
    avatar_url: str
    message: str

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_admin: bool
    company_id: uuid.UUID
    created_at: datetime
    last_active: Optional[datetime]
    
    class Config:
        from_attributes = True

class CompanyCreate(BaseModel):
    name: str
    plan_tier: str = "starter"
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters long')
        return v.strip()

class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    plan_tier: str
    subscription_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CompanyRegistration(BaseModel):
    """Complete company registration with admin user"""
    company_name: str
    admin_email: EmailStr
    admin_password: str
    admin_first_name: Optional[str] = None
    admin_last_name: Optional[str] = None
    plan_tier: str = "starter"

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    user_id: Optional[str] = None
    company_id: Optional[str] = None
    is_admin: bool = False
    permissions: List[str] = []

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    """Request password reset with email"""
    email: EmailStr

class PasswordResetVerify(BaseModel):
    """Verify password reset token"""
    token: str

class PasswordResetConfirm(BaseModel):
    """Confirm password reset with new password"""
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class PasswordChange(BaseModel):
    """Change password for logged-in user"""
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class AuthResponse(BaseModel):
    """Complete authentication response"""
    user: UserResponse
    company: CompanyResponse
    token: Token

class RegistrationResponse(BaseModel):
    user: UserResponse
    company: CompanyResponse
    message: str
    token: str