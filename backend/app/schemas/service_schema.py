"""
GovGuide AI — Government Service Schemas
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DatasetPendingResponse(BaseModel):
    """
    Legacy schema for dataset pending status.
    """
    status: str = "dataset_pending"
    message: str = (
        "Government service data has not yet been integrated. "
        "This endpoint will return live data once the official dataset is available."
    )
    endpoint: Optional[str] = None


class GovernmentOfficeResponse(BaseModel):
    """Response schema for GovernmentOffice."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    department: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    business_hours: Optional[str] = None
    website_url: Optional[str] = None


class GovernmentServiceResponse(BaseModel):
    """Response schema for a single GovernmentService."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_code: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    source_url: Optional[str] = None
    license_term_years: Optional[int] = None
    fee_amount: Optional[str] = None
    fee_description: Optional[str] = None
    application_portal_url: Optional[str] = None
    eligibility_summary: Optional[str] = None
    required_documents: Optional[str] = None
    application_steps: Optional[str] = None
    inspection_required: Optional[bool] = None
    renewal_required: Optional[bool] = None
    renewal_period: Optional[str] = None
    legal_reference: Optional[str] = None
    source_confidence: Optional[str] = None
    office: Optional[GovernmentOfficeResponse] = None


class ServiceListResponse(BaseModel):
    """Paginated list of government services."""
    total: int
    items: List[GovernmentServiceResponse]


class CategoryListResponse(BaseModel):
    """List of service categories."""
    total: int
    categories: List[str]


class ServiceSearchResponse(BaseModel):
    """Search results response for government services."""
    query: str
    total: int
    items: List[GovernmentServiceResponse]


class OfficialSourceResponse(BaseModel):
    """Response schema for a single OfficialSource record."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class SourceListResponse(BaseModel):
    """Paginated list of official sources."""
    total: int
    items: List[OfficialSourceResponse]
