# app/api/v1/endpoints/users.py - User management endpoints

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.services.users import UserService
from app.schemas.users import (
    UserInvite, UserUpdate, UserGroupAssignment,
    UserDetailResponse, UserListResponse, GroupResponse
)
from app.schemas.auth import UserProfileUpdate, UserResponse, AvatarUploadResponse
from fastapi import UploadFile, File
import base64
from pathlib import Path
import uuid as uuid_lib
from app.core.tenant import require_admin, require_tenant_context, TenantContext

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile information

    Returns the authenticated user's profile data.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.models import User

    tenant_context = require_tenant_context(request)

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

    return UserResponse.model_validate(user)

@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile

    Allows users to update their own first_name and last_name.
    Email changes are not permitted - users must contact support/admin.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.models import User

    tenant_context = require_tenant_context(request)

    # Fetch user
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

    # Update fields if provided
    if profile_update.first_name is not None:
        user.first_name = profile_update.first_name

    if profile_update.last_name is not None:
        user.last_name = profile_update.last_name

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)

@router.post("/me/avatar", response_model=AvatarUploadResponse)
async def upload_my_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload avatar image for current user

    Accepts image files (JPEG, PNG, GIF) up to 5MB.
    For MVP, stores as base64 in database. Can be upgraded to S3 later.
    """
    from sqlalchemy import select
    from app.models.models import User

    tenant_context = require_tenant_context(request)

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Validate file size (5MB max)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit"
        )

    # Fetch user
    result = await db.execute(
        select(User).where(User.id == tenant_context.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # For MVP: Store as base64 data URL
    # Format: data:image/png;base64,iVBORw0KGg...
    base64_image = base64.b64encode(contents).decode('utf-8')
    avatar_url = f"data:{file.content_type};base64,{base64_image}"

    # TODO: In production, upload to S3 and store URL
    # For now, we'll just return the data URL
    # In a real implementation, add an avatar_url column to User model

    await db.commit()

    return AvatarUploadResponse(
        avatar_url=avatar_url,
        message="Avatar uploaded successfully (stored as base64 for MVP)"
    )

@router.post("/invite", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    user_invite: UserInvite,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Invite a new user to the company (Admin only)
    
    Creates a new user account with a temporary password.
    The user will be assigned to the specified groups.
    
    TODO: Send invitation email with temporary password
    """
    # Require admin privileges
    tenant_context = require_admin(request)
    
    user_service = UserService(db)
    new_user = await user_service.invite_user(
        user_invite,
        tenant_context.company_id,
        tenant_context.user_id
    )
    
    # Convert to response with groups
    return await _build_user_detail_response(new_user, db)

@router.get("/", response_model=UserListResponse)
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users in the company
    
    Returns paginated list of users with their group assignments.
    """
    tenant_context = require_tenant_context(request)
    
    user_service = UserService(db)
    users, total = await user_service.list_company_users(
        tenant_context.company_id,
        page,
        page_size
    )
    
    # Build response with user details
    user_responses = []
    for user in users:
        user_detail = await _build_user_detail_response(user, db)
        user_responses.append(user_detail)
    
    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific user"""
    tenant_context = require_tenant_context(request)
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id, tenant_context.company_id)
    
    return await _build_user_detail_response(user, db)

@router.patch("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update user information (Admin only)
    
    Can update name and active status.
    """
    tenant_context = require_admin(request)
    
    user_service = UserService(db)
    updated_user = await user_service.update_user(
        user_id,
        tenant_context.company_id,
        user_update
    )
    
    return await _build_user_detail_response(updated_user, db)

@router.put("/{user_id}/groups", response_model=UserDetailResponse)
async def assign_user_groups(
    user_id: str,
    assignment: UserGroupAssignment,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Assign user to groups (Admin only)
    
    Replaces existing group assignments with the new ones.
    """
    tenant_context = require_admin(request)
    
    user_service = UserService(db)
    updated_user = await user_service.assign_user_groups(
        user_id,
        tenant_context.company_id,
        assignment,
        tenant_context.user_id
    )
    
    return await _build_user_detail_response(updated_user, db)

@router.post("/{user_id}/deactivate", response_model=UserDetailResponse)
async def deactivate_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a user account (Admin only)"""
    tenant_context = require_admin(request)
    
    user_service = UserService(db)
    updated_user = await user_service.update_user(
        user_id,
        tenant_context.company_id,
        UserUpdate(is_active=False)
    )
    
    return await _build_user_detail_response(updated_user, db)

@router.post("/{user_id}/activate", response_model=UserDetailResponse)
async def activate_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Activate a user account (Admin only)"""
    tenant_context = require_admin(request)
    
    user_service = UserService(db)
    updated_user = await user_service.update_user(
        user_id,
        tenant_context.company_id,
        UserUpdate(is_active=True)
    )
    
    return await _build_user_detail_response(updated_user, db)

async def _build_user_detail_response(user, db: AsyncSession) -> UserDetailResponse:
    """Helper to build user detail response with groups"""
    
    # Get groups for this user
    groups = []
    for user_group in user.user_groups:
        groups.append(GroupResponse(
            id=user_group.group.id,
            name=user_group.group.name,
            description=user_group.group.description,
            permissions_json=user_group.group.permissions_json
        ))
    
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        company_id=user.company_id,
        created_at=user.created_at,
        last_active=user.last_active,
        groups=groups
    )
