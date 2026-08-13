"""
GovGuide AI — Generic Response Schemas
"""

from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    agents: dict


class ErrorResponse(BaseModel):
    detail: str
    request_id: Optional[str] = None
