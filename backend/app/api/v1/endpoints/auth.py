# app/api/v1/endpoints/auth.py - Authentication endpoints

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import timedelta, datetime, timezone
import logging

from app.db.session import get_db
from app.services.auth import AuthService
from app.schemas.auth import (
    CompanyRegistration, UserLogin, AuthResponse, RegistrationResponse,
    Token, UserResponse, CompanyResponse, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirm
)
from app.models.models import User, PasswordResetToken
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_company(
    registration: CompanyRegistration,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new company with admin user and make user inactive until email verification

    This creates:
    - A new company (inactive)
    - An admin user for the company (inactive) with the provided password
    - Default user groups (Administrators, Partners, Associates, etc.)
    - Assigns admin to Administrators group
    - Sends confirmation email to admin

    The admin must click the confirmation link in their email to activate both
    their account and the company. The password is set during registration.
    """
    from app.services.email import EmailService
    import logging

    logger = logging.getLogger(__name__)
    auth_service = AuthService(db)
    email_service = EmailService()

    # Create company and admin user. Both are inactive requiring email confirmation.
    company, admin_user = await auth_service.create_company_with_admin(registration)

    # Request password reset token for email confirmation
    reset_token, user_exists = await auth_service.request_password_reset(admin_user.email)

    # Send confirmation email with password setup link
    try:
        user_name = f"{admin_user.first_name} {admin_user.last_name}" if admin_user.first_name else None
        await email_service.send_admin_email_confirmation(
            to_email=admin_user.email,
            token=reset_token,
            user_name=user_name
        )
    except Exception as e:
        # Log error but don't reveal to user (security: prevent email enumeration)
        logger.error(f"Failed to send admin email confirmation: {e}")


    return RegistrationResponse(
        user=UserResponse.model_validate(admin_user),
        company=CompanyResponse.model_validate(company),
        message="Registration successful. Please check your email to verify your account.",
        token=reset_token
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

    # Request password reset (returns token and whether user exists)
    reset_token, user_exists = await auth_service.request_password_reset(request_data.email)

    # Only send email if user exists (prevents unnecessary email attempts)
    if user_exists:
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

    # Always return same response (security: prevent email enumeration)
    return {
        "message": "If the email exists, a password reset link has been sent",
        "detail": "Please check your email for instructions"
    }

@router.get("/password-reset/verify", status_code=status.HTTP_200_OK)
async def verify_password_reset_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify password reset token

    Check if a password reset token is valid without using it.
    Useful for frontend to validate token before showing reset form.

    Example: GET /api/v1/auth/password-reset/verify?token=abc123
    """
    auth_service = AuthService(db)

    is_valid = await auth_service.verify_password_reset_token(token)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    return {"message": "Token is valid", "valid": True}

@router.get("/confirm-email/verify", status_code=status.HTTP_200_OK)
async def verify_email_confirmation_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email confirmation token

    Check if an email confirmation token is valid without using it.
    Useful for frontend to validate token before showing password setup form.

    Example: GET /api/v1/auth/confirm-email/verify?token=abc123
    """
    auth_service = AuthService(db)

    is_valid = await auth_service.verify_password_reset_token(token)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token"
        )

    return {"message": "Token is valid", "valid": True}

@router.post("/confirm-email", response_model=AuthResponse)
async def confirm_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm email address for new admin user

    This endpoint is used during the registration flow. When an admin registers
    (providing email AND password), they receive an email with a confirmation link.
    Clicking that link will:
    - Activate their user account
    - Activate their company (if they are the admin)
    - Return authentication tokens for immediate login

    The password was already set during registration, so this just activates the account.

    Request body: {"token": "confirmation_token"}
    """
    from hashlib import sha256

    auth_service = AuthService(db)

    # Verify and get the token from database
    token_hash = sha256(token.encode()).hexdigest()

    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.is_used or db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token"
        )

    # Get the user
    user_result = await db.execute(
        select(User)
        .options(selectinload(User.company))
        .where(User.id == db_token.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Activate user
    if not user.is_active:
        user.is_active = True
        logger.info(f"User {user.email} activated via email confirmation")

        # If user is admin and company is inactive, activate the company too
        if user.is_admin and user.company and not user.company.is_active:
            user.company.is_active = True
            logger.info(f"Company {user.company.name} activated via admin email confirmation")

    # Mark token as used
    db_token.is_used = True
    db_token.used_at = datetime.now(timezone.utc)

    await db.commit()

    # Create new authentication tokens
    access_token = await auth_service.create_user_auth_token(user)
    refresh_token = await auth_service.create_refresh_token(user)

    # Prepare response
    token_obj = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        company=CompanyResponse.model_validate(user.company),
        token=token_obj
    )

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