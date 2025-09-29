# app/utils/auth.py - Temporary fix for password hashing

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import hashlib
import os

from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash - temporary simple implementation"""
    # Simple SHA256 hash for testing (NOT for production)
    test_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return test_hash == hashed_password

def get_password_hash(password: str) -> str:
    """Generate password hash - temporary simple implementation"""
    # Simple SHA256 hash for testing (NOT for production)
    # TODO: Fix bcrypt and switch back to proper password hashing
    return hashlib.sha256(password.encode()).hexdigest()

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