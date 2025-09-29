# app/services/auth.py - Authentication service

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime
import uuid
import logging

from app.models.models import User, Company, Group, UserGroup
from app.schemas.auth import UserCreate, UserLogin, CompanyCreate, CompanyRegistration
from app.utils.auth import verify_password, get_password_hash, create_user_token
from app.core.config import settings

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for BC Legal Tech"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_company_with_admin(self, registration: CompanyRegistration) -> tuple[Company, User]:
        """Create a new company with admin user and default groups"""
        
        # Check if company name already exists
        existing_company = await self.db.execute(
            select(Company).where(Company.name == registration.company_name)
        )
        if existing_company.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name already exists"
            )
        
        # Check if admin email already exists
        existing_user = await self.db.execute(
            select(User).where(User.email == registration.admin_email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        try:
            # Create company
            company = Company(
                id=uuid.uuid4(),
                name=registration.company_name,
                plan_tier=registration.plan_tier,
                subscription_status="trial"
            )
            self.db.add(company)
            await self.db.flush()  # Get the company ID
            
            # Create admin user
            admin_user = User(
                id=uuid.uuid4(),
                email=registration.admin_email,
                password_hash=get_password_hash(registration.admin_password),
                first_name=registration.admin_first_name,
                last_name=registration.admin_last_name,
                is_admin=True,
                company_id=company.id
            )
            self.db.add(admin_user)
            await self.db.flush()  # Get the user ID
            
            # Create default groups
            default_groups = await self._create_default_groups(company.id)
            
            # Assign admin to Administrator group
            admin_group = next((g for g in default_groups if g.name == "Administrators"), None)
            if admin_group:
                user_group = UserGroup(
                    user_id=admin_user.id,
                    group_id=admin_group.id,
                    assigned_by=admin_user.id
                )
                self.db.add(user_group)
            
            await self.db.commit()
            
            logger.info(f"Created company '{company.name}' with admin user '{admin_user.email}'")
            return company, admin_user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create company: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create company"
            )
    
    async def _create_default_groups(self, company_id: uuid.UUID) -> list[Group]:
        """Create default groups for a new company"""
        default_groups_data = [
            {
                "name": "Administrators",
                "description": "Full system access and user management",
                "permissions": [
                    "manage_users", "manage_documents", "manage_settings",
                    "view_analytics", "export_data", "manage_billing"
                ]
            },
            {
                "name": "Partners",
                "description": "Senior legal professionals with broad access",
                "permissions": [
                    "upload_documents", "chat_advanced", "view_analytics",
                    "export_conversations", "manage_team_documents"
                ]
            },
            {
                "name": "Associates",
                "description": "Legal professionals with standard access",
                "permissions": [
                    "upload_documents", "chat_basic", "export_conversations"
                ]
            },
            {
                "name": "Paralegals",
                "description": "Support staff with limited access",
                "permissions": [
                    "chat_basic", "view_documents"
                ]
            },
            {
                "name": "Guests",
                "description": "Read-only access for external users",
                "permissions": [
                    "chat_basic"
                ]
            }
        ]
        
        groups = []
        for group_data in default_groups_data:
            group = Group(
                id=uuid.uuid4(),
                company_id=company_id,
                name=group_data["name"],
                description=group_data["description"],
                permissions_json=group_data["permissions"],
                is_default=True
            )
            self.db.add(group)
            groups.append(group)
        
        return groups
    
    async def authenticate_user(self, login: UserLogin) -> tuple[User, Company]:
        """Authenticate user and return user with company"""
        
        # Find user by email
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.company))
            .where(User.email == login.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        if not verify_password(login.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last active timestamp
        user.last_active = datetime.utcnow()
        await self.db.commit()
        
        return user, user.company
    
    async def get_user_permissions(self, user_id: uuid.UUID) -> list[str]:
        """Get all permissions for a user based on their groups"""
        
        result = await self.db.execute(
            select(Group.permissions_json)
            .join(UserGroup, Group.id == UserGroup.group_id)
            .where(UserGroup.user_id == user_id)
        )
        
        all_permissions = set()
        for row in result:
            permissions = row[0] if isinstance(row[0], list) else []
            all_permissions.update(permissions)
        
        return list(all_permissions)
    
    async def create_user_auth_token(self, user: User) -> str:
        """Create authentication token for user"""
        
        # Get user permissions
        permissions = await self.get_user_permissions(user.id)
        
        # Create JWT token
        token = create_user_token(
            user_id=str(user.id),
            company_id=str(user.company_id),
            is_admin=user.is_admin,
            permissions=permissions
        )
        
        return token
    