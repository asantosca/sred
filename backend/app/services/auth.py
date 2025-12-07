# app/services/auth.py - Authentication service

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime, timezone
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
        
        # Check if company name already exists and its activation status
        existing_company = await self.db.execute(
            select(Company).where(Company.name == registration.company_name)
        )
        existing_company_obj = existing_company.scalar_one_or_none()

        if existing_company_obj and existing_company_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name already exists"
            )

        # Check if admin email already exists and is active
        existing_user = await self.db.execute(
            select(User).where(User.email == registration.admin_email)
        )
        existing_user_obj = existing_user.scalar_one_or_none()

        if existing_user_obj and existing_user_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        try:
            # Create or update company (inactive until admin email confirmation)
            if existing_company_obj:
                # Reuse existing inactive company
                company = existing_company_obj
                company.plan_tier = registration.plan_tier
                company.subscription_status = "trial"
                company.is_active = False
            else:
                # Create new company
                company = Company(
                    id=uuid.uuid4(),
                    name=registration.company_name,
                    plan_tier=registration.plan_tier,
                    subscription_status="trial",
                    is_active=False
                )
                self.db.add(company)
            await self.db.flush()  # Get the company ID

            # Create or update admin user (inactive until email confirmation)
            if existing_user_obj:
                # Reuse existing inactive user
                admin_user = existing_user_obj
                admin_user.password_hash = get_password_hash(registration.admin_password)
                admin_user.first_name = registration.admin_first_name
                admin_user.last_name = registration.admin_last_name
                admin_user.is_admin = True
                admin_user.is_active = False
                admin_user.company_id = company.id
            else:
                # Create new user
                admin_user = User(
                    id=uuid.uuid4(),
                    email=registration.admin_email,
                    password_hash=get_password_hash(registration.admin_password),
                    first_name=registration.admin_first_name,
                    last_name=registration.admin_last_name,
                    is_admin=True,
                    is_active=False,
                    company_id=company.id
                )
                self.db.add(admin_user)
            await self.db.flush()  # Get the user ID
            
            # Create default groups (or get existing ones if company existed)
            default_groups = await self._create_default_groups(company.id, skip_if_exist=bool(existing_company_obj))

            # Assign admin to Administrator group (check if assignment already exists)
            admin_group = next((g for g in default_groups if g.name == "Administrators"), None)
            if admin_group:
                # Check if user is already assigned to this group
                existing_assignment = await self.db.execute(
                    select(UserGroup).where(
                        UserGroup.user_id == admin_user.id,
                        UserGroup.group_id == admin_group.id
                    )
                )
                if not existing_assignment.scalar_one_or_none():
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
    
    async def _create_default_groups(self, company_id: uuid.UUID, skip_if_exist: bool = False) -> list[Group]:
        """Create default groups for a new company"""

        # If company already existed, fetch and return existing groups
        if skip_if_exist:
            result = await self.db.execute(
                select(Group).where(
                    Group.company_id == company_id,
                    Group.is_default == True
                )
            )
            existing_groups = list(result.scalars().all())
            if existing_groups:
                return existing_groups

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
                detail="Account is disabled. Did you validate your email?"
            )
        
        if not verify_password(login.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update last active timestamp
        user.last_active = datetime.now(timezone.utc)
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
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

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
        if db_token.expires_at < datetime.now(timezone.utc):
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
            db_token.revoked_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def revoke_all_user_refresh_tokens(self, user_id: uuid.UUID) -> None:
        """Revoke all refresh tokens for a user (used when password changes)"""
        result = await self.db.execute(
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            token.is_revoked = True
            token.revoked_at = datetime.now(timezone.utc)

        if tokens:
            await self.db.commit()
            logger.info(f"Revoked {len(tokens)} refresh tokens for user {user_id}")

    async def request_password_reset(
        self,
        email: str,
        expires_in_days: int = 0,
        expires_in_hours: int = 1
    ) -> tuple[str, bool]:
        """
        Request password reset for user

        Args:
            email: User's email address
            expires_in_days: Token expiration in days (default 0)
            expires_in_hours: Token expiration in hours (default 1)
                For password reset: use default (1 hour)
                For email confirmation: use expires_in_days=5

        Returns: (reset_token, user_exists)
        Note: Always generates a token (security best practice to prevent timing attacks),
        but only saves it to database if user exists
        """
        from datetime import timedelta
        from hashlib import sha256

        # Find user by email
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        # Generate token regardless (prevent timing attacks)
        reset_token = secrets.token_urlsafe(32)
        user_exists = user is not None

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
                token.used_at = datetime.now(timezone.utc)

            # Create new reset token
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days, hours=expires_in_hours)

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

        return reset_token, user_exists

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

        if db_token.expires_at < datetime.now(timezone.utc):
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

        if db_token.expires_at < datetime.now(timezone.utc):
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

        # Activate user if they're not active (for email confirmation flow)
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

        await self.db.commit()

        logger.info(f"Password reset successful for user {user.email}")

        return user
