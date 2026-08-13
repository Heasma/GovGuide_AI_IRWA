"""
GovGuide AI — Shared SQLAlchemy Base and column helpers.

All ORM models import Base, uuid_pk, and now from here.
This ensures a single metadata registry for Alembic discovery.
"""

import uuid
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base  # single source-of-truth Base


# ── Column helpers ────────────────────────────────────────────────────────────

def uuid_pk():
    """UUID v4 primary key column."""
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def now():
    """Timestamp column defaulting to current UTC time (server-side)."""
    return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


__all__ = ["Base", "uuid_pk", "now"]
