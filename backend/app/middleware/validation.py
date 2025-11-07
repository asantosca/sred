# app/middleware/validation.py - Input validation and sanitization middleware

import re
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate and sanitize incoming requests.

    Protects against:
    - Path traversal attacks
    - XSS attempts
    - SQL injection patterns (defense in depth, ORM handles this)
    - Malicious file uploads
    - Oversized requests
    """

    # Suspicious patterns that might indicate attacks
    SUSPICIOUS_PATTERNS = [
        r"\.\.\/",  # Path traversal
        r"\.\.\\",  # Path traversal (Windows)
        r"<script",  # XSS
        r"javascript:",  # XSS
        r"on\w+\s*=",  # Event handlers (XSS)
        r"UNION\s+SELECT",  # SQL injection
        r"DROP\s+TABLE",  # SQL injection
        r"INSERT\s+INTO",  # SQL injection
        r"DELETE\s+FROM",  # SQL injection
        r"--\s*$",  # SQL comment
        r"/\*.*\*/",  # SQL comment
    ]

    # Compile patterns for performance
    COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS]

    # Maximum request body size (50MB - same as upload limit)
    MAX_BODY_SIZE = 50 * 1024 * 1024

    async def dispatch(self, request: Request, call_next):
        """Process request through validation middleware"""

        try:
            # 1. Validate request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.MAX_BODY_SIZE:
                logger.warning(
                    f"Request too large: {content_length} bytes from {request.client.host}"
                )
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Request body too large"
                )

            # 2. Validate path for traversal attempts
            path = str(request.url.path)
            if self._is_suspicious(path):
                logger.warning(
                    f"Suspicious path detected: {path} from {request.client.host}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request path"
                )

            # 3. Validate query parameters
            for param_name, param_value in request.query_params.items():
                if self._is_suspicious(param_value):
                    logger.warning(
                        f"Suspicious query parameter '{param_name}': {param_value} "
                        f"from {request.client.host}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid query parameter: {param_name}"
                    )

            # 4. Validate headers
            # Check for suspicious user agents
            user_agent = request.headers.get("user-agent", "")
            if self._is_suspicious_user_agent(user_agent):
                logger.warning(
                    f"Suspicious user agent: {user_agent} from {request.client.host}"
                )
                # Don't block, just log - some legitimate tools have weird UAs

            # 5. Process request
            response = await call_next(request)

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Validation middleware error: {str(e)}", exc_info=True)
            # Let the request through if validation fails - fail open for availability
            return await call_next(request)

    def _is_suspicious(self, text: str) -> bool:
        """
        Check if text contains suspicious patterns.

        Args:
            text: Text to check

        Returns:
            True if suspicious patterns found
        """
        if not text:
            return False

        # Check against compiled patterns
        for pattern in self.COMPILED_PATTERNS:
            if pattern.search(text):
                return True

        return False

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """
        Check if user agent looks suspicious.

        Args:
            user_agent: User agent string

        Returns:
            True if suspicious
        """
        if not user_agent:
            return True  # Missing user agent is suspicious

        # Very basic check - just flag empty or very short UAs
        if len(user_agent) < 5:
            return True

        # Check for common attack tools (log only, don't block)
        attack_tools = ["sqlmap", "nikto", "nmap", "masscan", "burp"]
        user_agent_lower = user_agent.lower()

        for tool in attack_tools:
            if tool in user_agent_lower:
                return True

        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed_file"

    # Remove path components
    filename = filename.split("/")[-1]
    filename = filename.split("\\")[-1]

    # Remove or replace dangerous characters
    # Allow alphanumeric, dash, underscore, and dot
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Prevent multiple dots (could hide extensions)
    while ".." in filename:
        filename = filename.replace("..", ".")

    # Ensure it doesn't start with a dot
    if filename.startswith("."):
        filename = "file" + filename

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")

    return filename


def validate_uuid(value: str) -> bool:
    """
    Validate that a string is a valid UUID.

    Args:
        value: String to validate

    Returns:
        True if valid UUID format
    """
    uuid_pattern = re.compile(
        r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(value))


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input by removing potentially dangerous content.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text.strip()
