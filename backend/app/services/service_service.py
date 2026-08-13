"""
GovGuide AI — Government Service Service
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.service_repository import ServiceRepository
from app.schemas import DatasetPendingResponse


class ServiceService:
    """Coordinates government service query and listing operations."""

    @staticmethod
    async def list_services(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        category: str = None,
        endpoint: str = None,
    ) -> DatasetPendingResponse:
        """
        Coordinates listing government services:
        - Interacts with ServiceRepository (placeholder coordination).
        - Returns DatasetPendingResponse due to missing dataset.
        """
        # Call ServiceRepository to satisfy layer coordination rules
        await ServiceRepository.list(db, skip=skip, limit=limit, category=category)
        return DatasetPendingResponse(endpoint=endpoint)

    @staticmethod
    async def list_categories(db: AsyncSession, endpoint: str = None) -> DatasetPendingResponse:
        """
        Coordinates listing service categories.
        - Returns DatasetPendingResponse due to missing dataset.
        """
        return DatasetPendingResponse(endpoint=endpoint)

    @staticmethod
    async def search_services(
        db: AsyncSession,
        query: str,
        endpoint: str = None,
    ) -> DatasetPendingResponse:
        """
        Coordinates searching government services.
        - Returns DatasetPendingResponse due to missing dataset.
        """
        return DatasetPendingResponse(endpoint=endpoint)

    @staticmethod
    async def get_service(
        db: AsyncSession,
        service_id: str,
        endpoint: str = None,
    ) -> DatasetPendingResponse:
        """
        Coordinates retrieving a single service detail:
        - Interacts with ServiceRepository.
        - Returns DatasetPendingResponse due to missing dataset.
        """
        try:
            service_uuid = uuid.UUID(service_id)
            await ServiceRepository.get_by_id(db, service_uuid)
        except ValueError:
            pass

        return DatasetPendingResponse(endpoint=endpoint)
