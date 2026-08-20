# GovGuide AI — Phase 3 Database Schema Extension & Ingestion Report

**Date**: 2026-08-20  
**Phase**: 3 — Database Schema Extension + Full Dataset Ingestion  
**Status**: COMPLETE  

---

## 1. Executive Summary

Phase 3 successfully extended the GovGuide AI PostgreSQL database schema and ingested the complete City of Chicago Active Business Licenses dataset (`53,091` records) with 100% data integrity, zero duplicate records, zero orphan records, and 100% foreign-key compliance.

All government service endpoints (`/api/v1/services`, `/api/v1/services/categories`, `/api/v1/services/search`, `/api/v1/services/{service_id}`) have been upgraded from `DatasetPendingResponse` placeholders to live, database-backed queries returning verified government license offerings.

---

## 2. Dataset Validation & Profiling Summary

### Source File Metrics
- **Source File**: `data/raw/Business_Licenses_-_Current_Active_20260819.csv`
- **Total Rows**: `53,091`
- **Total Columns**: `37` (all 37 validated and mapped)
- **Valid Rows**: `53,091` (100.0%)
- **Invalid Rows**: `0` (0.0%)
- **Unique LICENSE IDs**: `53,091` (100.0% unique natural key)
- **Duplicate LICENSE IDs**: `0` (0.0%)
- **Unique ACCOUNT NUMBERs**: `36,262`
- **Unique (ACCOUNT NUMBER, SITE NUMBER) Pairs**: `43,506`
- **Unique LICENSE NUMBERs**: `52,220` (871 license numbers shared across renewal/version records)
- **Unique Physical Business Addresses**: `40,127`
- **Unique LICENSE CODE Values**: `56` (100% mapped to official BACP services)

### Missing Values Distribution by Column

| Column Name | Missing Count | Missing Percentage | Ingestion Treatment |
|---|---|---|---|
| `ID` | 0 | 0.00% | Ingested as `raw_record_reference` |
| `LICENSE ID` | 0 | 0.00% | Ingested as `license_id` (Unique Natural Key) |
| `ACCOUNT NUMBER` | 0 | 0.00% | Ingested as `account_number` (Holder Key) |
| `SITE NUMBER` | 0 | 0.00% | Ingested as `site_number` (Holder Key) |
| `LEGAL NAME` | 0 | 0.00% | Ingested as `legal_name` |
| `DOING BUSINESS AS NAME` | 0 | 0.00% | Ingested as `doing_business_as_name` |
| `ADDRESS` | 0 | 0.00% | Ingested as `address` |
| `CITY` | 0 | 0.00% | Ingested as `city` |
| `STATE` | 0 | 0.00% | Ingested as `state` |
| `ZIP CODE` | 16 | 0.03% | Stored as nullable string |
| `WARD` | 4,084 | 7.69% | Stored as nullable integer |
| `PRECINCT` | 4,287 | 8.07% | Stored as nullable integer |
| `WARD PRECINCT` | 3,936 | 7.41% | Stored as nullable string |
| `POLICE DISTRICT` | 4,037 | 7.60% | Stored as nullable integer |
| `COMMUNITY AREA` | 4,171 | 7.86% | Stored as nullable integer (0–77 range) |
| `COMMUNITY AREA NAME` | 4,176 | 7.87% | Stored as nullable string |
| `NEIGHBORHOOD` | 4,205 | 7.92% | Stored as nullable string |
| `LICENSE CODE` | 0 | 0.00% | Ingested as `license_code` (Maps to GovernmentService) |
| `LICENSE DESCRIPTION` | 0 | 0.00% | Ingested as `license_description` |
| `BUSINESS ACTIVITY ID` | 3,082 | 5.81% | Stored as nullable string |
| `BUSINESS ACTIVITY` | 3,082 | 5.81% | Stored as nullable text |
| `LICENSE NUMBER` | 0 | 0.00% | Ingested as `license_number` |
| `APPLICATION TYPE` | 0 | 0.00% | Ingested as `application_type` |
| `APPLICATION CREATED DATE` | 41,890 | 78.90% | Stored as nullable date (absent on renewals) |
| `APPLICATION REQUIREMENTS COMPLETE` | 39 | 0.07% | Stored as nullable date |
| `PAYMENT DATE` | 138 | 0.26% | Stored as nullable date |
| `CONDITIONAL APPROVAL` | 0 | 0.00% | Converted to Boolean (Y/N) |
| `LICENSE TERM START DATE` | 3 | 0.01% | Stored as nullable date |
| `LICENSE TERM EXPIRATION DATE` | 0 | 0.00% | Stored as date |
| `LICENSE APPROVED FOR ISSUANCE` | 2,295 | 4.32% | Stored as nullable date |
| `DATE ISSUED` | 0 | 0.00% | Stored as date |
| `LICENSE STATUS` | 0 | 0.00% | Ingested as `license_status` (all "AAI") |
| `LICENSE STATUS CHANGE DATE` | 53,091 | 100.00% | Stored as nullable date (all null for active) |
| `SSA` | 39,068 | 73.59% | Stored as nullable string |
| `LATITUDE` | 4,238 | 7.98% | Stored as nullable float |
| `LONGITUDE` | 4,238 | 7.98% | Stored as nullable float |
| `LOCATION` | 4,238 | 7.98% | Redundant WKT point (coordinates captured directly) |

