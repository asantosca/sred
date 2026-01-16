# app/api/v1/endpoints/matters.py - Claim management endpoints (legacy route, uses claims)

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
import math

from app.db.session import get_db
from app.schemas.claims import (
    Claim as Matter, ClaimCreate as MatterCreate, ClaimUpdate as MatterUpdate,
    ClaimWithDetails as MatterWithDetails, ClaimListResponse as MatterListResponse,
    ClaimAccess as MatterAccess, ClaimAccessCreate as MatterAccessCreate,
    ClaimAccessUpdate as MatterAccessUpdate, ClaimAccessWithDetails as MatterAccessWithDetails,
    ClaimAccessListResponse as MatterAccessListResponse
)
from app.models.models import Claim as MatterModel, ClaimAccess as MatterAccessModel, User, Conversation, BillableSession
from app.api.deps import get_current_user, verify_company_access

router = APIRouter()

@router.get("/", response_model=MatterListResponse)
async def list_matters(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search in matter number, client name, or description"),
    status: Optional[str] = Query(None, description="Filter by matter status"),
    matter_type: Optional[str] = Query(None, description="Filter by matter type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List matters with pagination and filtering.
    Users can only see matters they have access to.
    """
    # Build base query for matters user has access to
    query = (
        select(MatterModel)
        .join(MatterAccessModel, MatterModel.id == MatterAccessModel.claim_id)
        .where(
            and_(
                MatterModel.company_id == current_user.company_id,
                MatterAccessModel.user_id == current_user.id
            )
        )
    )
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                MatterModel.claim_number.ilike(search_term),
                MatterModel.company_name.ilike(search_term),
                MatterModel.description.ilike(search_term)
            )
        )
    
    if status:
        query = query.where(MatterModel.claim_status == status)

    if matter_type:
        query = query.where(MatterModel.project_type == matter_type)
    
    # Count total records
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(MatterModel.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    matters = result.scalars().all()
    
    # Calculate pagination info
    pages = math.ceil(total / size) if total > 0 else 1
    
    # Convert to response format with additional details
    matters_with_details = []
    for matter in matters:
        # Get additional details (we'll optimize this later with joins)
        matter_dict = {
            **matter.__dict__,
            "lead_consultant_name": None,
            "created_by_name": "Unknown",
            "updated_by_name": "Unknown",
            "document_count": 0,
            "team_member_count": 0
        }
        matters_with_details.append(MatterWithDetails(**matter_dict))
    
    return MatterListResponse(
        claims=matters_with_details,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/", response_model=Matter, status_code=status.HTTP_201_CREATED)
async def create_matter(
    matter_data: MatterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new matter.
    The creating user is automatically granted lead_consultant access.
    """
    # Check if matter number already exists in company
    existing_query = select(MatterModel).where(
        and_(
            MatterModel.company_id == current_user.company_id,
            MatterModel.claim_number == matter_data.claim_number
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claim number already exists in your organization"
        )
    
    # Create matter
    matter = MatterModel(
        company_id=current_user.company_id,
        created_by=current_user.id,
        updated_by=current_user.id,
        **matter_data.model_dump()
    )
    
    db.add(matter)
    await db.flush()  # Get the matter ID
    
    # Grant creator lead_consultant access
    matter_access = MatterAccessModel(
        claim_id=matter.id,
        user_id=current_user.id,
        access_role="lead_consultant",
        can_upload=True,
        can_edit=True,
        can_delete=True,
        granted_by=current_user.id
    )
    
    db.add(matter_access)
    await db.commit()
    await db.refresh(matter)
    
    return Matter.model_validate(matter)

@router.get("/{matter_id}", response_model=MatterWithDetails)
async def get_matter(
    matter_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific matter by ID with current user's permissions."""
    # Check if user has access to this claim and get their permissions
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.claim_id == matter_id,
            MatterAccessModel.user_id == current_user.id
        )
    )
    access_result = await db.execute(access_query)
    user_access = access_result.scalar()

    if not user_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found or access denied"
        )

    # Get matter with details
    query = select(MatterModel).where(MatterModel.id == matter_id)
    result = await db.execute(query)
    matter = result.scalar()

    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )

    # Add additional details including user's permissions
    matter_dict = {
        **matter.__dict__,
        "lead_consultant_name": None,
        "created_by_name": "Unknown",
        "updated_by_name": "Unknown",
        "document_count": 0,
        "team_member_count": 0,
        "user_can_upload": user_access.can_upload,
        "user_can_edit": user_access.can_edit,
        "user_can_delete": user_access.can_delete,
    }

    return MatterWithDetails(**matter_dict)

