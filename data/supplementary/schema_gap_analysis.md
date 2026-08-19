# GovGuide AI — Schema Gap Analysis

**Date**: 2026-08-19  
**Phase**: 2 — Supplementary Data Design  
**Status**: ANALYSIS ONLY — No model or database changes made

---

## Overview

This document compares the required data model for GovGuide AI (to answer citizen
license/service queries) against the current SQLAlchemy model definitions, and identifies
the structural gaps that must be addressed in Phase 3.

---

## Current SQLAlchemy Models (from backend/app/models/)

### GovernmentOffice
```
id, name, department, contact_info (JSONB), raw_metadata (JSONB),
created_at, updated_at
+ Relationship to GovernmentService (one-to-many)
```

### GovernmentService
```
id, name, description, category, service_code, is_active,
government_office_id (FK), last_verified_at, raw_metadata (JSONB),
created_at, updated_at
+ Relationship to GovernmentOffice, OfficialSource, DocumentChunk
```

### OfficialSource
```
id, government_service_id (FK), url, title, content, source_type,
fetched_at, raw_metadata (JSONB), created_at, updated_at
```

### DocumentChunk
```
id, government_service_id (FK), official_source_id (FK),
content, chunk_index, embedding (vector), metadata (JSONB),
created_at, updated_at
```

---

## Critical Semantic Gap: Business vs. Government Office

### Current Assumption (Wrong)
The existing `GovernmentOffice` model assumes the entity is a **government department** 
(e.g., "Chicago BACP").

### Reality (From Dataset)
The Business Licenses CSV describes **licensed businesses** (e.g., "Joe's Restaurant LLC").
These are NOT government offices.

### Correct Semantic Mapping

| Concept | Correct Model | Current Status |
|---------|--------------|----------------|
| License type (e.g., "Retail Food Establishment") | `GovernmentService` | ✅ Fits |
| Government authority (BACP) | `GovernmentOffice` | ✅ Fits — but needs address/contact columns |
| Licensed business holder (e.g., "Joe's Restaurant") | **No model exists** | ❌ MISSING |
| Business location/address | **No model** or GovernmentOffice.raw_metadata | ⚠️ Partial |
| License record (specific license issued to a business) | **No model exists** | ❌ MISSING |

---

## Field-Level Gaps: GovernmentOffice

| Required Field | Current Status | Proposed Change |
|----------------|----------------|-----------------|
| `name` | Exists (VARCHAR) | Maps to BACP department name |
| `department` | Exists (VARCHAR) | Maps to division/unit |
| `street_address` | Missing | Add `street_address VARCHAR(500)` |
| `city` | Missing | Add `city VARCHAR(100)` (default: Chicago) |
| `state` | Missing | Add `state VARCHAR(50)` (default: IL) |
| `zip_code` | Missing | Add `zip_code VARCHAR(20)` |
| `phone` | Missing from columns; in contact_info JSONB | Add `phone VARCHAR(50)` or use JSONB |
| `email` | Missing from columns; in contact_info JSONB | Add `email VARCHAR(200)` or use JSONB |
| `business_hours` | Missing | Add `business_hours VARCHAR(300)` |
| `latitude` | Missing | Add `latitude FLOAT` |
| `longitude` | Missing | Add `longitude FLOAT` |
| `website_url` | Missing | Add `website_url TEXT` |

---

## Field-Level Gaps: GovernmentService

| Required Field | Current Status | Proposed Change |
|----------------|----------------|-----------------|
| `name` | Exists | Maps to `LICENSE DESCRIPTION` |
| `description` | Exists | Maps to citizen-facing service description |
| `category` | Exists (VARCHAR) | Maps to standardized service category |
| `service_code` | Exists | Maps to `LICENSE CODE` |
| `is_active` | Exists | Maps from `LICENSE STATUS` (AAI = True) |
| `license_term_years` | Missing | Add `license_term_years INTEGER` |
| `fee_amount` | Missing | Add `fee_amount VARCHAR(500)` |
| `fee_description` | Missing | Add `fee_description TEXT` |
| `application_portal_url` | Missing | Add `application_portal_url TEXT` |
| `eligibility_summary` | Missing | Add `eligibility_summary TEXT` |
| `required_documents` | Missing | Add `required_documents TEXT` |
| `application_steps` | Missing | Add `application_steps TEXT` |
| `inspection_required` | Missing | Add `inspection_required BOOLEAN` |
| `renewal_required` | Missing | Add `renewal_required BOOLEAN` |
| `renewal_period` | Missing | Add `renewal_period VARCHAR(100)` |
| `legal_reference` | Missing | Add `legal_reference VARCHAR(200)` |

---

## Missing Model: BusinessLicenseHolder

The dataset contains 36,262 unique business accounts. None of the existing models
can cleanly represent a **business entity that holds one or more licenses**.