---

## 3. Database Schema & Architecture

### Entity-Relationship Architecture

```
[ GovernmentOffice ] (City of Chicago - BACP)
         │ 1
         │
         ▼ many
[ GovernmentService ] (56 License Offerings: LBL, Retail Food, etc.)
         │ 1
         │
         ▼ many
[ BusinessLicense ] (53,091 active license records)
         ▲
         │ many
         │
         │ 1
[ BusinessLicenseHolder ] (43,506 physical business locations)
```

### Uniqueness & Deduplication Strategy
1. **Business License Holder**:
   - Natural Key: `(account_number, site_number)`
   - Composite Unique Index: `ix_business_license_holders_account_site`
   - Outcome: Accounts operating multiple physical branches (e.g. 2,490 multi-site accounts) maintain separate location and ward records without loss of geospatial detail.
2. **Business License**:
   - Natural Key: `license_id` (Unique Constraint & Index)
   - Foreign Keys:
     - `holder_id` → `business_license_holders.id` (`NOT NULL`)
     - `government_service_id` → `government_services.id` (`NULLABLE`, 100% mapped)

---

## 4. Ingestion Pipeline Execution Metrics

| Metric | Result | Target | Compliance |
|---|---|---|---|
| **Total Streamed Rows** | `53,091` | `53,091` | 100% |
| **Valid Records** | `53,091` | `53,091` | 100% |
| **Holders Created** | `43,506` | `43,506` | 100% |
| **Holders Updated** | `0` | `0` | 100% |
| **Licenses Created** | `53,091` | `53,091` | 100% |
| **Licenses Skipped / Duplicates** | `0` | `0` | 100% |
| **Ingestion Execution Time** | `47.50 seconds` | `< 120s` | 100% |
| **Average Ingestion Throughput** | `1,117.7 rows/sec` | `> 500 rows/sec` | Exceeded |
| **Memory Efficiency** | Streaming batches of 1,000 rows | No full-CSV RAM load | Compliant |

---

## 5. Post-Ingestion Database Verification

### Table Row Counts in PostgreSQL (`govguide_db`)

| Table Name | PostgreSQL Count | Expected Count | Status |
|---|---|---|---|
| `government_offices` | `1` | `1` | MATCH |
| `government_services` | `56` | `56` | MATCH |
| `business_license_holders` | `43,506` | `43,506` | MATCH |
| `business_licenses` | `53,091` | `53,091` | MATCH |
| `users` | `4` | `4` | MATCH |
| `official_sources` | `0` | `0` | MATCH |
| `document_chunks` | `0` | `0` | MATCH |

