# app/api/v1/endpoints/auth.py - Authentication endpoints

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.db.session import get_db
from app.services.auth import AuthService
from app.schemas.auth import (
    CompanyRegistration, UserLogin, AuthResponse,
    Token, UserResponse, CompanyResponse, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetVerify, PasswordResetConfirm
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

    # Create authentication tokens
    access_token = await auth_service.create_user_auth_token(admin_user)
    refresh_token = await auth_service.create_refresh_token(admin_user)

    # Prepare response
    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
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

    # Create authentication tokens
    access_token = await auth_service.create_user_auth_token(user)
    refresh_token = await auth_service.create_refresh_token(user)

    # Prepare response
    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        company=CompanyResponse.model_validate(company),
        token=token
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token

    This endpoint allows clients to obtain a new access token using a valid refresh token.
    The old refresh token is revoked and a new one is issued for security (token rotation).
    """
    auth_service = AuthService(db)

    # Verify the refresh token and get user
    user, company = await auth_service.verify_refresh_token(refresh_request.refresh_token)

    # Revoke the old refresh token (token rotation for security)
    await auth_service.revoke_refresh_token(refresh_request.refresh_token)

    # Create new tokens
    access_token = await auth_service.create_user_auth_token(user)
    new_refresh_token = await auth_service.create_refresh_token(user)

    # Return new tokens
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=new_refresh_token
    )

@router.post("/logout")
async def logout():
    """
    Logout user (client-side token removal)
    """
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=AuthResponse)
async def get_current_user_info(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information

    Returns the full user profile, company details, and a fresh token.
    Uses the JWT middleware to validate authentication.
    """
    from app.middleware.auth import get_current_user
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.models import User

    # Get current user from JWT (validates token, raises 401 if invalid)
    tenant_context = await get_current_user(request)

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

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create fresh auth token
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

@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset

    Sends a password reset email to the user if the email exists.
    Always returns success to prevent email enumeration attacks.
    """
    from app.services.email import EmailService

    auth_service = AuthService(db)
    email_service = EmailService()

    # Request password reset (returns token even if user doesn't exist)
    reset_token = await auth_service.request_password_reset(request_data.email)

    # Send email (only if user exists, but we don't reveal this)
    # The email service handles the logic internally
    try:
        await email_service.send_password_reset_email(
            to_email=request_data.email,
            reset_token=reset_token
        )
    except Exception as e:
        # Log error but don't reveal to user
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send password reset email: {e}")

    # Always return success (security: prevent email enumeration)
    return {
        "message": "If the email exists, a password reset link has been sent",
        "detail": "Please check your email for instructions"
    }

@router.post("/password-reset/verify", status_code=status.HTTP_200_OK)
async def verify_password_reset_token(
    verify_data: PasswordResetVerify,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify password reset token

    Check if a password reset token is valid without using it.
    Useful for frontend to validate token before showing reset form.
    """
    auth_service = AuthService(db)

    is_valid = await auth_service.verify_password_reset_token(verify_data.token)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    return {"message": "Token is valid", "valid": True}

@router.post("/password-reset/confirm", response_model=AuthResponse)
async def confirm_password_reset(
    confirm_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset with new password

    Resets the user's password and returns new authentication tokens.
    """
    auth_service = AuthService(db)

    # Reset password
    user = await auth_service.reset_password(
        token=confirm_data.token,
        new_password=confirm_data.new_password
    )

    # Create new authentication tokens
    access_token = await auth_service.create_user_auth_token(user)
    refresh_token = await auth_service.create_refresh_token(user)

    # Prepare response
    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        company=CompanyResponse.model_validate(user.company),
        token=token
    )