# app/api/v1/endpoints/matters.py - Matter management endpoints

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
import math

from app.db.session import get_db
from app.schemas.matters import (
    Matter, MatterCreate, MatterUpdate, MatterWithDetails,
    MatterListResponse, MatterAccess, MatterAccessCreate, 
    MatterAccessUpdate, MatterAccessWithDetails, MatterAccessListResponse
)
from app.models.models import Matter as MatterModel, MatterAccess as MatterAccessModel, User
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
        .join(MatterAccessModel, MatterModel.id == MatterAccessModel.matter_id)
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
                MatterModel.matter_number.ilike(search_term),
                MatterModel.client_name.ilike(search_term),
                MatterModel.description.ilike(search_term)
            )
        )
    
    if status:
        query = query.where(MatterModel.matter_status == status)

    if matter_type:
        query = query.where(MatterModel.matter_type == matter_type)
    
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
            "lead_attorney_name": None,
            "created_by_name": "Unknown",
            "updated_by_name": "Unknown",
            "document_count": 0,
            "team_member_count": 0
        }
        matters_with_details.append(MatterWithDetails(**matter_dict))
    
    return MatterListResponse(
        matters=matters_with_details,
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
    The creating user is automatically granted lead_attorney access.
    """
    # Check if matter number already exists in company
    existing_query = select(MatterModel).where(
        and_(
            MatterModel.company_id == current_user.company_id,
            MatterModel.matter_number == matter_data.matter_number
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Matter number already exists in your organization"
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
    
    # Grant creator lead_attorney access
    matter_access = MatterAccessModel(
        matter_id=matter.id,
        user_id=current_user.id,
        access_role="lead_attorney",
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
    """Get a specific matter by ID."""
    # Check if user has access to this matter
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.matter_id == matter_id,
            MatterAccessModel.user_id == current_user.id
        )
    )
    access_result = await db.execute(access_query)
    if not access_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found or access denied"
        )
    
    # Get matter with details
    query = select(MatterModel).where(MatterModel.id == matter_id)
    result = await db.execute(query)
    matter = result.scalar()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found"
        )
    
    # Add additional details
    matter_dict = {
        **matter.__dict__,
        "lead_attorney_name": None,
        "created_by_name": "Unknown",
        "updated_by_name": "Unknown", 
        "document_count": 0,
        "team_member_count": 0
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
    # Check if user has edit access to this matter
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.matter_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.can_edit == True
        )
    )
    access_result = await db.execute(access_query)
    if not access_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No edit access to this matter"
        )
    
    # Get matter
    query = select(MatterModel).where(MatterModel.id == matter_id)
    result = await db.execute(query)
    matter = result.scalar()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found"
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
    """Delete a matter. Requires delete access."""
    # Check if user has delete access to this matter
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.matter_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.can_delete == True
        )
    )
    access_result = await db.execute(access_query)
    if not access_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No delete access to this matter"
        )
    
    # Get matter
    query = select(MatterModel).where(MatterModel.id == matter_id)
    result = await db.execute(query)
    matter = result.scalar()
    
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found"
        )
    
    # Delete matter (cascade will handle related records)
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
    # Check if user has access to this matter
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.matter_id == matter_id,
            MatterAccessModel.user_id == current_user.id
        )
    )
    access_result = await db.execute(access_query)
    if not access_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matter not found or access denied"
        )
    
    # Get matter details
    matter_query = select(MatterModel).where(MatterModel.id == matter_id)
    matter_result = await db.execute(matter_query)
    matter = matter_result.scalar()
    
    # Get all access records for this matter
    access_query = (
        select(MatterAccessModel)
        .where(MatterAccessModel.matter_id == matter_id)
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
        matter_id=matter_id,
        matter_number=matter.matter_number,
        client_name=matter.client_name
    )

@router.post("/{matter_id}/access", response_model=MatterAccess, status_code=status.HTTP_201_CREATED)
async def grant_matter_access(
    matter_id: UUID,
    access_data: MatterAccessCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Grant access to a matter for a user."""
    # Check if current user has access to manage this matter
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.matter_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.access_role.in_(["lead_attorney", "partner"])
        )
    )
    access_result = await db.execute(access_query)
    if not access_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to manage access for this matter"
        )
    
    # Check if user already has access
    existing_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.matter_id == matter_id,
            MatterAccessModel.user_id == access_data.user_id
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has access to this matter"
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
        matter_id=matter_id,
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
            MatterAccessModel.matter_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.access_role.in_(["lead_attorney", "partner"])
        )
    )
    manager_result = await db.execute(manager_query)
    if not manager_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to manage access for this matter"
        )
    
    # Get access record
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.id == access_id,
            MatterAccessModel.matter_id == matter_id
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
            MatterAccessModel.matter_id == matter_id,
            MatterAccessModel.user_id == current_user.id,
            MatterAccessModel.access_role.in_(["lead_attorney", "partner"])
        )
    )
    manager_result = await db.execute(manager_query)
    if not manager_result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to manage access for this matter"
        )
    
    # Get access record
    access_query = select(MatterAccessModel).where(
        and_(
            MatterAccessModel.id == access_id,
            MatterAccessModel.matter_id == matter_id
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
    if access_record.access_role == "lead_attorney":
        lead_count_query = select(func.count()).where(
            and_(
                MatterAccessModel.matter_id == matter_id,
                MatterAccessModel.access_role == "lead_attorney"
            )
        )
        lead_count_result = await db.execute(lead_count_query)
        if lead_count_result.scalar() <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last lead attorney from a matter"
            )
    
    # Delete access record
    await db.delete(access_record)
    await db.commit()