### Foreign Key Integrity & Orphan Records Check

| Check Description | Query / Condition | Orphan Count | Status |
|---|---|---|---|
| **Orphan Licenses (Invalid Holder)** | `business_licenses.holder_id ∉ business_license_holders.id` | **0** | PASSED |
| **Orphan Licenses (Invalid Service)** | `business_licenses.government_service_id ∉ government_services.id` | **0** | PASSED |
| **Unmapped Service Licenses** | `business_licenses.government_service_id IS NULL` | **0** | PASSED |
| **Orphan Services (Invalid Office)** | `government_services.office_id ∉ government_offices.id` | **0** | PASSED |

### Top 5 Government Services by Active Licenses
1. **[1010] Apply for a Limited Business License (LBL)**: 16,065 active licenses
2. **[1006] Apply for a Retail Food Establishment License**: 11,141 active licenses
3. **[4404] Apply for a Regulated Business License (RBL)**: 7,476 active licenses
4. **[1475] Apply for a Consumption on Premises - Incidental Activity License**: 2,843 active licenses
5. **[1781] Apply for a Tobacco License**: 1,842 active licenses

---

## 6. Live API Verification & Transition from DatasetPendingResponse

All government service endpoints were updated and verified against live PostgreSQL data:

1. **`GET /api/v1/services`**:
   - Status: `200 OK`
   - Response: `ServiceListResponse(total=56, items=[...])`
   - Includes full BACP office relationships, fee details, renewal terms, and requirement summaries.
2. **`GET /api/v1/services/categories`**:
   - Status: `200 OK`
   - Response: `CategoryListResponse(total=9, categories=['childcare_education', 'entertainment_amusement', 'food_beverage', 'health_medical', 'liquor_alcohol', 'motor_vehicle', 'real_estate_property', 'retail_general', 'tobacco'])`
3. **`GET /api/v1/services/search?query=food`**:
   - Status: `200 OK`
   - Response: `ServiceSearchResponse(query='food', total=7, items=[...])`
   - Returns Retail Food, Mobile Food, Shared Kitchen, Wholesale Food, etc.
4. **`GET /api/v1/services/{service_id}`**:
   - Status: `200 OK`
   - Returns complete single service detail and office nested metadata.

---

## 7. Test Suite Results

```
====================== 182 passed, 11 warnings in 6.65s =======================
```

- **Unit Tests**: `167 passed`
- **Integration Tests**: `15 passed`
- **Total Passing Tests**: `182 / 182 (100%)`
- **Zero Failures, Zero Errors**

---

## 8. Artifacts Created & Updated in Phase 3

1. `backend/app/models/business_license.py` — ORM models for `BusinessLicenseHolder` and `BusinessLicense`
2. `backend/app/models/government_service.py` — Schema extension for `GovernmentOffice` and `GovernmentService`
3. `backend/migrations/versions/5bb023e04734_add_business_license_entities.py` — Non-destructive Alembic migration
4. `backend/app/ingestion/csv_reader.py` — Streaming CSV batch reader
5. `backend/app/ingestion/validators.py` — 37-column row and batch validators
6. `backend/app/ingestion/transformers.py` — Type parsing and coercion engine
7. `backend/app/ingestion/license_mapper.py` — License code to government service mapper
8. `backend/app/ingestion/loader.py` — Transactional batch database loader
9. `backend/scripts/run_full_ingestion.py` — Production dataset ingestion script
10. `data/raw/business_license_data_dictionary.md` — Comprehensive 37-column data dictionary
11. `data/processed/full_ingestion_report.json` — Complete ingestion run metadata
12. `tests/unit/test_csv_ingestion.py` — Unit tests for CSV ingestion components
13. `tests/integration/test_business_license_models.py` — Integration tests for business license ORM models
14. `docs/PHASE_3_DATABASE_INGESTION_REPORT.md` — Final Phase 3 documentation
