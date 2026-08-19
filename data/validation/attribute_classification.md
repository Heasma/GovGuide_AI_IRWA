# GovGuide AI -- Attribute Classification

**Dataset**: Business_Licenses_-_Current_Active_20260819.csv  
**Classification Date**: 2026-08-19  
**Basis**: Actual CSV inspection (37 columns confirmed)

---

## Classification Categories

- **A. CORE SERVICE DATA** -- directly describes the government service/license type
- **B. LICENSE / APPLICATION DATA** -- license lifecycle and workflow fields
- **C. LOCATION DATA** -- physical/geographic fields
- **D. ORGANIZATION / BUSINESS DATA** -- entity identity fields
- **E. STATUS / LIFECYCLE DATA** -- current state and status tracking
- **F. TEMPORAL DATA** -- date and time fields
- **G. IDENTIFIER DATA** -- unique IDs and key fields
- **H. POTENTIALLY IRRELEVANT DATA** -- unlikely to support GovGuide AI use cases
- **I. UNKNOWN** -- needs domain confirmation

---

## Classification Table

| # | CSV Column | Category | Code | Rationale |
|---|-----------|----------|------|-----------|
| 1 | `ID` | Identifier Data | G | Composite unique record key (ACCOUNT_NO + term start year). Not a natural government ID. |
| 2 | `LICENSE ID` | Identifier Data | G | Numeric primary ID for the license record. Key linking field. |
| 3 | `ACCOUNT NUMBER` | Identifier Data | G | Business account number -- links all licenses to one business entity. Critical grouping key. |
| 4 | `SITE NUMBER` | Identifier Data | G | Location index for multi-site businesses. Low value on its own. |
| 5 | `LEGAL NAME` | Organization / Business Data | D | Registered legal name of the business entity. Essential for search and display. |
| 6 | `DOING BUSINESS AS NAME` | Organization / Business Data | D | Trade/DBA name -- often the public-facing name citizens know. High RAG relevance. |
| 7 | `ADDRESS` | Location Data | C | Street address of the licensed premises. Essential for location search and display. |
| 8 | `CITY` | Location Data | C | City name. Expected to be CHICAGO for nearly all records. Useful for filtering. |
| 9 | `STATE` | Location Data | C | State abbreviation. Expected IL. Useful only if non-IL records exist. |
| 10 | `ZIP CODE` | Location Data | C | US ZIP code. Useful for geographic filtering. |
| 11 | `WARD` | Location Data | C | Chicago City Council ward. High relevance for neighborhood-based service queries. |
| 12 | `PRECINCT` | Location Data | C | Election precinct within ward. Lower citizen relevance than ward. |
| 13 | `WARD PRECINCT` | Location Data | C | Composite WARD-PRECINCT. Redundant if WARD and PRECINCT are separate. |
| 14 | `POLICE DISTRICT` | Location Data | C | CPD district. Useful for area-based filtering. |
| 15 | `COMMUNITY AREA` | Location Data | C | Standard Chicago community area number (1-77). Useful for spatial grouping. |
| 16 | `COMMUNITY AREA NAME` | Location Data | C | Human-readable community area name (e.g., UPTOWN). High citizen relevance. |
| 17 | `NEIGHBORHOOD` | Location Data | C | Neighborhood name within community area. High relevance for local queries. |
| 18 | `LICENSE CODE` | Core Service Data | A | Numeric code that categorizes the license type. Key for service classification. |
| 19 | `LICENSE DESCRIPTION` | Core Service Data | A | Human-readable license type name (e.g., "Limited Business License"). Core RAG content. |
| 20 | `BUSINESS ACTIVITY ID` | Core Service Data | A | Pipe-delimited activity code(s). Identifies regulated activities. Useful for sub-categorization. |
| 21 | `BUSINESS ACTIVITY` | Core Service Data | A | Pipe-delimited activity descriptions. High-value text for RAG chunking and search. |
| 22 | `LICENSE NUMBER` | License / Application Data | B | Official license number issued. Useful for verification queries. |
| 23 | `APPLICATION TYPE` | License / Application Data | B | ISSUE / RENEW / C_LOC etc. Indicates the stage of the application lifecycle. |
| 24 | `APPLICATION CREATED DATE` | Temporal Data | F | Date application was created. Useful for processing time analysis. |
| 25 | `APPLICATION REQUIREMENTS COMPLETE` | License / Application Data | B | Date requirements were completed. Indicates readiness stage. |
| 26 | `PAYMENT DATE` | License / Application Data | B | Fee payment date. Indirectly confirms fee was paid. |
| 27 | `CONDITIONAL APPROVAL` | License / Application Data | B | Y/N flag for conditional approvals. Useful for status nuance. |
| 28 | `LICENSE TERM START DATE` | Temporal Data | F | Start date of license validity. Key for active-status determination. |
| 29 | `LICENSE TERM EXPIRATION DATE` | Temporal Data | F | Expiration date. Critical for identifying active vs expiring licenses. |
| 30 | `LICENSE APPROVED FOR ISSUANCE` | Temporal Data | F | Approval date. Useful for processing time calculation. |
| 31 | `DATE ISSUED` | Temporal Data | F | Formal issuance date. |
| 32 | `LICENSE STATUS` | Status / Lifecycle Data | E | Current status code (e.g., AAI = Active After Issuance). Core filtering field. |
| 33 | `LICENSE STATUS CHANGE DATE` | Status / Lifecycle Data | E | Date of last status change. Useful for recency determination. |
| 34 | `SSA` | Location Data | C | Special Service Area number. Niche -- may be relevant for certain business district queries. |
| 35 | `LATITUDE` | Location Data | C | WGS84 latitude. Enables map-based queries and proximity search. |
| 36 | `LONGITUDE` | Location Data | C | WGS84 longitude. Pairs with LATITUDE. |
| 37 | `LOCATION` | Location Data | C | WKT POINT geometry string. Redundant with LAT/LON but useful for GIS tools. |

