# app/api/v1/endpoints/auth.py - Authentication endpoints

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.db.session import get_db
from app.services.auth import AuthService
from app.schemas.auth import (
    CompanyRegistration, UserLogin, AuthResponse, 
    Token, UserResponse, CompanyResponse
)
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_company(
    registration: CompanyRegistration,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new company with admin user
    
    This creates:
    - A new company
    - An admin user for the company
    - Default user groups (Administrators, Partners, Associates, etc.)
    - Assigns admin to Administrators group
    """
    auth_service = AuthService(db)
    
    # Create company and admin user
    company, admin_user = await auth_service.create_company_with_admin(registration)
    
    # Create authentication token
    access_token = await auth_service.create_user_auth_token(admin_user)
    
    # Prepare response
    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return AuthResponse(
        user=UserResponse.model_validate(admin_user),
        company=CompanyResponse.model_validate(company),
        token=token
    )

@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access token
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user, company = await auth_service.authenticate_user(login_data)
    
    # Create authentication token
    access_token = await auth_service.create_user_auth_token(user)
    
    # Prepare response
    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        company=CompanyResponse.model_validate(company),
        token=token
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    # TODO: Implement refresh token logic
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token not implemented yet"
    )

@router.post("/logout")
async def logout():
    """
    Logout user (client-side token removal)
    """
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=AuthResponse)
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information
    
    Returns the full user profile, company details, and a fresh token.
    """
    from app.services.auth import AuthService
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.models import User
    from app.core.tenant import get_tenant_context
    
    # Extract tenant context from request (handles JWT extraction)
    tenant_context = await get_tenant_context(request)
    
    if not tenant_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Fetch user with company relationship
    result = await db.execute(
        select(User)
        .options(selectinload(User.company))
        .where(User.id == tenant_context.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user permissions
    auth_service = AuthService(db)
    access_token = await auth_service.create_user_auth_token(user)
    
    # Prepare response
    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        company=CompanyResponse.model_validate(user.company),
        token=token
    )