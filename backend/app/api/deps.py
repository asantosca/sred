# app/api/deps.py - FastAPI dependencies

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.session import get_db
from app.middleware.auth import get_current_user as get_tenant_context
from app.models.models import User
from app.core.tenant import TenantContext
from app.core.config import settings

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get current authenticated user as User model.
    Converts TenantContext to actual User model from database.
    """
    # Get tenant context from auth middleware
    tenant_context = await get_tenant_context(request)
    
    # Get user from database
    query = select(User).where(User.id == UUID(tenant_context.user_id))
    result = await db.execute(query)
    user = result.scalar()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get current authenticated admin user.
    Requires user to be an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

def verify_company_access(user: User, resource_company_id: UUID) -> None:
    """
    Verify that user has access to resources belonging to specific company.
    Raises HTTPException if access denied.
    """
    if user.company_id != resource_company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"  # Don't reveal existence of resource in other company
        )


async def get_platform_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get current authenticated platform admin.
    Platform admins are SR&ED Intelligence staff who can access all companies' data.
    Configured via PLATFORM_ADMIN_EMAILS environment variable.
    """
    if current_user.email.lower() not in settings.PLATFORM_ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin privileges required"
        )

    return current_user