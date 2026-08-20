# GovGuide AI — Phase 3 Implementation Plan

**Date**: 2026-08-20  
**Phase**: 3 — Database Schema Extension + Dataset Ingestion Preparation  
**Status**: APPROVED — Implementation In Progress  

---

## 1. Current Schema (Confirmed by Inspection)

### Existing Tables (from initial migration `f318d9725a43`)

| Table | Model | Status |
|---|---|---|
| `users` | `User` | Stable |
| `query_sessions` | `QuerySession` | Stable |
| `conversation_messages` | `ConversationMessage` | Stable |
| `audit_logs` | `AuditLog` | Stable |
| `agent_interaction_logs` | `AgentInteractionLog` | Stable |
| `government_offices` | `GovernmentOffice` | Extend — add address/contact columns |
| `government_services` | `GovernmentService` | Extend — add service-detail columns + relationship |
| `official_sources` | `OfficialSource` | No change |
| `document_chunks` | `DocumentChunk` | No change |

### Existing GovernmentOffice Columns
`id, name, department, contact_info (JSONB), website_url, raw_metadata (JSONB), created_at, updated_at`

### Existing GovernmentService Columns
`id, service_code (unique), name, description, category, office_id (FK), is_active, source_url, last_verified_at, raw_metadata (JSONB), created_at, updated_at`

**Note**: `service_code` is already present and will serve as the mapping key for `LICENSE CODE`. No duplicate `license_code` column will be added.

---

## 2. Account Number Uniqueness Analysis

### Dataset Investigation Results

| Metric | Value |
|---|---|
| Total rows | 53,091 |
| Unique ACCOUNT NUMBERs | 36,262 |
| Accounts with multiple SITE NUMBERs | 2,490 |
| Accounts with multiple ADDRESSes | 2,394 |
| Composite (account_number, site_number) duplicates | 9,585 |
| Unique (account_number, site_number) combos | 43,506 |
| Unique LICENSE IDs | 53,091 (all unique — confirmed) |

### Real-World Semantic Analysis

The data reveals a three-level hierarchy:

1. **Legal Entity** (`ACCOUNT NUMBER`) — A company registered with the City of Chicago. One entity may operate at multiple physical locations.
2. **Physical Location** (`ACCOUNT NUMBER` + `SITE NUMBER`) — A specific business site. One site may hold multiple licenses (different `LICENSE CODE` values).
3. **Individual License** (`LICENSE ID`) — A specific license issued to a site. Always unique.

**Example**: `REGAL CINEMAS, INC.` (ACCOUNT=353500) operates two sites (site 1: 2600 N Western, site 2: 1471 W Webster). Each site holds multiple licenses (Retail Food, Public Place of Amusement, etc.).

### Decision: No Unique Constraint on `account_number` Alone

**`UNIQUE(account_number)` is WRONG** because one account legitimately operates across multiple physical sites.

**`UNIQUE(account_number, site_number)` is ALSO WRONG** because 9,585 composite duplicates exist — one (account, site) pair holds multiple license types.

### Final Design Decision

`BusinessLicenseHolder` represents a **physical location of a business** identified by `(account_number, site_number)`. No uniqueness constraint is placed on `account_number` alone.

**Primary deduplication key**: `(account_number, site_number)` — implemented as a **unique composite index** (not a constraint, to allow graceful upsert behavior during ingestion).

**Rationale**: This correctly represents the real-world hierarchy. A business may have site 1 and site 2 as separate physical locations, each with its own address, ward, and geographic coordinates. Merging them would lose location data.

---

## 3. Required New Models

### BusinessLicenseHolder — `business_license_holders`

Natural deduplication key: `(account_number, site_number)` — unique composite index.

### BusinessLicense — `business_licenses`

Natural deduplication key: `license_id` — unique constraint.

---

## 4. CSV-to-Model Mapping

### BusinessLicenseHolder Fields

| CSV Column | Model Field | Type | Nullable |
|---|---|---|---|
| `ACCOUNT NUMBER` | `account_number` | VARCHAR(50) | NO |
| `SITE NUMBER` | `site_number` | VARCHAR(20) | NO |
| `LEGAL NAME` | `legal_name` | VARCHAR(500) | NO |
| `DOING BUSINESS AS NAME` | `doing_business_as_name` | VARCHAR(500) | YES |
| `ADDRESS` | `address` | VARCHAR(500) | YES |
| `CITY` | `city` | VARCHAR(100) | YES |
| `STATE` | `state` | VARCHAR(50) | YES |
| `ZIP CODE` | `zip_code` | VARCHAR(20) | YES |
| `WARD` | `ward` | INTEGER | YES (7.7% null) |
| `PRECINCT` | `precinct` | INTEGER | YES (8.1% null) |
| `WARD PRECINCT` | `ward_precinct` | VARCHAR(20) | YES (7.4% null) |
| `POLICE DISTRICT` | `police_district` | INTEGER | YES (7.6% null) |
| `COMMUNITY AREA` | `community_area` | INTEGER | YES (7.9% null) |
| `COMMUNITY AREA NAME` | `community_area_name` | VARCHAR(100) | YES (7.9% null) |
| `NEIGHBORHOOD` | `neighborhood` | VARCHAR(100) | YES (7.9% null) |
| `LATITUDE` | `latitude` | FLOAT | YES (8.0% null) |
| `LONGITUDE` | `longitude` | FLOAT | YES (8.0% null) |
| (overflow) | `raw_metadata` | JSONB | YES |

### BusinessLicense Fields

