# app/utils/auth.py - Authentication utilities with proper bcrypt

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
import secrets
import hashlib

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate password hash with bcrypt"""
    try:
        # Bcrypt has a 72-byte limit, handle long passwords
        if len(password.encode('utf-8')) > 72:
            logger.warning("Password exceeds 72 bytes, truncating")
            password = password[:72]
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise ValueError("Failed to hash password")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def create_user_token(user_id: str, company_id: str, is_admin: bool = False, permissions: list = None) -> str:
    """Create JWT token for user with company and permission info"""
    if permissions is None:
        permissions = []
    
    token_data = {
        "sub": str(user_id),  # Subject (user ID)
        "company_id": str(company_id),
        "is_admin": is_admin,
        "permissions": permissions,
        "type": "access"
    }
    
    return create_access_token(token_data)

def extract_token_data(token: str) -> Optional[Dict[str, Any]]:
    """Extract user data from JWT token"""
    payload = verify_token(token)
    if not payload:
        return None

    return {
        "user_id": payload.get("sub"),
        "company_id": payload.get("company_id"),
        "is_admin": payload.get("is_admin", False),
        "permissions": payload.get("permissions", [])
    }

def create_refresh_token() -> str:
    """Generate a secure random refresh token"""
    return secrets.token_urlsafe(32)

def hash_refresh_token(token: str) -> str:
    """Create a secure hash of the refresh token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def create_refresh_token_jwt(user_id: str, company_id: str) -> str:
    """Create JWT refresh token with extended expiration"""
    token_data = {
        "sub": str(user_id),
        "company_id": str(company_id),
        "type": "refresh"
    }

    expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(token_data, expires_delta)