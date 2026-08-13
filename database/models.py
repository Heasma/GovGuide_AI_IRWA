"""
GovGuide AI — SQLAlchemy ORM Models (compatibility shim)

The canonical model definitions have been moved to:

    backend/app/models/user.py
    backend/app/models/conversation.py
    backend/app/models/government_service.py
    backend/app/models/official_source.py

This file re-exports all models from those locations so that any
code still using `from database.models import ...` continues to work.

NOTE: This shim depends on the backend being in sys.path (which it is
when running from the backend/ directory or via the dependencies.py
PROJECT_ROOT path setup).
"""

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
