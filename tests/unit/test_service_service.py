"""
Unit tests — ServiceService
"""

import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from app.services.service_service import ServiceService
from app.schemas.service_schema import (
    ServiceListResponse,
    CategoryListResponse,
    ServiceSearchResponse,
    GovernmentServiceResponse,
)
from app.models.government_service import GovernmentService, GovernmentOffice


def _make_mock_service(service_code="1006", name="Retail Food Establishment"):
    svc = MagicMock(spec=GovernmentService)
    svc.id = uuid.uuid4()
    svc.service_code = service_code
    svc.name = name
    svc.description = "Test Description"
    svc.category = "Food & Beverage"
    svc.is_active = True
    svc.source_url = "https://chicago.gov"
    svc.license_term_years = 2
    svc.fee_amount = "$660.00"
    svc.fee_description = None
    svc.application_portal_url = None
    svc.eligibility_summary = None
    svc.required_documents = None
    svc.application_steps = None
    svc.inspection_required = True
    svc.renewal_required = True
    svc.renewal_period = "2 years"
    svc.legal_reference = None
    svc.source_confidence = "VERIFIED"
    svc.office = None
    return svc


@pytest.mark.anyio
async def test_list_services():
    db = AsyncMock()
    mock_svc = _make_mock_service()
    
    with patch("app.repositories.service_repository.ServiceRepository.list", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = ([mock_svc], 1)
        
        response = await ServiceService.list_services(db, skip=0, limit=10, category="Food & Beverage")
        
        assert isinstance(response, ServiceListResponse)
        assert response.total == 1
        assert response.items[0].service_code == "1006"
        mock_list.assert_called_once_with(db, skip=0, limit=10, category="Food & Beverage")


@pytest.mark.anyio
async def test_list_categories():
    db = AsyncMock()
    
    with patch("app.repositories.service_repository.ServiceRepository.list_categories", new_callable=AsyncMock) as mock_cat:
        mock_cat.return_value = ["Food & Beverage", "Retail"]
        
        response = await ServiceService.list_categories(db)
        
        assert isinstance(response, CategoryListResponse)
        assert response.total == 2
        assert "Food & Beverage" in response.categories
        mock_cat.assert_called_once_with(db)


@pytest.mark.anyio
async def test_search_services():
    db = AsyncMock()
    mock_svc = _make_mock_service(service_code="1006", name="Retail Food")
    
    with patch("app.repositories.service_repository.ServiceRepository.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = ([mock_svc], 1)
        
        response = await ServiceService.search_services(db, query="food", skip=0, limit=10)
        
        assert isinstance(response, ServiceSearchResponse)
        assert response.query == "food"
        assert response.total == 1
        assert response.items[0].service_code == "1006"
        mock_search.assert_called_once_with(db, query_str="food", skip=0, limit=10)


@pytest.mark.anyio
async def test_get_service_success():
    db = AsyncMock()
    mock_svc = _make_mock_service()
    service_id = str(mock_svc.id)
    
    with patch("app.repositories.service_repository.ServiceRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
        mock_get_by_id.return_value = mock_svc
        
        response = await ServiceService.get_service(db, service_id=service_id)
        
        assert isinstance(response, GovernmentServiceResponse)
        assert response.id == mock_svc.id
        assert response.service_code == "1006"
        mock_get_by_id.assert_called_once_with(db, mock_svc.id)


@pytest.mark.anyio
async def test_get_service_not_found():
    db = AsyncMock()
    service_id = str(uuid.uuid4())
    
    with patch("app.repositories.service_repository.ServiceRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
        mock_get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await ServiceService.get_service(db, service_id=service_id)
        assert exc_info.value.status_code == 404
