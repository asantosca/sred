# app/core/tenant.py - Multi-tenant context management

from typing import Optional
from dataclasses import dataclass
from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class TenantContext:
    """Tenant context for multi-tenancy"""
    company_id: Optional[str] = None
    user_id: Optional[str] = None
    tenancy_type: str = "shared_rls"  # shared_rls, dedicated_schema, dedicated_instance
    is_admin: bool = False
    permissions: list = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []

async def get_tenant_context(request: Request) -> Optional[TenantContext]:
    """Extract tenant context from request"""
    
    # Skip tenant context for health checks and docs
    if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
        return None
    
    # Get authorization header
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extract tenant information
        company_id = payload.get("company_id")
        user_id = payload.get("sub")  # Subject = user ID
        is_admin = payload.get("is_admin", False)
        permissions = payload.get("permissions", [])
        
        if not company_id or not user_id:
            logger.warning("JWT missing required tenant information")
            return None
        
        return TenantContext(
            company_id=company_id,
            user_id=user_id,
            is_admin=is_admin,
            permissions=permissions
        )
        
    except (ValueError, JWTError) as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting tenant context: {e}")
        return None

def require_tenant_context(request: Request) -> TenantContext:
    """Dependency to require valid tenant context"""
    tenant_context = getattr(request.state, 'tenant', None)
    
    if not tenant_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return tenant_context

def require_admin(request: Request) -> TenantContext:
    """Dependency to require admin privileges"""
    tenant_context = require_tenant_context(request)
    
    if not tenant_context.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return tenant_context

def require_permission(permission: str):
    """Dependency factory to require specific permission"""
    def _require_permission(request: Request) -> TenantContext:
        tenant_context = require_tenant_context(request)
        
        if permission not in tenant_context.permissions and not tenant_context.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return tenant_context
    
    return _require_permission
