"""
GovGuide AI — Official Source and Document Chunk ORM Models

[PRELIMINARY] These tables are structural placeholders.
The embedding column for DocumentChunk is NOT defined here —
it will be added in a future Alembic migration once the embedding
model and its output dimension are confirmed.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, uuid_pk, now


class OfficialSource(Base):
    """[PRELIMINARY] Official source document or webpage for a service."""
    __tablename__ = "official_sources"

    id = uuid_pk()
    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("government_services.id"),
        nullable=True,
    )
    title = Column(String(500), nullable=True)
    url = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=True)  # webpage, pdf, gazette, etc.
    verified_at = Column(DateTime(timezone=True), nullable=True)
    checksum = Column(String(64), nullable=True)     # SHA-256 for change detection
    raw_content = Column(Text, nullable=True)
    raw_metadata = Column(JSONB, default=dict)
    created_at = now()

    service = relationship("GovernmentService", back_populates="official_sources")
    chunks = relationship("DocumentChunk", back_populates="source", lazy="select")


class DocumentChunk(Base):
    """
    [PRELIMINARY] Text chunk from an official source, used for RAG retrieval.

    IMPORTANT: The embedding column is NOT defined here.
    It will be added in a future Alembic migration:
        ALTER TABLE document_chunks ADD COLUMN embedding VECTOR(<N>);
    once the embedding model and its output dimension are confirmed.
    pgvector extension must be enabled before running that migration.
    """
    __tablename__ = "document_chunks"

    id = uuid_pk()
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("official_sources.id"),
        nullable=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # embedding: VECTOR(<dim>) — added in future migration
    token_count = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)
    created_at = now()

    source = relationship("OfficialSource", back_populates="chunks")


__all__ = ["OfficialSource", "DocumentChunk"]
