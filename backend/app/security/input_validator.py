"""
GovGuide AI — Input Validator
Validates and sanitizes user-supplied query strings before
they reach any agent or database layer.
"""

import re
from pydantic import BaseModel, field_validator

# ── Constants ─────────────────────────────────────────────────────────────────
MIN_QUERY_LENGTH = 3
MAX_QUERY_LENGTH = 1000
MAX_EMAIL_LENGTH = 255
MIN_PASSWORD_LENGTH = 8

# Characters that are never legitimate in a natural-language query
_SUSPICIOUS_PATTERN = re.compile(
    r"(<script|javascript:|data:|vbscript:|onload=|onerror=|<iframe|<img)",
    re.IGNORECASE,
)


class QueryInput(BaseModel):
    """Pydantic model for validating a user's natural-language query."""

    query: str

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()
        if len(value) < MIN_QUERY_LENGTH:
            raise ValueError(f"Query must be at least {MIN_QUERY_LENGTH} characters.")
        if len(value) > MAX_QUERY_LENGTH:
            raise ValueError(f"Query must not exceed {MAX_QUERY_LENGTH} characters.")
        if _SUSPICIOUS_PATTERN.search(value):
            raise ValueError("Query contains disallowed content.")
        return value


def sanitize_query(raw_query: str) -> str:
    """
    Sanitize a raw query string.
    Strips leading/trailing whitespace and collapses internal whitespace.
    Raises ValueError if the query fails validation.
    """
    validated = QueryInput(query=raw_query)
    # Collapse multiple spaces
    return re.sub(r"\s+", " ", validated.query)


def validate_email(email: str) -> str:
    """Basic email format validation."""
    email = email.strip().lower()
    if len(email) > MAX_EMAIL_LENGTH:
        raise ValueError("Email address is too long.")
    pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    if not pattern.match(email):
        raise ValueError("Invalid email address format.")
    return email


def validate_password_strength(password: str) -> None:
    """
    Basic password strength check.
    Phase 1: Minimum length only.
    Phase 2: Can add complexity rules.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