@router.put("/{matter_id}", response_model=Matter)
async def update_matter(
    matter_id: UUID,
    matter_data: MatterUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a matter. Requires edit access."""
    # Check if user has edit access to this claim
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.claim_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.can_edit == True
        )
    )
    access_result = await db.execute(access_query)
    if not access_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No edit access to this claim"
        )
    
    # Get matter
    query = select(MatterModel).where(MatterModel.id == matter_id)
    result = await db.execute(query)
    matter = result.scalar()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )
    
    # Update matter
    update_data = matter_data.model_dump(exclude_unset=True)
    if update_data:
        for field, value in update_data.items():
            setattr(matter, field, value)
        matter.updated_by = current_user.id
        
        await db.commit()
        await db.refresh(matter)
    
    return Matter.model_validate(matter)

@router.delete("/{matter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_matter(
    matter_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a matter. Requires delete access.

    Cannot delete claims that have linked conversations or billable sessions.
    User must first delete or unlink those resources.
    """
    # Check if user has delete access to this claim
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.claim_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.can_delete == True
        )
    )
    access_result = await db.execute(access_query)
    if not access_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No delete access to this claim"
        )

    # Get matter
    query = select(MatterModel).where(MatterModel.id == matter_id)
    result = await db.execute(query)
    matter = result.scalar()

    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )

    # Check for linked conversations
    conv_count_query = select(func.count()).where(Conversation.claim_id == matter_id)
    conv_result = await db.execute(conv_count_query)
    conv_count = conv_result.scalar() or 0

    if conv_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete claim: {conv_count} conversation(s) are linked to this claim. Please delete or unlink them first."
        )

    # Check for linked billable sessions
    session_count_query = select(func.count()).where(BillableSession.claim_id == matter_id)
    session_result = await db.execute(session_count_query)
    session_count = session_result.scalar() or 0

    if session_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete claim: {session_count} billable session(s) are linked to this claim. Please delete or unlink them first."
        )

    # Delete matter (cascade will handle documents and matter_access)
    await db.delete(matter)
    await db.commit()

# Matter Access Management Endpoints

@router.get("/{matter_id}/access", response_model=MatterAccessListResponse)
async def list_matter_access(
    matter_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users with access to a matter."""
    # Check if user has access to this claim
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.claim_id == matter_id,
            MatterAccessModel.user_id == current_user.id
        )
    )
    access_result = await db.execute(access_query)
    if not access_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found or access denied"
        )
    
    # Get matter details
    matter_query = select(MatterModel).where(MatterModel.id == matter_id)
    matter_result = await db.execute(matter_query)
    matter = matter_result.scalar()
    
    # Get all access records for this claim
    access_query = (
        select(MatterAccessModel)
        .where(MatterAccessModel.claim_id == matter_id)
        .order_by(MatterAccessModel.granted_at.desc())
    )
    access_result = await db.execute(access_query)
    access_records = access_result.scalars().all()
    
    # Convert to response format with user details
    access_with_details = []
    for access in access_records:
        access_dict = {
            **access.__dict__,
            "user_name": "Unknown User",
            "user_email": "unknown@example.com",
            "granted_by_name": "Unknown"
        }
        access_with_details.append(MatterAccessWithDetails(**access_dict))
    
    return MatterAccessListResponse(
        access_list=access_with_details,
        claim_id=matter_id,
        claim_number=matter.claim_number,
        company_name=matter.company_name
    )

@router.post("/{matter_id}/access", response_model=MatterAccess, status_code=status.HTTP_201_CREATED)
async def grant_matter_access(
    matter_id: UUID,
    access_data: MatterAccessCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Grant access to a matter for a user."""
    # Check if current user has access to manage this claim
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.claim_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.access_role.in_(["lead_consultant", "partner"])
        )
    )
    access_result = await db.execute(access_query)
    if not access_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to manage access for this claim"
        )
    
    # Check if user already has access
    existing_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.claim_id == matter_id,
            MatterAccessModel.user_id == access_data.user_id
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has access to this claim"
        )
    
    # Verify target user exists and is in same company
    user_query = select(User).where(
        and_(
            User.id == access_data.user_id,
            User.company_id == current_user.company_id
        )
    )
    user_result = await db.execute(user_query)
    if not user_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in your organization"
        )
    
    # Create access record
    matter_access = MatterAccessModel(
        claim_id=matter_id,
        granted_by=current_user.id,
        **access_data.model_dump()
    )
    
    db.add(matter_access)
    await db.commit()
    await db.refresh(matter_access)
    
    return MatterAccess.model_validate(matter_access)

@router.put("/{matter_id}/access/{access_id}", response_model=MatterAccess)
async def update_matter_access(
    matter_id: UUID,
    access_id: UUID,
    access_data: MatterAccessUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update matter access permissions."""
    # Check if current user has permission to manage access
    manager_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.claim_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.access_role.in_(["lead_consultant", "partner"])
        )
    )
    manager_result = await db.execute(manager_query)
    if not manager_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to manage access for this claim"
        )
    
    # Get access record
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.id == access_id,
            MatterAccessModel.claim_id == matter_id
        )
    )
    access_result = await db.execute(access_query)
    access_record = access_result.scalar()
    
    if not access_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access record not found"
        )
    
    # Update access
    update_data = access_data.model_dump(exclude_unset=True)
    if update_data:
        for field, value in update_data.items():
            setattr(access_record, field, value)
        
        await db.commit()
        await db.refresh(access_record)
    
    return MatterAccess.model_validate(access_record)

@router.delete("/{matter_id}/access/{access_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_matter_access(
    matter_id: UUID,
    access_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke matter access from a user."""
    # Check if current user has permission to manage access
    manager_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.claim_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.access_role.in_(["lead_consultant", "partner"])
        )
    )
    manager_result = await db.execute(manager_query)
    if not manager_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to manage access for this claim"
        )
    
    # Get access record
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.id == access_id,
            MatterAccessModel.claim_id == matter_id
        )
    )
    access_result = await db.execute(access_query)
    access_record = access_result.scalar()
    
    if not access_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access record not found"
        )
    
    # Don't allow removing the last lead attorney
    if access_record.access_role == "lead_consultant":
        lead_count_query = select(func.count()).where(
            and_(
                MatterAccessModel.claim_id == matter_id,
                MatterAccessModel.access_role == "lead_consultant"
            )
        )
        lead_count_result = await db.execute(lead_count_query)
        if lead_count_result.scalar() <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last lead consultant from a claim"
            )
    
    # Delete access record
    await db.delete(access_record)
    await db.commit()