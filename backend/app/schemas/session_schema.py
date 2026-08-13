"""
GovGuide AI — Session Schemas
"""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.schemas.query_schema import SourceReference


class SessionSummary(BaseModel):
    session_id: str
    started_at: datetime
    message_count: int


class MessageRecord(BaseModel):
    message_id: str
    role: str
    content: str
    confidence_score: Optional[float] = None
    sources: List[SourceReference] = []
    created_at: datetime
