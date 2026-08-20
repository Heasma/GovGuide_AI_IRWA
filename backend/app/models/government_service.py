"""
GovGuide AI — Government Office and Service ORM Models

GovernmentOffice represents a government ministry, department, or regulatory authority.
GovernmentService represents a license type or government service offering.

Phase 3 additions:
  GovernmentOffice — street address, contact, and geolocation columns added.
  GovernmentService — service-detail columns, source_confidence, and issued_licenses
                      relationship added. service_code is the primary mapping key
                      for CSV LICENSE CODE (no duplicate license_code column added).
"""

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, uuid_pk, now


class GovernmentOffice(Base):
    """Represents a government ministry or department / regulatory authority."""
    __tablename__ = "government_offices"

    id = uuid_pk()
    name = Column(String(500), nullable=False)
    department = Column(String(500), nullable=True)

    # ── Phase 3: address / contact / geolocation ──────────────────────────────
    street_address = Column(String(500), nullable=True)
    city           = Column(String(100), nullable=True)
    state          = Column(String(50),  nullable=True)
    zip_code       = Column(String(20),  nullable=True)
    phone          = Column(String(50),  nullable=True)
    email          = Column(String(200), nullable=True)
    business_hours = Column(String(300), nullable=True)
    latitude       = Column(Float,       nullable=True)
    longitude      = Column(Float,       nullable=True)

    # ── Existing JSONB catch-all + web presence ───────────────────────────────
    contact_info = Column(JSONB, default=dict)    # legacy / overflow
    website_url  = Column(Text,  nullable=True)
    raw_metadata = Column(JSONB, default=dict)

    created_at = now()
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    services = relationship("GovernmentService", back_populates="office", lazy="select")


class GovernmentService(Base):
    """Represents a government service or license type."""
    __tablename__ = "government_services"

    id = uuid_pk()
    # service_code is the primary mapping key: CSV LICENSE CODE → GovernmentService
    service_code = Column(String(100), unique=True, nullable=True)
    name         = Column(String(500), nullable=False)
    description  = Column(Text,        nullable=True)
    category     = Column(String(200), nullable=True, index=True)
    office_id = Column(
        UUID(as_uuid=True),
        ForeignKey("government_offices.id"),
        nullable=True,
    )
    is_active       = Column(Boolean, default=True, nullable=False)
    source_url      = Column(Text,    nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # ── Phase 3: service-detail columns (from government_services_template.csv) ─
    license_term_years     = Column(Integer,      nullable=True)
    fee_amount             = Column(String(500),  nullable=True)
    fee_description        = Column(Text,         nullable=True)
    application_portal_url = Column(Text,         nullable=True)
    eligibility_summary    = Column(Text,         nullable=True)
    required_documents     = Column(Text,         nullable=True)
    application_steps      = Column(Text,         nullable=True)
    inspection_required    = Column(Boolean,      nullable=True)
    renewal_required       = Column(Boolean,      nullable=True)
    renewal_period         = Column(String(100),  nullable=True)
    legal_reference        = Column(String(200),  nullable=True)
    # source_confidence: VERIFIED | PARTIALLY_VERIFIED | REQUIRES_MANUAL_VERIFICATION
    source_confidence      = Column(String(40),   nullable=True)

    raw_metadata = Column(JSONB, default=dict)
    created_at   = now()
    updated_at   = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    office = relationship("GovernmentOffice", back_populates="services")
    official_sources = relationship("OfficialSource", back_populates="service", lazy="select")
    # Phase 3: one-to-many → individual license records
    issued_licenses = relationship(
        "BusinessLicense",
        back_populates="service",
        lazy="select",
    )


__all__ = ["GovernmentOffice", "GovernmentService"]
