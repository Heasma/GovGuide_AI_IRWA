"""
GovGuide AI — Admin Schemas
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AdminUserRecord(BaseModel):
    user_id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class AdminAuditLogRecord(BaseModel):
    id: str
    event_type: str
    outcome: Optional[str] = None
    user_id: Optional[str] = None
    resource: Optional[str] = None
    created_at: datetime


class AdminAgentLogRecord(BaseModel):
    id: str
    request_id: str
    agent_id: str
    message_type: str
    duration_ms: Optional[int] = None
    created_at: datetime
