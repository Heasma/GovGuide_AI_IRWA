"""
GovGuide AI — Service Repository

Handles database persistence for GovernmentService and GovernmentOffice.

[DATASET PENDING] The /services router currently returns DatasetPendingResponse
for all endpoints — no actual queries against these tables are executed yet.
This repository provides a stable interface for when the dataset is integrated.

Methods defined here are the minimal interface expected for Phase 2.
No methods are invented beyond what the application structure will require.
"""

import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.government_service import GovernmentService, GovernmentOffice


class ServiceRepository:
    """Data access layer for GovernmentService and GovernmentOffice models."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        service_id: uuid.UUID,
    ) -> Optional[GovernmentService]:
        """Retrieve a government service by its UUID."""
        result = await db.execute(
            select(GovernmentService).where(GovernmentService.id == service_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        is_active: bool = True,
    ) -> List[GovernmentService]:
        """
        Return a paginated list of services.
        Optionally filter by category and active status.
        """
        query = select(GovernmentService).where(
            GovernmentService.is_active == is_active
        )
        if category:
            query = query.where(GovernmentService.category == category)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
