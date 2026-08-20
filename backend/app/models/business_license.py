"""
GovGuide AI — Business License ORM Models

Two new models representing licensed businesses and their individual licenses.

Design decisions (documented in docs/PHASE_3_IMPLEMENTATION_PLAN.md):

BusinessLicenseHolder
─────────────────────
Represents a physical business location registered with the City of Chicago.

Natural key analysis of the CSV revealed:
  • 36,262 unique ACCOUNT NUMBERs, but 2,490 have multiple SITE NUMBERs.
  • One business entity (ACCOUNT NUMBER) can legitimately operate at multiple
    physical locations (SITE NUMBERs), each with a different address.
  • (account_number, site_number) has 9,585 composite duplicates because one
    physical site can hold multiple license types.
  • LICENSE ID is the only fully unique identifier across all 53,091 rows.

Conclusion:
  • UNIQUE(account_number) → WRONG (2,490 accounts have multiple sites).
  • UNIQUE(account_number, site_number) → used as a composite unique INDEX
    (not a hard constraint) to allow graceful upsert semantics during ingestion.
    The loader deduplicates by (account_number, site_number) and picks the most
    complete record when multiple licenses share the same site.

BusinessLicense
───────────────
Represents one individual license record (one CSV row).
LICENSE ID is globally unique across all 53,091 rows → used as the
natural deduplication key with a unique constraint.

Foreign keys:
  holder_id           → business_license_holders.id  (NOT NULL)
  government_service_id → government_services.id     (nullable — seeded later)
"""

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float,
    ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, uuid_pk, now


class BusinessLicenseHolder(Base):
    """
    A physical business location registered with the City of Chicago.

    Deduplication: (account_number, site_number) unique composite index.
    One holder record covers a single physical site. Multiple licenses
    (different LICENSE CODEs) at the same site all reference this holder.
    """
    __tablename__ = "business_license_holders"

    id = uuid_pk()

    # ── Natural identifiers ───────────────────────────────────────────────────
    account_number = Column(String(50),  nullable=False, index=True)
    site_number    = Column(String(20),  nullable=False)

    # ── Business identity ─────────────────────────────────────────────────────
    legal_name             = Column(String(500), nullable=False)
    doing_business_as_name = Column(String(500), nullable=True)

    # ── Physical location ─────────────────────────────────────────────────────
    address              = Column(String(500), nullable=True)
    city                 = Column(String(100), nullable=True)
    state                = Column(String(50),  nullable=True)
    zip_code             = Column(String(20),  nullable=True)

    # ── Chicago administrative geography ─────────────────────────────────────
    ward               = Column(Integer,      nullable=True)   # 7.7% null in source
    precinct           = Column(Integer,      nullable=True)   # 8.1% null
    ward_precinct      = Column(String(20),   nullable=True)   # 7.4% null
    police_district    = Column(Integer,      nullable=True)   # 7.6% null
    community_area     = Column(Integer,      nullable=True)   # 7.9% null
    community_area_name = Column(String(100), nullable=True)   # 7.9% null
    neighborhood       = Column(String(100),  nullable=True)   # 7.9% null

    # ── Geolocation ──────────────────────────────────────────────────────────
    latitude  = Column(Float, nullable=True)   # 8.0% null
    longitude = Column(Float, nullable=True)   # 8.0% null

    # ── Overflow ──────────────────────────────────────────────────────────────
    raw_metadata = Column(JSONB, default=dict)

    # ── Audit timestamps ─────────────────────────────────────────────────────
    created_at = now()
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    licenses = relationship(
        "BusinessLicense",
        back_populates="holder",
        lazy="select",
    )

    # ── Table-level constraints ────────────────────────────────────────────────
    __table_args__ = (
        Index(
            "ix_business_license_holders_account_site",
            "account_number",
            "site_number",
            unique=True,
        ),
    )


class BusinessLicense(Base):
    """
    An individual business license record — one per CSV row.

    LICENSE ID is the globally unique natural key for this dataset
    (confirmed: 53,091 rows, 53,091 distinct LICENSE IDs).

    government_service_id is nullable because GovernmentService records are
    seeded separately from the government_services_template.csv. Licenses for
    unmapped service codes remain in the database with government_service_id=NULL
    and are flagged in the ingestion validation report.
    """
    __tablename__ = "business_licenses"

    id = uuid_pk()

    # ── Natural identifiers ───────────────────────────────────────────────────
    license_id     = Column(String(50),  nullable=False, unique=True, index=True)
    license_number = Column(String(100), nullable=False, index=True)

    # ── License type ──────────────────────────────────────────────────────────
    license_code        = Column(String(20),  nullable=False, index=True)
    license_description = Column(String(300), nullable=False)

    # ── Business activity (may be pipe-delimited for multi-activity licenses) ─
    business_activity_id = Column(String(200), nullable=True)
    business_activity    = Column(Text,        nullable=True)

    # ── Application metadata ─────────────────────────────────────────────────
    application_type = Column(String(50), nullable=True)
    # APPLICATION CREATED DATE: 78.9% null in source — always nullable
    application_created_date           = Column(Date, nullable=True)
    application_requirements_complete  = Column(Date, nullable=True)
    payment_date                       = Column(Date, nullable=True)
    conditional_approval               = Column(Boolean, nullable=False, default=False)

    # ── License term ─────────────────────────────────────────────────────────
    license_term_start_date      = Column(Date, nullable=True)
    license_term_expiration_date = Column(Date, nullable=True)
    license_approved_for_issuance = Column(Date, nullable=True)
    date_issued                   = Column(Date, nullable=True)

    # ── Status ────────────────────────────────────────────────────────────────
    license_status             = Column(String(20), nullable=False, default="AAI")
    # LICENSE STATUS CHANGE DATE: 100% null in current dataset
    license_status_change_date = Column(Date, nullable=True)

    # ── Special Service Area ─────────────────────────────────────────────────
    ssa = Column(String(20), nullable=True)   # 73.6% null

    # ── Source tracking ───────────────────────────────────────────────────────
    # CSV composite row ID: e.g. "2948166-20280716"
    raw_record_reference = Column(String(100), nullable=True)

    # ── Foreign keys ─────────────────────────────────────────────────────────
    holder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business_license_holders.id"),
        nullable=False,
        index=True,
    )
    government_service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("government_services.id"),
        nullable=True,
        index=True,
    )

    # ── Audit timestamps ─────────────────────────────────────────────────────
    created_at = now()
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    holder = relationship(
        "BusinessLicenseHolder",
        back_populates="licenses",
    )
    service = relationship(
        "GovernmentService",
        back_populates="issued_licenses",
    )


__all__ = ["BusinessLicenseHolder", "BusinessLicense"]
