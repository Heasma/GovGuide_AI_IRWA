"""
GovGuide AI — Query Schemas
"""

from pydantic import BaseModel, field_validator
from typing import List, Optional
from app.security.input_validator import sanitize_query


class SourceReference(BaseModel):
    """A single evidence source returned with an AI response."""
    source_id: str
    title: str
    url: Optional[str] = None
    excerpt: Optional[str] = None


class QueryRequest(BaseModel):
    """User's natural language query to the AI assistant."""
    query: str
    session_id: Optional[str] = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        from app.security.input_validator import sanitize_query
        return sanitize_query(v)


class QueryResponse(BaseModel):
    """The complete response from the AI query pipeline."""
    request_id: str
    answer: str
    confidence_score: float
    confidence_label: str   # high | medium | low | insufficient
    sources: List[SourceReference] = []
    caveats: List[str] = []
    explanation: Optional[str] = None
    is_demo: bool = False   # True when returning stub/mock data


class FeedbackRequest(BaseModel):
    """User feedback on an AI response."""
    rating: int          # 1 = helpful, -1 = not helpful
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if v not in (-1, 1):
            raise ValueError("Rating must be 1 (helpful) or -1 (not helpful).")
        return v
