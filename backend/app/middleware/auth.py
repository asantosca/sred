# app/middleware/auth.py - JWT Authentication Middleware

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
import logging

from app.core.config import settings
from app.core.tenant import TenantContext

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate JWT tokens from requests.
    Attaches tenant context to request.state for use in endpoints.
    """

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/test",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    }

    async def dispatch(self, request: Request, call_next):
        """Process request and attach tenant context if authenticated"""

        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract tenant context from JWT token
        tenant_context = await self._extract_tenant_context(request)

        # Attach tenant context to request state
        if tenant_context:
            request.state.tenant = tenant_context
            logger.debug(f"Authenticated request: user={tenant_context.user_id}, company={tenant_context.company_id}")
        else:
            # No valid token found - endpoint dependencies will enforce auth if needed
            request.state.tenant = None

        # Continue processing request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise

    async def _extract_tenant_context(self, request: Request) -> TenantContext | None:
        """Extract and validate JWT token from Authorization header"""

        # Get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            logger.debug("No Authorization header found")
            return None

        try:
            # Extract token from "Bearer <token>"
            parts = authorization.split()
            if len(parts) != 2:
                logger.warning("Invalid Authorization header format")
                return None

            scheme, token = parts
            if scheme.lower() != "bearer":
                logger.warning(f"Invalid auth scheme: {scheme}")
                return None

            # Decode and verify JWT token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Extract tenant information
            user_id = payload.get("sub")  # Subject = user ID
            company_id = payload.get("company_id")
            is_admin = payload.get("is_admin", False)
            permissions = payload.get("permissions", [])
            token_type = payload.get("type", "access")

            # Validate required fields
            if not user_id or not company_id:
                logger.warning("JWT missing required fields (sub or company_id)")
                return None

            # Ensure it's an access token (not refresh token)
            if token_type != "access":
                logger.warning(f"Invalid token type: {token_type}")
                return None

            # Create tenant context
            return TenantContext(
                company_id=company_id,
                user_id=user_id,
                is_admin=is_admin,
                permissions=permissions
            )

        except JWTError as e:
            logger.warning(f"JWT validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting tenant context: {e}")
            return None


async def get_current_user(request: Request) -> TenantContext:
    """
    FastAPI dependency to get current authenticated user.
    Raises 401 if not authenticated.

    Usage:
        @router.get("/protected")
        async def protected_endpoint(current_user: TenantContext = Depends(get_current_user)):
            ...
    """
    tenant_context = getattr(request.state, 'tenant', None)

    if not tenant_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return tenant_context


async def get_current_admin(request: Request) -> TenantContext:
    """
    FastAPI dependency to get current authenticated admin user.
    Raises 401 if not authenticated, 403 if not admin.

    Usage:
        @router.post("/admin-only")
        async def admin_endpoint(current_user: TenantContext = Depends(get_current_admin)):
            ...
    """
    tenant_context = await get_current_user(request)

    if not tenant_context.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return tenant_context


def require_permission(permission: str):
    """
    FastAPI dependency factory to require specific permission.

    Usage:
        @router.post("/documents/upload")
        async def upload(current_user: TenantContext = Depends(require_permission("upload_documents"))):
            ...
    """
    async def _check_permission(request: Request) -> TenantContext:
        tenant_context = await get_current_user(request)

        # Admins have all permissions
        if tenant_context.is_admin:
            return tenant_context

        # Check if user has the required permission
        if permission not in tenant_context.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )

        return tenant_context

    return _check_permission
