"""
GovGuide AI — Government Service Service
"""

import uuid
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.service_repository import ServiceRepository
from app.repositories.source_repository import SourceRepository
from app.schemas.service_schema import (
    GovernmentServiceResponse,
    ServiceListResponse,
    CategoryListResponse,
    ServiceSearchResponse,
    OfficialSourceResponse,
    SourceListResponse,
)


class ServiceService:
    """Coordinates government service query and listing operations."""

    @staticmethod
    async def list_services(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> ServiceListResponse:
        """
        Coordinates listing government services:
        - Retrieves paginated services from ServiceRepository.
        - Returns structured ServiceListResponse with real database records.
        """
        items, total = await ServiceRepository.list(
            db, skip=skip, limit=limit, category=category
        )
        return ServiceListResponse(
            total=total,
            items=[GovernmentServiceResponse.model_validate(item) for item in items],
        )

    @staticmethod
    async def list_categories(
        db: AsyncSession,
        endpoint: Optional[str] = None,
    ) -> CategoryListResponse:
        """
        Coordinates listing service categories:
        - Retrieves distinct categories from ServiceRepository.
        - Returns CategoryListResponse.
        """
        categories = await ServiceRepository.list_categories(db)
        return CategoryListResponse(
            total=len(categories),
            categories=categories,
        )

    @staticmethod
    async def search_services(
        db: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 50,
        endpoint: Optional[str] = None,
    ) -> ServiceSearchResponse:
        """
        Coordinates searching government services:
        - Performs text search across services using ServiceRepository.
        - Returns ServiceSearchResponse.
        """
        items, total = await ServiceRepository.search(
            db, query_str=query, skip=skip, limit=limit
        )
        return ServiceSearchResponse(
            query=query,
            total=total,
            items=[GovernmentServiceResponse.model_validate(item) for item in items],
        )

    @staticmethod
    async def get_service(
        db: AsyncSession,
        service_id: str,
        endpoint: Optional[str] = None,
    ) -> GovernmentServiceResponse:
        """
        Coordinates retrieving a single service detail:
        - Interacts with ServiceRepository.
        - Returns GovernmentServiceResponse or raises 404 if not found.
        """
        try:
            service_uuid = uuid.UUID(service_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid service UUID format")

        service = await ServiceRepository.get_by_id(db, service_uuid)
        if not service:
            raise HTTPException(status_code=404, detail="Government service not found")

        return GovernmentServiceResponse.model_validate(service)

    @staticmethod
    async def list_sources(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        endpoint: Optional[str] = None,
    ) -> SourceListResponse:
        """
        Coordinates listing official source documents.
        Returns structured SourceListResponse with real database records.
        """
        from sqlalchemy import select, func
        from app.models.official_source import OfficialSource

        count_result = await db.execute(select(func.count(OfficialSource.id)))
        total = count_result.scalar_one()

        sources = await SourceRepository.list(db, skip=skip, limit=limit)
        return SourceListResponse(
            total=total,
            items=[OfficialSourceResponse.model_validate(s) for s in sources],
        )
