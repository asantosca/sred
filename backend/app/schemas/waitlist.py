# app/schemas/waitlist.py

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class WaitlistSignupCreate(BaseModel):
    """Schema for creating a waitlist signup"""
    email: EmailStr
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None

    # Tracking parameters (usually from frontend)
    source: Optional[str] = None  # 'landing_page', 'contact_page', etc.
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class WaitlistSignupResponse(BaseModel):
    """Schema for waitlist signup response"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    converted_to_user: bool = False

    class Config:
        from_attributes = True
