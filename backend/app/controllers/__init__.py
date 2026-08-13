"""
GovGuide AI — Controllers Registry
"""

from app.controllers.auth_controller import router as auth_router
from app.controllers.query_controller import router as query_router
from app.controllers.service_controller import router as service_router
from app.controllers.session_controller import router as session_router
from app.controllers.admin_controller import router as admin_router
from app.controllers.health_controller import router as health_router

__all__ = [
    "auth_router",
    "query_router",
    "service_router",
    "session_router",
    "admin_router",
    "health_router",
]
