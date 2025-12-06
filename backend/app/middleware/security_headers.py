# app/middleware/security_headers.py - Security Headers Middleware

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements:
    - Content Security Policy (CSP) - prevents XSS attacks
    - X-Content-Type-Options - prevents MIME sniffing
    - X-Frame-Options - prevents clickjacking
    - X-XSS-Protection - legacy XSS protection
    - Referrer-Policy - controls referrer information
    - Permissions-Policy - restricts browser features
    - Strict-Transport-Security - enforces HTTPS (production only)
    """

    def __init__(self, app):
        super().__init__(app)
        self.is_production = settings.ENVIRONMENT == "production"

        # Build CSP based on environment
        self.csp = self._build_csp()

    def _build_csp(self) -> str:
        """Build Content Security Policy header value"""

        # Build connect-src with external APIs
        connect_sources = "'self' https://api.anthropic.com https://api.openai.com"
        if settings.SENTRY_DSN:
            connect_sources += " https://*.ingest.sentry.io"

        # Base CSP directives
        directives = [
            # Default: only allow resources from same origin
            "default-src 'self'",

            # Scripts: only from same origin (blocks injected scripts)
            "script-src 'self'",

            # Styles: same origin + inline (Tailwind requires unsafe-inline)
            "style-src 'self' 'unsafe-inline'",

            # Images: same origin + data URIs + HTTPS (for avatars, etc.)
            "img-src 'self' data: https:",

            # Fonts: same origin
            "font-src 'self'",

            # API connections: same origin + external APIs + Sentry
            f"connect-src {connect_sources}",

            # Frames: none (prevents clickjacking)
            "frame-ancestors 'none'",

            # Base URI: same origin (prevents base tag injection)
            "base-uri 'self'",

            # Form submissions: same origin only
            "form-action 'self'",

            # Object/embed: none (blocks Flash, etc.)
            "object-src 'none'",
        ]

        # Add upgrade-insecure-requests in production
        if self.is_production:
            directives.append("upgrade-insecure-requests")

        return "; ".join(directives)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking (legacy, CSP frame-ancestors is preferred)
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"

        # HSTS - only in production with HTTPS
        if self.is_production:
            # max-age=31536000 = 1 year, includeSubDomains for all subdomains
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
