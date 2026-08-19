# GovGuide AI -- Dataset to Model Mapping Proposal

**Dataset**: Business_Licenses_-_Current_Active_20260819.csv  
**Generated**: 2026-08-19  
**Status**: PROPOSAL ONLY -- No database changes made. No SQLAlchemy models modified.

---

## Important Notes

> This mapping is a proposal only. It is based on actual CSV column inspection.
> No SQLAlchemy models, Alembic migrations, or PostgreSQL schema have been modified.
> All transformations listed are future-phase work.

---

## Existing Target Models

| Model | Table | Purpose |
|-------|-------|---------|
| `GovernmentOffice` | `government_offices` | Government department/ministry |
| `GovernmentService` | `government_services` | Government service offered |
| `OfficialSource` | `official_sources` | Official document or webpage |
| `DocumentChunk` | `document_chunks` | RAG text chunk |
| `User` | `users` | Application user |
| `QuerySession` | `query_sessions` | Conversation session |
| `ConversationMessage` | `conversation_messages` | Individual chat message |
| `AuditLog` | `audit_logs` | Security audit trail |
| `AgentInteractionLog` | `agent_interaction_logs` | Agent message log |

---

## Full Field-by-Field Mapping

| # | CSV Field | Possible Model | Possible Field | Transformation Required | New Field Needed | Confidence | Notes |
|---|-----------|----------------|----------------|------------------------|------------------|------------|-------|
| 1 | `ID` | GovernmentService | `service_code` (partial) | Extract numeric part or use as raw external ID | No | Medium | Composite key -- not a clean service code |
| 2 | `LICENSE ID` | GovernmentService | `service_code` | Cast to string, use as external ID | No | High | Best candidate for unique service identifier |
| 3 | `ACCOUNT NUMBER` | GovernmentOffice | `raw_metadata.account_number` | Store in JSONB; group licenses by account | No | Medium | Represents business entity, not government office |
| 4 | `SITE NUMBER` | GovernmentOffice | `raw_metadata.site_number` | Store in JSONB | No | Low | Multi-site index; rarely queried independently |
| 5 | `LEGAL NAME` | GovernmentOffice | `name` | Trim whitespace | No | High | Best field for office/entity name |
| 6 | `DOING BUSINESS AS NAME` | GovernmentOffice | `department` (or new field) | Trim whitespace | Yes (dba_name) | Medium | DBA name is distinct from legal name; may need dedicated column |
| 7 | `ADDRESS` | GovernmentOffice | `raw_metadata.address` | Trim, standardize | Yes (address) | High | No address field on GovernmentOffice -- needs new column or JSONB |
| 8 | `CITY` | GovernmentOffice | `raw_metadata.city` | Trim | No | High | Store in JSONB contact_info |
| 9 | `STATE` | GovernmentOffice | `raw_metadata.state` | Trim | No | High | Store in JSONB contact_info |
| 10 | `ZIP CODE` | GovernmentOffice | `raw_metadata.zip_code` | Trim, zero-pad if needed | No | High | Store in JSONB contact_info |
| 11 | `WARD` | GovernmentService | `raw_metadata.ward` | Cast to int | No | High | Store in JSONB |
| 12 | `PRECINCT` | GovernmentService | `raw_metadata.precinct` | Cast to int | No | Low | Store in JSONB |
| 13 | `WARD PRECINCT` | GovernmentService | `raw_metadata.ward_precinct` | Keep as string | No | Low | Redundant if WARD + PRECINCT stored |
| 14 | `POLICE DISTRICT` | GovernmentService | `raw_metadata.police_district` | Cast to int | No | Medium | Useful for location-based queries |
| 15 | `COMMUNITY AREA` | GovernmentService | `raw_metadata.community_area` | Cast to int | No | High | Chicago standard area code |
| 16 | `COMMUNITY AREA NAME` | GovernmentService | `raw_metadata.community_area_name` | Trim, title-case | No | High | Human-readable -- useful for search |
| 17 | `NEIGHBORHOOD` | GovernmentService | `raw_metadata.neighborhood` | Trim | No | High | Sub-neighborhood for local queries |
| 18 | `LICENSE CODE` | GovernmentService | `category` (or new field) | Cast to string; map to human label | Yes (license_code) | High | 56 unique codes -- suitable for categorical indexing |
| 19 | `LICENSE DESCRIPTION` | GovernmentService | `name` | Trim whitespace | No | High | This IS the service name -- direct mapping |
| 20 | `BUSINESS ACTIVITY ID` | GovernmentService | `raw_metadata.activity_ids` | Split on " | " into list | No | High | Pipe-delimited -- split required |
| 21 | `BUSINESS ACTIVITY` | GovernmentService | `description` (partial) + DocumentChunk.content | Trim, split on " | ", join for RAG text | No | High | Primary RAG text content candidate |
| 22 | `LICENSE NUMBER` | GovernmentService | `raw_metadata.license_number` | Keep as string | No | High | Official license number |
| 23 | `APPLICATION TYPE` | GovernmentService | `raw_metadata.application_type` | Trim; enum validation (ISSUE/RENEW/etc.) | No | High | 6 unique values -- categorical |
| 24 | `APPLICATION CREATED DATE` | GovernmentService | `raw_metadata.application_created_date` | Parse to datetime UTC | No | Medium | 78.9% missing -- unreliable |
| 25 | `APPLICATION REQUIREMENTS COMPLETE` | GovernmentService | `raw_metadata.requirements_complete_date` | Parse to datetime UTC | No | High | 0.07% missing |
| 26 | `PAYMENT DATE` | GovernmentService | `raw_metadata.payment_date` | Parse to datetime UTC | No | Medium | 0.26% missing |
| 27 | `CONDITIONAL APPROVAL` | GovernmentService | `raw_metadata.conditional_approval` | Map Y/N to boolean | No | High | 2 unique values |
| 28 | `LICENSE TERM START DATE` | GovernmentService | `raw_metadata.term_start_date` | Parse to datetime UTC | No | High | 0.01% missing |
| 29 | `LICENSE TERM EXPIRATION DATE` | GovernmentService | `last_verified_at` or `raw_metadata.term_expiry_date` | Parse to datetime UTC | No | High | Directly indicates license validity |
| 30 | `LICENSE APPROVED FOR ISSUANCE` | GovernmentService | `raw_metadata.approved_date` | Parse to datetime UTC | No | High | 4.32% missing |
| 31 | `DATE ISSUED` | GovernmentService | `raw_metadata.date_issued` | Parse to datetime UTC | No | High | 0% missing |
| 32 | `LICENSE STATUS` | GovernmentService | `is_active` (derived) | Map AAI -> True; others -> conditional | No | High | Currently ONLY "AAI" -- entire dataset is active |
| 33 | `LICENSE STATUS CHANGE DATE` | GovernmentService | `raw_metadata.status_change_date` | Parse to datetime -- BUT 100% missing | No | Low | 100% NULL -- completely empty column |
| 34 | `SSA` | GovernmentService | `raw_metadata.ssa` | Cast to int; note 73.6% missing | No | Medium | Special Service Area -- sparse |
| 35 | `LATITUDE` | GovernmentOffice | `raw_metadata.latitude` or new FLOAT column | Cast to float | Yes (lat/lon columns) | High | Enables geographic proximity search |
| 36 | `LONGITUDE` | GovernmentOffice | `raw_metadata.longitude` or new FLOAT column | Cast to float | Yes (lat/lon columns) | High | Pairs with LATITUDE |
| 37 | `LOCATION` | GovernmentOffice | `raw_metadata.location_wkt` | Store as string; parse to geometry later | No | Medium | Redundant if lat/lon stored separately |