### Proposed New Model

```python
class BusinessLicenseHolder(Base):
    __tablename__ = "business_license_holders"
    
    id = Column(UUID, primary_key=True)
    account_number = Column(String(50), unique=True)      # ACCOUNT NUMBER
    legal_name = Column(String(500))                       # LEGAL NAME
    dba_name = Column(String(500), nullable=True)          # DOING BUSINESS AS NAME
    street_address = Column(String(500), nullable=True)    # ADDRESS
    city = Column(String(100), nullable=True)              # CITY
    state = Column(String(50), nullable=True)              # STATE
    zip_code = Column(String(20), nullable=True)           # ZIP CODE
    latitude = Column(Float, nullable=True)                # LATITUDE
    longitude = Column(Float, nullable=True)               # LONGITUDE
    ward = Column(Integer, nullable=True)                  # WARD
    community_area = Column(Integer, nullable=True)        # COMMUNITY AREA
    community_area_name = Column(String(100), nullable=True)  # COMMUNITY AREA NAME
    neighborhood = Column(String(100), nullable=True)     # NEIGHBORHOOD
    police_district = Column(Integer, nullable=True)      # POLICE DISTRICT
    raw_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    licenses = relationship("BusinessLicense", back_populates="holder")
```

---

## Missing Model: BusinessLicense

Individual license records (one per row in the CSV) need their own model.

### Proposed New Model

```python
class BusinessLicense(Base):
    __tablename__ = "business_licenses"
    
    id = Column(UUID, primary_key=True)
    license_id = Column(String(50), unique=True)           # LICENSE ID
    license_number = Column(String(100))                   # LICENSE NUMBER
    license_code = Column(String(20))                      # LICENSE CODE
    license_description = Column(String(200))             # LICENSE DESCRIPTION
    application_type = Column(String(50))                  # APPLICATION TYPE
    license_status = Column(String(50), default="AAI")     # LICENSE STATUS
    term_start_date = Column(Date, nullable=True)          # LICENSE TERM START DATE
    term_expiry_date = Column(Date, nullable=True)         # LICENSE TERM EXPIRATION DATE
    date_issued = Column(Date, nullable=True)              # DATE ISSUED
    conditional_approval = Column(Boolean, default=False) # CONDITIONAL APPROVAL
    raw_metadata = Column(JSONB, default=dict)             # remaining fields
    
    # Foreign keys
    holder_id = Column(UUID, ForeignKey("business_license_holders.id"))
    government_service_id = Column(UUID, ForeignKey("government_services.id"))
    
    # Relationships
    holder = relationship("BusinessLicenseHolder", back_populates="licenses")
    service = relationship("GovernmentService", back_populates="issued_licenses")
```

---

## OfficialSource Model Assessment

| Required | Current Status | Gap |
|----------|---------------|-----|
| `url` | Exists | ✅ Ready |
| `title` | Exists | ✅ Ready |
| `source_type` | Exists | ✅ Ready |
| `fetched_at` | Exists | ✅ Ready |
| `source_verified_date` | Missing | Add to `raw_metadata` JSONB (Phase 3) |
| `source_confidence` | Missing | Add to `raw_metadata` JSONB (Phase 3) |
| `legal_reference` | Missing | Add to `raw_metadata` JSONB (Phase 3) |

---

## DocumentChunk Model Assessment

| Required | Current Status | Gap |
|----------|---------------|-----|
| `content` | Exists | ✅ Ready |
| `chunk_index` | Exists | ✅ Ready |
| `embedding` | Exists (vector) | ✅ Ready |
| `metadata` | Exists (JSONB) | ✅ Ready |
| Link to GovernmentService | Exists (FK) | ✅ Ready |
| Link to OfficialSource | Exists (FK) | ✅ Ready |

DocumentChunk is the most complete model for Phase 3 ingestion.

---

## Summary of Required Database Changes (Phase 3)

| Priority | Change | Model | Type |
|----------|--------|-------|------|
| 1 (Critical) | Create `BusinessLicenseHolder` model | NEW | New table |
| 2 (Critical) | Create `BusinessLicense` model | NEW | New table |
| 3 (High) | Add address/contact columns to `GovernmentOffice` | MODIFY | Alembic migration |
| 4 (High) | Add service-detail columns to `GovernmentService` | MODIFY | Alembic migration |
| 5 (Medium) | Add `source_verified_date`, `source_confidence` to `OfficialSource` raw_metadata | MODIFY | JSONB (no migration) |
| 6 (Low) | Add `license_term_years`, `renewal_required` to `GovernmentService` | MODIFY | Alembic migration |

> **Important**: These changes must NOT be implemented until Phase 3 is approved.
> This document is ANALYSIS ONLY.
