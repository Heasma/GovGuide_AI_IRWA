"""
GovGuide AI — Pydantic Schema Registry
"""

from app.schemas.auth_schema import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfile,
)
from app.schemas.query_schema import (
    SourceReference,
    QueryRequest,
    QueryResponse,
    FeedbackRequest,
)
from app.schemas.service_schema import (
    DatasetPendingResponse,
    GovernmentOfficeResponse,
    GovernmentServiceResponse,
    ServiceListResponse,
    CategoryListResponse,
    ServiceSearchResponse,
)
from app.schemas.session_schema import (
    SessionSummary,
    MessageRecord,
)
from app.schemas.admin_schema import (
    AdminUserRecord,
    AdminAuditLogRecord,
    AdminAgentLogRecord,
)
from app.schemas.response_schema import (
    HealthResponse,
    ErrorResponse,
)

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "RefreshTokenRequest",
    "TokenResponse",
    "UserProfile",
    "SourceReference",
    "QueryRequest",
    "QueryResponse",
    "FeedbackRequest",
    "DatasetPendingResponse",
    "GovernmentOfficeResponse",
    "GovernmentServiceResponse",
    "ServiceListResponse",
    "CategoryListResponse",
    "ServiceSearchResponse",
    "SessionSummary",
    "MessageRecord",
    "AdminUserRecord",
    "AdminAuditLogRecord",
    "AdminAgentLogRecord",
    "HealthResponse",
    "ErrorResponse",
]
