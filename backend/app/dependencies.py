"""
GovGuide AI — FastAPI Dependencies
Shared dependencies injected across routers.
"""

import sys
import os

# Allow imports from project root (database/, etc.)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.database import get_db
from app.security.rbac import get_current_user, require_role, require_admin, require_citizen, Role

__all__ = [
    "get_db",
    "get_current_user",
    "require_role",
    "require_admin",
    "require_citizen",
    "Role",
]
