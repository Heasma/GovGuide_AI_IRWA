"""
GovGuide AI — ORM Model Registry

Import all models here so that:
1. SQLAlchemy's Base.metadata is fully populated for Alembic.
2. Consumers can do: from app.models import User, QuerySession, ...
3. There is a single predictable import location for all ORM models.

Import order matters for FK resolution:
  base → user → conversation → government_service → official_source
"""

from app.models.base import Base  # noqa: F401  — exposes Base for Alembic
from app.models.user import User  # noqa: F401
from app.models.conversation import (  # noqa: F401
    QuerySession,
    ConversationMessage,
    AuditLog,
    AgentInteractionLog,
)
from app.models.government_service import (  # noqa: F401
    GovernmentOffice,
    GovernmentService,
)
from app.models.official_source import (  # noqa: F401
    OfficialSource,
    DocumentChunk,
)

__all__ = [
    "Base",
    "User",
    "QuerySession",
    "ConversationMessage",
    "AuditLog",
    "AgentInteractionLog",
    "GovernmentOffice",
    "GovernmentService",
    "OfficialSource",
    "DocumentChunk",
]
