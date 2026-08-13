"""
GovGuide AI — Government Office and Service ORM Models

[PRELIMINARY] These tables are structural placeholders.
Column names, types, and relationships WILL CHANGE when the real dataset
arrives. JSONB fields (raw_metadata) are intentionally flexible.
No government data is inserted here.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, uuid_pk, now


class GovernmentOffice(Base):
    """[PRELIMINARY] Represents a government ministry or department."""
    __tablename__ = "government_offices"

    id = uuid_pk()
    name = Column(String(500), nullable=False)
    department = Column(String(500), nullable=True)
    contact_info = Column(JSONB, default=dict)    # phone, email, address — structure TBD
    website_url = Column(Text, nullable=True)
    raw_metadata = Column(JSONB, default=dict)    # any extra fields from dataset
    created_at = now()
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    services = relationship("GovernmentService", back_populates="office", lazy="select")


class GovernmentService(Base):
    """[PRELIMINARY] Represents a government service. Structure depends on real dataset."""
    __tablename__ = "government_services"

    id = uuid_pk()
    service_code = Column(String(100), unique=True, nullable=True)  # external ID if available
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(200), nullable=True, index=True)
    office_id = Column(
        UUID(as_uuid=True),
        ForeignKey("government_offices.id"),
        nullable=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    source_url = Column(Text, nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    raw_metadata = Column(JSONB, default=dict)    # flexible — absorbs unknown dataset columns
    created_at = now()
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    office = relationship("GovernmentOffice", back_populates="services")
    official_sources = relationship("OfficialSource", back_populates="service", lazy="select")


__all__ = ["GovernmentOffice", "GovernmentService"]
