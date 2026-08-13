"""
GovGuide AI — Source Repository

Handles database persistence for OfficialSource and DocumentChunk.

[DATASET PENDING] No current router endpoints query these tables directly.
This repository provides a stable interface for when the retrieval pipeline
is integrated with the real government dataset.
"""

import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.official_source import OfficialSource, DocumentChunk


class SourceRepository:
    """Data access layer for OfficialSource and DocumentChunk models."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        source_id: uuid.UUID,
    ) -> Optional[OfficialSource]:
        """Retrieve an official source document by its UUID."""
        result = await db.execute(
            select(OfficialSource).where(OfficialSource.id == source_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        service_id: Optional[uuid.UUID] = None,
    ) -> List[OfficialSource]:
        """
        Return a paginated list of official sources.
        Optionally filter by service_id.
        """
        query = select(OfficialSource)
        if service_id:
            query = query.where(OfficialSource.service_id == service_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_chunks_by_source(
        db: AsyncSession,
        source_id: uuid.UUID,
    ) -> List[DocumentChunk]:
        """
        Return all document chunks for a given source, ordered by chunk index.
        Required by the retrieval pipeline (Phase 2).
        """
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.source_id == source_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())
