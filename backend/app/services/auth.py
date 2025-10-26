# app/services/auth.py - Authentication service

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime
import uuid
import logging

from app.models.models import User, Company, Group, UserGroup, RefreshToken, PasswordResetToken
from app.schemas.auth import UserCreate, UserLogin, CompanyCreate, CompanyRegistration
from app.utils.auth import (
    verify_password, get_password_hash, create_user_token,
    create_refresh_token_jwt, hash_refresh_token, verify_token
)
from app.core.config import settings
import secrets

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

    async def create_refresh_token(self, user: User) -> str:
        """Create and store refresh token for user"""
        from datetime import timedelta

        # Create refresh token JWT
        refresh_token = create_refresh_token_jwt(
            user_id=str(user.id),
            company_id=str(user.company_id)
        )

        # Hash the token for storage
        token_hash = hash_refresh_token(refresh_token)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        # Store in database
        db_refresh_token = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(db_refresh_token)
        await self.db.commit()

        return refresh_token

    async def verify_refresh_token(self, refresh_token: str) -> tuple[User, Company]:
        """Verify refresh token and return user with company"""

        # First verify the JWT structure and expiration
        payload = verify_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Hash the token to look up in database
        token_hash = hash_refresh_token(refresh_token)

        # Find the refresh token in database
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
        )
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )

        # Check if token is revoked
        if db_token.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )

        # Check if token is expired
        if db_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )

        # Get user with company
        user_id = payload.get("sub")
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.company))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )

        return user, user.company

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revoke a refresh token"""
        token_hash = hash_refresh_token(refresh_token)

        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
        )
        db_token = result.scalar_one_or_none()

        if db_token:
            db_token.is_revoked = True
            db_token.revoked_at = datetime.utcnow()
            await self.db.commit()

    async def request_password_reset(self, email: str) -> str:
        """
        Request password reset for user

        Returns the reset token (for email sending)
        Note: Returns a token even if user doesn't exist (security best practice to prevent email enumeration)
        """
        from datetime import timedelta
        from hashlib import sha256

        # Find user by email
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        # Generate token regardless (prevent email enumeration)
        reset_token = secrets.token_urlsafe(32)

        if user:
            # Hash the token for storage
            token_hash = sha256(reset_token.encode()).hexdigest()

            # Invalidate any existing reset tokens for this user
            existing_tokens = await self.db.execute(
                select(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.is_used == False
                )
            )
            for token in existing_tokens.scalars():
                token.is_used = True
                token.used_at = datetime.utcnow()

            # Create new reset token (expires in 1 hour)
            expires_at = datetime.utcnow() + timedelta(hours=1)

            db_reset_token = PasswordResetToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at
            )
            self.db.add(db_reset_token)
            await self.db.commit()

            logger.info(f"Password reset requested for user {user.email}")
        else:
            logger.warning(f"Password reset requested for non-existent email: {email}")

        return reset_token

    async def verify_password_reset_token(self, token: str) -> bool:
        """
        Verify if password reset token is valid

        Returns True if valid, False otherwise
        """
        from hashlib import sha256

        token_hash = sha256(token.encode()).hexdigest()

        result = await self.db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
        )
        db_token = result.scalar_one_or_none()

        if not db_token:
            return False

        if db_token.is_used:
            return False

        if db_token.expires_at < datetime.utcnow():
            return False

        return True

    async def reset_password(self, token: str, new_password: str) -> User:
        """
        Reset user password with valid token

        Returns the user if successful
        Raises HTTPException if token is invalid
        """
        from hashlib import sha256

        token_hash = sha256(token.encode()).hexdigest()

        # Find the reset token
        result = await self.db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
        )
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        if db_token.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has already been used"
            )

        if db_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )

        # Get the user
        user_result = await self.db.execute(
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

        # Update password
        user.password_hash = get_password_hash(new_password)

        # Mark token as used
        db_token.is_used = True
        db_token.used_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Password reset successful for user {user.email}")

        return user
