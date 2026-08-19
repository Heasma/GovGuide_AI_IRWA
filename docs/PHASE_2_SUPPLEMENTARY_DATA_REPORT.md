# GovGuide AI — Phase 2: Supplementary Official Government Data Report

**Date**: 2026-08-19  
**Phase**: 2 — Supplementary Official Government Data Collection  
**Status**: COMPLETE — Awaiting approval for Phase 3  
**Dataset**: Business_Licenses_-_Current_Active_20260819.csv  

---

## 1. License Types Identified

**56 unique license types** identified from the Business Licenses CSV dataset.

| Category | License Count | Example License Types |
|----------|-------------|----------------------|
| Food & Beverage | 7 | Retail Food Establishment, Wholesale Food, Mobile Food, Shared Kitchen |
| Liquor/Alcohol | 6 | Tavern, Package Goods, Consumption on Premises, Outdoor Patio, Late Hour |
| Retail General | 5 | Limited Business License, Regulated Business License, Peddler, Secondhand Dealer |
| Motor Vehicle | 5 | Motor Vehicle Services, Filling Station, Towing, Private Booting, Commercial Garage |
| Entertainment | 3 | Public Place of Amusement, Music and Dance, Public Place of Amusement (PAV) |
| Transportation | 4 | Valet Parking, Taxicab, Bicycle Messenger, Commercial Passenger Vessel |
| Healthcare/Pharma | 2 | Pharmaceutical Representative, Childcare (Children's Services Facility) |
| Tobacco | 1 | Tobacco |
| Real Estate | 2 | Shared Housing Unit Operator, Short Term Residential Rental Intermediary |
| Other (specialized) | 21 | Raffles, Pawnbroker, Explosives, Navy Pier Kiosk, Wrigley Field, etc. |

---

## 2. License Types with Verified Official Sources

| Confidence Level | Count | License Types |
|-----------------|-------|--------------|
| **VERIFIED** | **10** | Retail Food, Limited Business, Children's Services, Tavern, Package Goods, Regulated Business, Mobile Food, Peddler, Shared Housing Unit Operator, Pharmaceutical Representative |
| **PARTIALLY_VERIFIED** | **6** | Filling Station, Tobacco, Consumption on Premises, Motor Vehicle Services, Public Place of Amusement, Private Booting |
| **REQUIRES_MANUAL_VERIFICATION** | **40** | 40 license types — see `data_collection_checklist.md` for priority order |
| **NOT_FOUND** | **0** | None |

**Total with any official source data: 16/56 (28.6%)**  
**Fully verified: 10/56 (17.9%)**

---

## 3. Partially Verified License Types

The following 6 license types have some official information but require manual follow-up:

| License Code | License Type | What Was Verified | What Is Still Missing |
|-------------|-------------|-------------------|----------------------|
| 1050 | Public Place of Amusement | Application process, inspections, aldermanic notice requirement | Fee amount |
| 1275 | Filling Station | Fee structure ($220 + per-gallon) | Required documents, renewal procedure |
| 1470 Tavern | Tavern | Fee ($4,400+$40), inspections, background check | Aldermanic moratorium zones, specific documents |
| 1475 | Consumption on Premises | Application process, inspections | Fee amount |
| 1781 | Tobacco | Pre-measurement fee ($250), distance restrictions, 21+ requirement | Full license fee amount |
| 8340 | Motor Vehicle Services | Fee ($1,000 RBL effective 2026-01-01), inspection agencies | Environmental compliance details |
| 8604 | Private Booting | Fee ($1,000 + $100/location) | Specific requirements |

---

## 4. License Types Requiring Manual Verification

**40 license types** were not individually researched and are marked `REQUIRES_MANUAL_VERIFICATION`.

All 40 license types have:
- ✅ Official BACP department contact (312-74-GOBIZ, businesslicense@cityofchicago.org)
- ✅ Chicago Business Direct application portal URL (https://www.chicago.gov/BusinessDirect)
- ✅ Source type and verification date recorded

**Top 10 by record count requiring manual verification:**

| License Code | License Type | Record Count | Priority |
|-------------|-------------|-------------|---------|
| 1470 | Tavern | 756 | HIGH |
| 1474 | Package Goods | 1,064 | — (VERIFIED) |
| 4409 | Pop-Up Retail User | 126 | MEDIUM |
| 7029 | Towing - Storage Lot | 29 | LOW |
| 7030 | Towing - Tow Truck | 82 | LOW |
| 7020 | Commercial Passenger Vessel | 33 | LOW |
| 1471 | Late Hour | 118 | MEDIUM |
| 1472 | Music and Dance | 47 | LOW |
| 1473 | Not-For-Profit Club | 55 | LOW |
| 1477 | Outdoor Patio | 734 | MEDIUM |

See [`data/supplementary/data_collection_checklist.md`](file:///D:/User/IRWA_project/data/supplementary/data_collection_checklist.md) for the full per-license checklist.

---

## 5. Government Departments Identified

All 56 license types are administered by a single primary department:

> **City of Chicago Department of Business Affairs and Consumer Protection (BACP)**  
> City Hall, 121 N. LaSalle Street, Room 800, Chicago, IL 60602  
> Phone: 312-74-GOBIZ (312-744-6249)  
> Email: businesslicense@cityofchicago.org  
> Hours: Monday-Friday 8:00 AM - 5:00 PM  
> Web: https://www.chicago.gov/city/en/depts/bacp.html  

**Important findings on department diversity:**

For some license types, ADDITIONAL departments are involved:

| External Department | Involved For |
|--------------------|-------------|
| Chicago Department of Public Health (CDPH) | Food, childcare, and health-related licenses |
| Chicago Fire Department | Most Regulated Business licenses |
| Department of Buildings | Complex structures (childcare, amusement venues) |
| IL Dept of Children and Family Services (DCFS) | Children's Services Facility |
| City of Chicago Department of Planning and Development | Parking/zoning determinations |

---

## 6. Missing Information Categories

| Information Category | Overall Completion | Gap Description |
|---------------------|-------------------|-----------------|
| Service name (citizen-facing) | 16/56 (28%) | 40 license types still need plain-language service names |
| Eligibility criteria | 6/56 (10%) | Most require BACP website manual review |
| Required documents | 7/56 (12%) | Critical for "what to bring" queries |
| Application procedure | 5/56 (9%) | Most critical gap for GovGuide AI |
| Application URL | 56/56 (100%) | All use Chicago Business Direct |
| Fees | 14/56 (25%) | Mix of flat and tiered; many unknown |
| Processing time | 0/56 (0%) | No data in CSV; not obtainable without BACP website access |
| Renewal steps | 1/56 (2%) | Known only for Pharmaceutical Representative |
| Department contact | 56/56 (100%) | All BACP — contact data populated for all |
| Official source URL | 56/56 (100%) | All have BACP or portal URL |
| Legal reference | 5/56 (9%) | MCC chapter only known for LBL, RBL, Retail Food, Tavern, Children's Services |

---

## 7. Source Quality Summary

### Primary Source Used
**Chicago Business Direct** (https://www.chicago.gov/BusinessDirect) — Official BACP online application portal. Domain: `chicago.gov` ✅

### Source Hierarchy Applied
1. Chicago Business Direct portal (highest confidence)
2. chicago.gov BACP department pages  
3. Chicago Municipal Code (chicityclerk.com)

### Sources NOT Used
- Wikipedia ❌
- Commercial license service websites ❌
- Legal blogs ❌
- Unofficial guides ❌
- Reddit or social media ❌

### Official Domain Validation
All source URLs validated against approved government domain list:
`chicago.gov | cityofchicago.org | chicityclerk.com | chicagocitytreasurer.com | illinois.gov | municode.com | amlegal.com`

---

## 8. Schema Gaps

Full analysis at [`data/supplementary/schema_gap_analysis.md`](file:///D:/User/IRWA_project/data/supplementary/schema_gap_analysis.md).

### Critical Semantic Gap Confirmed
The dataset describes **licensed businesses**, NOT government offices.  
Current `GovernmentOffice` model is semantically misaligned.

### Missing Models
1. **`BusinessLicenseHolder`** — Business entity that holds a license (36,262 unique accounts)
2. **`BusinessLicense`** — Individual license record (53,091 rows in CSV)

### Columns Missing from Existing Models

**GovernmentOffice** needs: `street_address`, `latitude`, `longitude`, `phone`, `email`, `business_hours`, `website_url`

**GovernmentService** needs: `license_term_years`, `fee_amount`, `fee_description`, `application_portal_url`, `eligibility_summary`, `required_documents`, `application_steps`, `inspection_required`, `renewal_required`, `renewal_period`, `legal_reference`

---

## 9. Recommended Database Changes for Phase 3

| Priority | Change | Impact |
|----------|--------|--------|
| 1 CRITICAL | Create `BusinessLicenseHolder` model + Alembic migration | Enables 36,262 business entity records |
| 2 CRITICAL | Create `BusinessLicense` model + Alembic migration | Enables 53,091 license records from CSV |
| 3 HIGH | Add address/location columns to `GovernmentOffice` | Enables geographic queries |
| 4 HIGH | Add service-detail columns to `GovernmentService` | Enables eligibility/procedure/fee queries |
| 5 MEDIUM | Add `source_confidence`, `legal_reference` to `OfficialSource.raw_metadata` | No schema migration needed — JSONB |
| 6 LOW | Add `license_term_years`, `renewal_required` to `GovernmentService` | Enables renewal queries |

> **All changes require Alembic migrations. None should be implemented before Phase 3 approval.**

---

## 10. Recommended Ingestion Strategy

### Phase 3a: Model Changes
1. Create `BusinessLicenseHolder` and `BusinessLicense` SQLAlchemy models
2. Write Alembic migration scripts
3. Add supplementary columns to `GovernmentService` and `GovernmentOffice`

### Phase 3b: Government Office Setup
1. Insert BACP as a single `GovernmentOffice` record
2. Insert sub-offices (CDPH, Fire Dept, Buildings) as related `GovernmentOffice` records

### Phase 3c: Government Service Setup (56 records)
1. Insert one `GovernmentService` record per unique license type (LICENSE CODE)
2. Populate from `government_services_template.csv` verified fields
3. Mark `is_active = True` for all 56 (all current-active)

### Phase 3d: CSV Ingestion (53,091 records)
1. Validate each row with Pydantic validators
2. Upsert `BusinessLicenseHolder` by ACCOUNT NUMBER
3. Insert `BusinessLicense` per record with FK to `BusinessLicenseHolder` and `GovernmentService`
4. Skip `LICENSE STATUS CHANGE DATE` (100% NULL)

### Phase 3e: RAG Content
1. Populate `OfficialSource` from `source_registry.csv` (56 sources)
2. Create RAG documents using `rag_document_template.md`
3. Chunk into `DocumentChunk` records
4. Generate embeddings for `DocumentChunk.embedding` (pgvector)

---

## 11. Test Results

```
35 passed, 0 failed, 2 warnings (cache permission warnings only)
```

| Test Group | Tests | Result |
|------------|-------|--------|
| License Type Extraction | 10 | ✅ All passed |
| Template Schema Validation | 9 | ✅ All passed |
| URL Validation | 3 | ✅ All passed |
| Duplicate Detection | 3 | ✅ All passed |
| NOT_AVAILABLE Handling | 3 | ✅ All passed |
| Official Source Validation | 7 | ✅ All passed |

**Test file**: [`tests/unit/test_supplementary_validation.py`](file:///D:/User/IRWA_project/tests/unit/test_supplementary_validation.py)

---

## Files Created

| File | Location |
|------|----------|
| `license_types.csv` | [`data/supplementary/`](file:///D:/User/IRWA_project/data/supplementary/license_types.csv) |
| `government_service_schema.md` | [`data/supplementary/`](file:///D:/User/IRWA_project/data/supplementary/government_service_schema.md) |
| `government_services_template.csv` | [`data/supplementary/`](file:///D:/User/IRWA_project/data/supplementary/government_services_template.csv) |
| `source_registry.csv` | [`data/supplementary/`](file:///D:/User/IRWA_project/data/supplementary/source_registry.csv) |
| `schema_gap_analysis.md` | [`data/supplementary/`](file:///D:/User/IRWA_project/data/supplementary/schema_gap_analysis.md) |
| `rag_document_template.md` | [`data/supplementary/`](file:///D:/User/IRWA_project/data/supplementary/rag_document_template.md) |
| `supplementary_data_validation.md` | [`data/supplementary/`](file:///D:/User/IRWA_project/data/supplementary/supplementary_data_validation.md) |
| `data_collection_checklist.md` | [`data/supplementary/`](file:///D:/User/IRWA_project/data/supplementary/data_collection_checklist.md) |
| `test_supplementary_validation.py` | [`tests/unit/`](file:///D:/User/IRWA_project/tests/unit/test_supplementary_validation.py) |
| `build_supplementary.py` | [`data/profiling/`](file:///D:/User/IRWA_project/data/profiling/build_supplementary.py) |
| `extract_license_types.py` | [`data/profiling/`](file:///D:/User/IRWA_project/data/profiling/extract_license_types.py) |
| `gen_checklist.py` | [`data/profiling/`](file:///D:/User/IRWA_project/data/profiling/gen_checklist.py) |

## Files Modified

| File | Change |
|------|--------|
| [`docs/AI_DATA_INTEGRATION_PLAN.md`](file:///D:/User/IRWA_project/docs/AI_DATA_INTEGRATION_PLAN.md) | Updated Sections 17–20 with Phase 1 real data findings (Phase 1 task) |

> No backend code was modified. No SQLAlchemy models were modified. No Alembic migrations were created. No PostgreSQL data was inserted. No embeddings were generated. No LLM was configured. No agents were modified. No frontend was modified.

---

## Stop Condition Confirmed

**PHASE 2 COMPLETE — WAITING FOR APPROVAL FOR PHASE 3**
