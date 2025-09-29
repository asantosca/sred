# app/api/v1/endpoints/auth.py - Authentication endpoints

from fastapi import APIRouter, Depends, HTTPException, status
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
        user=UserResponse.from_orm(admin_user),
        company=CompanyResponse.from_orm(company),
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
        user=UserResponse.from_orm(user),
        company=CompanyResponse.from_orm(company),
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

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    # TODO: Add dependency to get current user from token
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user information
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get current user not implemented yet"
    )
