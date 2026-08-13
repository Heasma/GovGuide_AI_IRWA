"""
GovGuide AI — Government Service Schemas
"""

from pydantic import BaseModel
from typing import Optional


class DatasetPendingResponse(BaseModel):
    """
    Returned by government-service endpoints until real dataset is integrated.
    Clearly communicates that this is a deliberate placeholder, not a failure.
    """
    status: str = "dataset_pending"
    message: str = (
        "Government service data has not yet been integrated. "
        "This endpoint will return live data once the official dataset is available."
    )
    endpoint: Optional[str] = None
