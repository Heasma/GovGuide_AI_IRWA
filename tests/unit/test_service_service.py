"""
Unit tests — ServiceService
"""

import pytest
import uuid
from unittest.mock import AsyncMock, patch

from app.services.service_service import ServiceService
from app.schemas import DatasetPendingResponse


@pytest.mark.anyio
async def test_list_services():
    db = AsyncMock()
    endpoint = "http://localhost/services"
    
    with patch("app.repositories.service_repository.ServiceRepository.list", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = []
        
        response = await ServiceService.list_services(db, skip=0, limit=10, category="health", endpoint=endpoint)
        
        assert isinstance(response, DatasetPendingResponse)
        assert response.status == "dataset_pending"
        assert response.endpoint == endpoint
        mock_list.assert_called_once_with(db, skip=0, limit=10, category="health")


@pytest.mark.anyio
async def test_list_categories():
    db = AsyncMock()
    endpoint = "http://localhost/services/categories"
    
    response = await ServiceService.list_categories(db, endpoint=endpoint)
    
    assert isinstance(response, DatasetPendingResponse)
    assert response.status == "dataset_pending"
    assert response.endpoint == endpoint


@pytest.mark.anyio
async def test_search_services():
    db = AsyncMock()
    endpoint = "http://localhost/services/search"
    
    response = await ServiceService.search_services(db, query="passport", endpoint=endpoint)
    
    assert isinstance(response, DatasetPendingResponse)
    assert response.status == "dataset_pending"
    assert response.endpoint == endpoint


@pytest.mark.anyio
async def test_get_service():
    db = AsyncMock()
    endpoint = "http://localhost/services/123"
    service_id = str(uuid.uuid4())
    
    with patch("app.repositories.service_repository.ServiceRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
        mock_get_by_id.return_value = None
        
        response = await ServiceService.get_service(db, service_id=service_id, endpoint=endpoint)
        
        assert isinstance(response, DatasetPendingResponse)
        assert response.status == "dataset_pending"
        assert response.endpoint == endpoint
        mock_get_by_id.assert_called_once_with(db, uuid.UUID(service_id))