---

## Summary Count

| Category | Count | Fields |
|----------|-------|--------|
| A. Core Service Data | 4 | LICENSE CODE, LICENSE DESCRIPTION, BUSINESS ACTIVITY ID, BUSINESS ACTIVITY |
| B. License / Application Data | 5 | LICENSE NUMBER, APPLICATION TYPE, APPLICATION REQUIREMENTS COMPLETE, PAYMENT DATE, CONDITIONAL APPROVAL |
| C. Location Data | 14 | ADDRESS, CITY, STATE, ZIP CODE, WARD, PRECINCT, WARD PRECINCT, POLICE DISTRICT, COMMUNITY AREA, COMMUNITY AREA NAME, NEIGHBORHOOD, SSA, LATITUDE, LONGITUDE, LOCATION (15 incl. LOCATION) |
| D. Organization / Business Data | 2 | LEGAL NAME, DOING BUSINESS AS NAME |
| E. Status / Lifecycle Data | 2 | LICENSE STATUS, LICENSE STATUS CHANGE DATE |
| F. Temporal Data | 5 | APPLICATION CREATED DATE, LICENSE TERM START DATE, LICENSE TERM EXPIRATION DATE, LICENSE APPROVED FOR ISSUANCE, DATE ISSUED |
| G. Identifier Data | 4 | ID, LICENSE ID, ACCOUNT NUMBER, SITE NUMBER |
| H. Potentially Irrelevant | 0 | None identified at this stage |
| I. Unknown | 1 | PRECINCT (low citizen utility but not irrelevant) |

---

## Key Observations

1. **Core service description is minimal** -- LICENSE DESCRIPTION and BUSINESS ACTIVITY are the only text fields suitable for RAG chunking. These alone provide limited retrieval depth.
2. **No eligibility, fees, required documents, processing time, or official URLs** are present in this dataset.
3. **Location data is rich** -- 14+ fields enable powerful geographic filtering.
4. **License lifecycle is trackable** -- multiple date fields allow processing-time analysis.
5. **BUSINESS ACTIVITY is pipe-delimited** -- will require splitting during transformation (Phase 2+).
6. **Supplementary official information is required** to build a complete GovGuide AI knowledge base.
