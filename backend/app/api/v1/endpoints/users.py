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
from app.core.tenant import require_admin, require_tenant_context, TenantContext

router = APIRouter()

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
