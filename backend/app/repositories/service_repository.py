"""
GovGuide AI — Service Repository

Handles database persistence and queries for GovernmentService and GovernmentOffice.
"""

import uuid
from typing import Optional, List, Tuple

from sqlalchemy import select, func, or_, distinct
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.government_service import GovernmentService, GovernmentOffice


class ServiceRepository:
    """Data access layer for GovernmentService and GovernmentOffice models."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        service_id: uuid.UUID,
    ) -> Optional[GovernmentService]:
        """Retrieve a government service by its UUID with office relationship loaded."""
        stmt = (
            select(GovernmentService)
            .options(selectinload(GovernmentService.office))
            .where(GovernmentService.id == service_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        is_active: bool = True,
    ) -> Tuple[List[GovernmentService], int]:
        """
        Return a paginated list of services and total count.
        Optionally filter by category and active status.
        """
        query = select(GovernmentService).where(
            GovernmentService.is_active == is_active
        )
        count_query = select(func.count(GovernmentService.id)).where(
            GovernmentService.is_active == is_active
        )

        if category:
            query = query.where(GovernmentService.category.ilike(f"%{category}%"))
            count_query = count_query.where(GovernmentService.category.ilike(f"%{category}%"))

        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        query = (
            query.options(selectinload(GovernmentService.office))
            .order_by(GovernmentService.name.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def search(
        db: AsyncSession,
        query_str: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[GovernmentService], int]:
        """
        Search services by name, description, category, or service_code.
        """
        base_filter = GovernmentService.is_active.is_(True)
        if query_str and query_str.strip():
            pattern = f"%{query_str.strip()}%"
            search_filter = or_(
                GovernmentService.name.ilike(pattern),
                GovernmentService.description.ilike(pattern),
                GovernmentService.category.ilike(pattern),
                GovernmentService.service_code.ilike(pattern),
                GovernmentService.eligibility_summary.ilike(pattern),
            )
            where_clause = [base_filter, search_filter]
        else:
            where_clause = [base_filter]

        count_query = select(func.count(GovernmentService.id)).where(*where_clause)
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        stmt = (
            select(GovernmentService)
            .options(selectinload(GovernmentService.office))
            .where(*where_clause)
            .order_by(GovernmentService.name.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all()), total

    @staticmethod
    async def list_categories(db: AsyncSession) -> List[str]:
        """Return a sorted list of distinct active categories."""
        stmt = (
            select(distinct(GovernmentService.category))
            .where(
                GovernmentService.is_active.is_(True),
                GovernmentService.category.isnot(None),
            )
            .order_by(GovernmentService.category.asc())
        )
        result = await db.execute(stmt)
        return [c for c in result.scalars().all() if c]
