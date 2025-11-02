# app/services/users.py - User management service

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import uuid
import logging
import secrets

from app.models.models import User, Company, Group, UserGroup
from app.schemas.users import UserInvite, UserUpdate, UserGroupAssignment
from app.utils.auth import get_password_hash

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing users within a company"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def invite_user(
        self,
        user_invite: UserInvite,
        company_id: uuid.UUID,
        invited_by: uuid.UUID
    ) -> tuple[User, str]:
        """
        Invite a new user to the company

        Returns:
            tuple[User, str]: The created user and the password reset token for invitation
        """

        # Check if email already exists in this company
        existing_user = await self.db.execute(
            select(User).where(
                User.email == user_invite.email,
                User.company_id == company_id
            )
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists in your company"
            )

        # Verify groups belong to this company
        if user_invite.group_ids:
            groups_result = await self.db.execute(
                select(Group).where(
                    Group.id.in_(user_invite.group_ids),
                    Group.company_id == company_id
                )
            )
            groups = groups_result.scalars().all()
            if len(groups) != len(user_invite.group_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more groups not found in your company"
                )

        try:
            # Create user as inactive - they must set password to activate
            # Use a placeholder password hash (user cannot log in with this)
            new_user = User(
                id=uuid.uuid4(),
                email=user_invite.email,
                password_hash=get_password_hash(secrets.token_urlsafe(32)),  # Random, unusable password
                first_name=user_invite.first_name,
                last_name=user_invite.last_name,
                is_active=False,  # Inactive until they set their password
                is_admin=False,
                company_id=company_id
            )
            self.db.add(new_user)
            await self.db.flush()

            # Assign to groups
            for group_id in user_invite.group_ids:
                user_group = UserGroup(
                    user_id=new_user.id,
                    group_id=group_id,
                    assigned_by=invited_by
                )
                self.db.add(user_group)

            await self.db.commit()

            # Generate password reset token for invitation
            from app.services.auth import AuthService
            auth_service = AuthService(self.db)
            invitation_token, _ = await auth_service.request_password_reset(new_user.email)

            logger.info(f"User {new_user.email} invited to company {company_id}")

            return new_user, invitation_token

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to invite user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to invite user"
            )
    
    async def list_company_users(self, company_id: uuid.UUID, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
        """List all users in a company with pagination"""
        
        # Get total count
        count_result = await self.db.execute(
            select(func.count(User.id)).where(User.company_id == company_id)
        )
        total = count_result.scalar()
        
        # Get paginated users with groups
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_groups).selectinload(UserGroup.group))
            .where(User.company_id == company_id)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        users = result.scalars().all()
        
        return users, total
    
    async def get_user_by_id(self, user_id: uuid.UUID, company_id: uuid.UUID) -> User:
        """Get user details by ID"""
        
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_groups).selectinload(UserGroup.group))
            .where(
                User.id == user_id,
                User.company_id == company_id
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    
    async def update_user(self, user_id: uuid.UUID, company_id: uuid.UUID, user_update: UserUpdate) -> User:
        """Update user information"""
        
        user = await self.get_user_by_id(user_id, company_id)
        
        # Update fields if provided
        if user_update.first_name is not None:
            user.first_name = user_update.first_name
        if user_update.last_name is not None:
            user.last_name = user_update.last_name
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        
        try:
            await self.db.commit()
            logger.info(f"Updated user {user.email}")
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
    
    async def assign_user_groups(self, user_id: uuid.UUID, company_id: uuid.UUID, assignment: UserGroupAssignment, assigned_by: uuid.UUID) -> User:
        """Assign user to groups (replaces existing assignments)"""
        
        user = await self.get_user_by_id(user_id, company_id)
        
        # Verify groups belong to this company
        if assignment.group_ids:
            groups_result = await self.db.execute(
                select(Group).where(
                    Group.id.in_(assignment.group_ids),
                    Group.company_id == company_id
                )
            )
            groups = groups_result.scalars().all()
            if len(groups) != len(assignment.group_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more groups not found in your company"
                )
        
        try:
            # Remove existing group assignments
            await self.db.execute(
                select(UserGroup).where(UserGroup.user_id == user_id)
            )
            existing_assignments = await self.db.execute(
                select(UserGroup).where(UserGroup.user_id == user_id)
            )
            for assignment_obj in existing_assignments.scalars():
                await self.db.delete(assignment_obj)
            
            # Add new group assignments
            for group_id in assignment.group_ids:
                user_group = UserGroup(
                    user_id=user_id,
                    group_id=group_id,
                    assigned_by=assigned_by
                )
                self.db.add(user_group)
            
            await self.db.commit()
            
            # Reload user with new groups
            return await self.get_user_by_id(user_id, company_id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to assign user groups: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign user groups"
            )