---

## Mapping Categories Summary

| Target Model | Fields Mapped | Method |
|--------------|---------------|--------|
| `GovernmentOffice` | LEGAL NAME, DBA NAME, ADDRESS, CITY, STATE, ZIP, LAT, LON | Direct + JSONB |
| `GovernmentService` | LICENSE CODE, LICENSE DESCRIPTION, BUSINESS ACTIVITY, LICENSE NUMBER, APPLICATION TYPE, STATUS, DATES | Direct + JSONB |
| `OfficialSource` | No direct mapping -- URL not in dataset | Supplementary data required |
| `DocumentChunk` | BUSINESS ACTIVITY, LICENSE DESCRIPTION (as RAG text) | Derived via chunking pipeline |

---

## Fields Requiring New Database Columns

| Field | Proposed Column | Model | Reason |
|-------|----------------|-------|--------|
| `DOING BUSINESS AS NAME` | `dba_name VARCHAR(500)` | GovernmentOffice | No DBA field exists |
| `ADDRESS` | `street_address VARCHAR(500)` | GovernmentOffice | No address field exists |
| `LATITUDE` | `latitude FLOAT` | GovernmentOffice | JSONB is imprecise for geospatial |
| `LONGITUDE` | `longitude FLOAT` | GovernmentOffice | JSONB is imprecise for geospatial |
| `LICENSE CODE` | `license_code VARCHAR(20)` | GovernmentService | Category field is too generic |

> These columns are PROPOSALS only. Alembic migrations will be created in Phase 2.

---

## Critical Observation: Dataset Represents Businesses, Not Offices

The dataset describes **licensed businesses** operating under government licenses -- it does NOT represent government offices/departments. The mapping is therefore:

- Each unique `LICENSE DESCRIPTION` / `LICENSE CODE` combination -> **GovernmentService** record (license type)
- Each unique business (ACCOUNT NUMBER) -> **GovernmentOffice** record (business entity acting as quasi-office)

This is a semantic mismatch that must be addressed in the transformation design (Phase 2).

---

## Unmappable CSV Fields (No Current Model)

| CSV Field | Reason |
|-----------|--------|
| `WARD PRECINCT` | Redundant composite of WARD + PRECINCT |
| `LICENSE STATUS CHANGE DATE` | 100% NULL -- no data |
| `SITE NUMBER` | Internal counter, low query value |
