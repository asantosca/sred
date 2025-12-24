# app/middleware/tenant_context.py - RLS Context Middleware

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.tenant import get_tenant_context
import logging

logger = logging.getLogger(__name__)

class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant context from JWT and attach to request state.

    The actual RLS context (`app.current_company_id`) is set by the `get_db` dependency
    in `app/db/session.py` which reads from `request.state.company_id`.

    This middleware ensures:
    1. JWT is decoded early in the request lifecycle
    2. company_id is attached to request.state for downstream use
    3. The get_db dependency can then set the PostgreSQL session variable
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract tenant context from JWT
        try:
            tenant_context = await get_tenant_context(request)
        except Exception:
            # If token extraction fails, proceed - auth dependencies will catch errors
            tenant_context = None

        # Attach company_id to request state for get_db dependency to use
        if tenant_context and tenant_context.company_id:
            request.state.company_id = tenant_context.company_id
            request.state.user_id = tenant_context.user_id
            request.state.is_admin = tenant_context.is_admin

        return await call_next(request)
