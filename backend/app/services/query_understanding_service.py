"""
GovGuide AI — Query Understanding Service (Service Layer Export)

Provides top-level access to the QueryUnderstandingService for API controllers,
middleware, and agent workflows.
"""

from app.nlp.query_understanding_service import (
    QueryUnderstandingService,
    QueryUnderstandingResult,
)

__all__ = [
    "QueryUnderstandingService",
    "QueryUnderstandingResult",
]