| CSV Column | Model Field | Type | Nullable |
|---|---|---|---|
| `LICENSE ID` | `license_id` | VARCHAR(50) | NO, unique |
| `LICENSE NUMBER` | `license_number` | VARCHAR(100) | NO |
| `LICENSE CODE` | `license_code` | VARCHAR(20) | NO |
| `LICENSE DESCRIPTION` | `license_description` | VARCHAR(300) | NO |
| `BUSINESS ACTIVITY ID` | `business_activity_id` | VARCHAR(200) | YES (5.8% null) |
| `BUSINESS ACTIVITY` | `business_activity` | TEXT | YES (5.8% null) |
| `APPLICATION TYPE` | `application_type` | VARCHAR(50) | NO |
| `APPLICATION CREATED DATE` | `application_created_date` | DATE | YES (78.9% null) |
| `APPLICATION REQUIREMENTS COMPLETE` | `application_requirements_complete` | DATE | YES (0.1% null) |
| `PAYMENT DATE` | `payment_date` | DATE | YES (0.3% null) |
| `CONDITIONAL APPROVAL` | `conditional_approval` | BOOLEAN | NO (Y/N) |
| `LICENSE TERM START DATE` | `license_term_start_date` | DATE | YES (0.0% null) |
| `LICENSE TERM EXPIRATION DATE` | `license_term_expiration_date` | DATE | NO |
| `LICENSE APPROVED FOR ISSUANCE` | `license_approved_for_issuance` | DATE | YES (4.3% null) |
| `DATE ISSUED` | `date_issued` | DATE | NO |
| `LICENSE STATUS` | `license_status` | VARCHAR(20) | NO (all=AAI) |
| `LICENSE STATUS CHANGE DATE` | `license_status_change_date` | DATE | YES (100% null) |
| `SSA` | `ssa` | VARCHAR(20) | YES (73.6% null) |
| `ID` | `raw_record_reference` | VARCHAR(100) | YES |
| — | `holder_id` | UUID FK | NO |
| — | `government_service_id` | UUID FK | YES |

---

## 5. GovernmentOffice Extensions

New columns (all nullable, no changes to existing):
`street_address, city, state, zip_code, phone, email, business_hours, latitude, longitude`

---

## 6. GovernmentService Extensions

New columns (all nullable, preserving existing `service_code`):
`license_term_years, fee_amount, fee_description, application_portal_url, eligibility_summary, required_documents, application_steps, inspection_required, renewal_required, renewal_period, legal_reference, source_confidence`

New relationship: `issued_licenses → BusinessLicense`

---

## 7. Relationships

```
GovernmentOffice (1) ──< GovernmentService (many)
GovernmentService (1) ──< OfficialSource (many)
GovernmentService (1) ──< BusinessLicense (many)
BusinessLicenseHolder (1) ──< BusinessLicense (many)
```

---

## 8. Migration Strategy

- Alembic autogenerate from updated model metadata
- New tables: `business_license_holders`, `business_licenses`
- Modified tables: `government_offices` (add columns), `government_services` (add columns + relationship)
- Zero drops, zero column removals
- Existing data preserved

---

## 9. Ingestion Architecture

```
CSV (53,091 rows)
    ↓
csv_reader.py — batch stream, column validation
    ↓
validators.py — required fields, dates, coords, license codes
    ↓
transformers.py — date, float, int, bool coercion
    ↓
license_mapper.py — LICENSE CODE → GovernmentService.id
    ↓
loader.py — upsert BusinessLicenseHolder, insert BusinessLicense
    ↓
data/processed/dry_run_report.json (first 100 rows, no commit)
```

Dry-run mode: validate + transform + map but never call `db.commit()`.

---

## 10. Validation Rules

| Field | Rule |
|---|---|
| LICENSE ID | Required, non-empty, must be unique |
| LICENSE NUMBER | Required, non-empty |
| LICENSE CODE | Required, must exist in known 56 codes |
| LICENSE DESCRIPTION | Required, non-empty |
| ACCOUNT NUMBER | Required, non-empty |
| SITE NUMBER | Required, non-empty |
| LEGAL NAME | Required, non-empty |
| Dates | MM/DD/YYYY or empty; empty is valid null |
| LATITUDE | Float in range -90 to 90 if present |
| LONGITUDE | Float in range -180 to 180 if present |
| WARD | Integer 1–50 if present |
| PRECINCT | Positive integer if present |
| POLICE DISTRICT | Integer 1–25 if present |
| CONDITIONAL APPROVAL | Must be Y or N |
| LICENSE STATUS | Must be AAI (current dataset) |

---

## 11. Testing Strategy

### Unit Tests (`tests/unit/test_csv_ingestion.py`)
- 37-column detection
- Date parsing (valid, empty, malformed)
- Float parsing (lat/long)
- Integer parsing (ward, precinct, police district)
- Boolean parsing (Y/N → True/False)
- License code mapping (known code, unknown code)
- Duplicate license_id detection
- Missing required field detection

### Integration Tests (`tests/integration/test_business_license_models.py`)
- SQLite in-memory for isolation
- `BusinessLicenseHolder` CRUD
- `BusinessLicense` CRUD with FK
- FK integrity enforcement
- Duplicate `license_id` → IntegrityError
- GovernmentService link

---

## 12. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Alembic drops existing columns | Inspect migration before running `upgrade head` |
| Duplicate holders if account+site collides | Composite unique index + upsert logic |
| Invalid dates in SOURCE columns | Graceful None conversion with validation report |
| `LOCATION` column (WKT point) unused | Stored in `raw_metadata` JSONB |
| `BUSINESS ACTIVITY` pipe-delimited | Stored as TEXT; not split in Phase 3 |
| GovernmentService not seeded yet | `government_service_id` nullable on BusinessLicense |
