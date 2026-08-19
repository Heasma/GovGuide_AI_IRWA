# GovGuide AI -- Dataset Quality Report

**Dataset**: `Business_Licenses_-_Current_Active_20260819.csv`  
**Generated**: 2026-08-19 21:47:44  
**Rows**: 53,091  
**Columns**: 37  
**SHA-256**: `d3246a6657fe8cbb46a12a5fc6027569d2ca783ab4b7040449eac4dfaa564a41`  
**Encoding**: utf-8-sig  
**Delimiter**: `','`  

---

## Column Quality Summary

| # | Column | Type | Missing % | Non-Null | Unique | Sample | Potential Meaning |
|---|--------|------|-----------|----------|--------|--------|-------------------|
| 1 | `ID` | text | 0.0% | 53,091 | 53,090 | 2948166-20280716; 2818291-20261116; 40561-20261016 | Composite unique record ID (ACCOUNT_NO-LICENSE_TERM_START_YEAR) |
| 2 | `LICENSE ID` | text | 0.0% | 53,091 | 53,091 | 3095906; 3082190; 3096968 | Numeric license identifier -- primary numeric key |
| 3 | `ACCOUNT NUMBER` | text | 0.0% | 53,091 | 36,262 | 487329; 432056; 34237 | Business account number -- groups all licenses per entity |
| 4 | `SITE NUMBER` | text | 0.0% | 53,091 | 467 | 2; 1; 5 | Location index for multi-site business accounts |
| 5 | `LEGAL NAME` | text | 0.0% | 53,091 | 36,161 | CHICAGO BH HOSPITAL, LLC; ALTRUISTIC ESTHETICS INC.; THE ARMADILLO'S PILLOW INC | Registered legal/corporate name of the business |
| 6 | `DOING BUSINESS AS NAME` | text | 0.17% | 53,001 | 38,708 | Montrose Behavioral Health Hospital; ALTRUISTIC ESTHETICS; THE ARMADILLO'S PILLOW INC | Trade/DBA name (may differ from legal name) |
| 7 | `ADDRESS` | location | 0.0% | 53,091 | 40,127 | 4840 N MARINE DR 5 FLOORS; 4809 N RAVENSWOOD AVE  116; 6753 N SHERIDAN RD 1ST | Street address of the licensed premises |
| 8 | `CITY` | location | 0.0% | 53,091 | 951 | CHICAGO; LA GRANGE; WHEATON | City (expected: CHICAGO for all or most records) |
| 9 | `STATE` | location | 0.0% | 53,091 | 48 | IL; TN; MN | US state abbreviation (expected: IL) |
| 10 | `ZIP CODE` | location | 0.03% | 53,075 | 1,186 | 60640; 60626; 60619 | US ZIP code of the licensed premises |
| 11 | `WARD` | location | 7.69% | 49,007 | 50 | 46; 47; 49 | Chicago City Council ward number |
| 12 | `PRECINCT` | location | 8.07% | 48,804 | 76 | 40; 32; 7 | Election precinct within the ward |
| 13 | `WARD PRECINCT` | location | 7.41% | 49,155 | 2,513 | 46-40; 47-32; 49-7 | Composite WARD-PRECINCT identifier |
| 14 | `POLICE DISTRICT` | location | 7.6% | 49,054 | 25 | 20; 24; 4 | CPD district number covering the premises |
| 15 | `COMMUNITY AREA` | location | 7.86% | 48,920 | 78 | 3; 1; 47 | Chicago community area number (1-77) |
| 16 | `COMMUNITY AREA NAME` | location | 7.87% | 48,915 | 77 | UPTOWN; ROGERS PARK; BURNSIDE | Human-readable community area name |
| 17 | `NEIGHBORHOOD` | location | 7.92% | 48,886 | 98 | UPTOWN; ROGERS PARK; BURNSIDE | Sub-community neighborhood name |
| 18 | `LICENSE CODE` | date | 0.0% | 53,091 | 56 | 4404; 1010; 8340 | Numeric license category code |
| 19 | `LICENSE DESCRIPTION` | text | 0.0% | 53,091 | 56 | Regulated Business License; Limited Business License; Motor Vehicle Services License | Human-readable license type description |
| 20 | `BUSINESS ACTIVITY ID` | text | 5.81% | 50,009 | 2,463 | 232; 767 | 896 | 956; 711 | Activity code(s) -- may be pipe-delimited |
| 21 | `BUSINESS ACTIVITY` | text | 5.81% | 50,009 | 2,463 | Operation of General Medical / Surg; Retail Sales of General Merchandise; Motor Vehicle Repair - Engine and B | Activity description(s) -- may be pipe-delimited |
| 22 | `LICENSE NUMBER` | text | 0.0% | 53,091 | 52,220 | 2948166; 2818291; 40561 | Official license number issued to the business |
| 23 | `APPLICATION TYPE` | categorical | 0.0% | 53,091 | 6 | RENEW; ISSUE; C_LOC | Application type: ISSUE / RENEW / C_LOC / etc. |
| 24 | `APPLICATION CREATED DATE` | date | 78.9% | 11,201 | 694 | 03/20/2025; 08/03/2026; 07/28/2026 | Date the application was created |
| 25 | `APPLICATION REQUIREMENTS COMPLETE` | date | 0.07% | 53,052 | 661 | 07/28/2026; 04/15/2026; 08/15/2026 | Date all requirements were satisfied |
| 26 | `PAYMENT DATE` | date | 0.26% | 52,953 | 874 | 07/29/2026; 04/15/2026; 08/17/2026 | Date the license fee was paid |
| 27 | `CONDITIONAL APPROVAL` | categorical | 0.0% | 53,091 | 2 | N; Y | Conditional approval flag (Y/N/blank) |
| 28 | `LICENSE TERM START DATE` | date | 0.01% | 53,088 | 537 | 07/16/2028; 11/16/2026; 10/16/2026 | Start date of the current license period |
| 29 | `LICENSE TERM EXPIRATION DATE` | date | 0.0% | 53,091 | 156 | 07/15/2030; 11/15/2028; 10/15/2028 | Expiration date of the current license period |
| 30 | `LICENSE APPROVED FOR ISSUANCE` | date | 4.32% | 50,796 | 764 | 07/29/2026; 04/15/2026; 08/17/2026 | Date approved for issuance |
| 31 | `DATE ISSUED` | date | 0.0% | 53,091 | 569 | 07/30/2026; 04/16/2026; 08/18/2026 | Date the license was formally issued |
| 32 | `LICENSE STATUS` | categorical | 0.0% | 53,091 | 1 | AAI | License status code (AAI = Active After Issuance) |
| 33 | `LICENSE STATUS CHANGE DATE` | date | 100.0% | 0 | 0 |  | Date of most recent status change |
| 34 | `SSA` | location | 73.59% | 14,023 | 53 | 34; 31; 54 | Special Service Area number (Chicago tax district) |
| 35 | `LATITUDE` | location | 7.98% | 48,853 | 29,499 | 41.970352506; 41.9691903575; 42.0050836914 | WGS84 latitude of geocoded address |
| 36 | `LONGITUDE` | location | 7.98% | 48,853 | 29,499 | -87.6501347448; -87.6740389209; -87.6607268964 | WGS84 longitude of geocoded address |
| 37 | `LOCATION` | location | 7.98% | 48,853 | 29,499 | POINT (-87.65013474477234 41.970352; POINT (-87.67403892092791 41.969190; POINT (-87.66072689641621 42.005083 | WKT POINT geometry (lon lat) |

---

## Duplicate Analysis

- **Complete duplicate rows**: 0
- **ID (composite)**: 1 values appear >1 times (1 extra rows)
- **LICENSE ID**: 0 values appear >1 times (0 extra rows)
- **LICENSE NUMBER**: 871 values appear >1 times (871 extra rows)
- **ACCOUNT NUMBER**: 7477 values appear >1 times (16829 extra rows)

> NOTE: Duplicates are NOT deleted. ACCOUNT NUMBER repeating = multiple licenses per business (expected).

---

## Date Field Analysis

| Column | Parse Rate | Min Date | Max Date | Missing |
|--------|-----------|---------|---------|---------|
| `LICENSE CODE` | 100.0% | 1003-01-01 00:00:00 | 8604-01-01 00:00:00 | 0 |
| `APPLICATION CREATED DATE` | 21.1% | 2021-05-21 00:00:00 | 2026-08-18 00:00:00 | 41890 |
| `APPLICATION REQUIREMENTS COMPLETE` | 99.93% | 2021-07-15 00:00:00 | 2026-08-18 00:00:00 | 39 |
| `PAYMENT DATE` | 99.74% | 2022-08-11 00:00:00 | 2026-08-18 00:00:00 | 138 |
| `LICENSE TERM START DATE` | 99.99% | 2024-07-22 00:00:00 | 2028-07-16 00:00:00 | 3 |
| `LICENSE TERM EXPIRATION DATE` | 100.0% | 2026-08-22 00:00:00 | 2030-07-15 00:00:00 | 0 |
| `LICENSE APPROVED FOR ISSUANCE` | 95.68% | 2024-06-02 00:00:00 | 2026-08-18 00:00:00 | 2295 |
| `DATE ISSUED` | 100.0% | 2024-07-15 00:00:00 | 2026-08-18 00:00:00 | 0 |
| `LICENSE STATUS CHANGE DATE` | 0.0% | None | None | 53091 |

---

## Location Field Analysis

| Column | Missing | Missing% | Unique | Notes |
|--------|---------|----------|--------|-------|
| `ADDRESS` | 0 | 0.0% | 40127 | -- |
| `CITY` | 0 | 0.0% | 951 | top_cities: CHICAGO, CICERO, NAPERVILLE |
| `STATE` | 0 | 0.0% | 48 | states: IL, IN, CA |
| `ZIP CODE` | 16 | 0.03% | 1186 | -- |
| `WARD` | 4084 | 7.69% | 50 | -- |
| `PRECINCT` | 4287 | 8.07% | 76 | -- |
| `WARD PRECINCT` | 3936 | 7.41% | 2513 | -- |
| `POLICE DISTRICT` | 4037 | 7.6% | 25 | -- |
| `COMMUNITY AREA` | 4171 | 7.86% | 78 | -- |
| `COMMUNITY AREA NAME` | 4176 | 7.87% | 77 | -- |
| `NEIGHBORHOOD` | 4205 | 7.92% | 98 | -- |
| `SSA` | 39068 | 73.59% | 53 | -- |
| `LATITUDE` | 4238 | 7.98% | 29499 | invalid_lat=0 |
| `LONGITUDE` | 4238 | 7.98% | 29499 | invalid_lon=0 |
| `LOCATION` | 4238 | 7.98% | 29499 | -- |

---

## Sample Records (first 3)

```
{"ID": "2948166-20280716", "LICENSE ID": "3095906", "ACCOUNT NUMBER": "487329", "SITE NUMBER": "2", "LEGAL NAME": "CHICAGO BH HOSPITAL, LLC", "DOING BUSINESS AS NAME": "Montrose Behavioral Health Hospital", "ADDRESS": "4840 N MARINE DR 5 FLOORS", "CITY": "CHICAGO", "STATE": "IL", "ZIP CODE": "60640", "WARD": "46", "PRECINCT": "40", "WARD PRECINCT": "46-40", "POLICE DISTRICT": "20", "COMMUNITY AREA": "3", "COMMUNITY AREA NAME": "UPTOWN", "NEIGHBORHOOD": "UPTOWN", "LICENSE CODE": "4404", "LICENSE DESCRIPTION": "Regulated Business License", "BUSINESS ACTIVITY ID": "232", "BUSINESS ACTIVITY": "Operation of General Medical / Surgical Hospital", "LICENSE NUMBER": "2948166", "APPLICATION TYPE": "RENEW", "APPLICATION CREATED DATE": NaN, "APPLICATION REQUIREMENTS COMPLETE": "07/28/2026", "PAYMENT DATE": "07/29/2026", "CONDITIONAL APPROVAL": "N", "LICENSE TERM START DATE": "07/16/2028", "LICENSE TERM EXPIRATION DATE": "07/15/2030", "LICENSE APPROVED FOR ISSUANCE": "07/29/2026", "DATE ISSUED": "07/30/2026", "LICENSE STATUS": "AAI", "LICENSE STATUS CHANGE DATE": NaN, "SSA": "34", "LATITUDE": "41.970352506", "LONGITUDE": "-87.6501347448", "LOCATION": "POINT (-87.65013474477234 41.97035250602275)"}
{"ID": "2818291-20261116", "LICENSE ID": "3082190", "ACCOUNT NUMBER": "432056", "SITE NUMBER": "2", "LEGAL NAME": "ALTRUISTIC ESTHETICS INC.", "DOING BUSINESS AS NAME": "ALTRUISTIC ESTHETICS", "ADDRESS": "4809 N RAVENSWOOD AVE  116", "CITY": "CHICAGO", "STATE": "IL", "ZIP CODE": "60640", "WARD": "47", "PRECINCT": "32", "WARD PRECINCT": "47-32", "POLICE DISTRICT": "20", "COMMUNITY AREA": "3", "COMMUNITY AREA NAME": "UPTOWN", "NEIGHBORHOOD": "UPTOWN", "LICENSE CODE": "1010", "LICENSE DESCRIPTION": "Limited Business License", "BUSINESS ACTIVITY ID": "767 | 896 | 956", "BUSINESS ACTIVITY": "Retail Sales of General Merchandise and Non-Perishable Food | Skincare Services | Provide Waxing Services", "LICENSE NUMBER": "2818291", "APPLICATION TYPE": "RENEW", "APPLICATION CREATED DATE": NaN, "APPLICATION REQUIREMENTS COMPLETE": "04/15/2026", "PAYMENT DATE": "04/15/2026", "CONDITIONAL APPROVAL": "N", "LICENSE TERM START DATE": "11/16/2026", "LICENSE TERM EXPIRATION DATE": "11/15/2028", "LICENSE APPROVED FOR ISSUANCE": "04/15/2026", "DATE ISSUED": "04/16/2026", "LICENSE STATUS": "AAI", "LICENSE STATUS CHANGE DATE": NaN, "SSA": "31", "LATITUDE": "41.9691903575", "LONGITUDE": "-87.6740389209", "LOCATION": "POINT (-87.67403892092791 41.969190357544846)"}
{"ID": "40561-20261016", "LICENSE ID": "3096968", "ACCOUNT NUMBER": "34237", "SITE NUMBER": "1", "LEGAL NAME": "THE ARMADILLO'S PILLOW INC", "DOING BUSINESS AS NAME": "THE ARMADILLO'S PILLOW INC", "ADDRESS": "6753 N SHERIDAN RD 1ST", "CITY": "CHICAGO", "STATE": "IL", "ZIP CODE": "60626", "WARD": "49", "PRECINCT": "7", "WARD PRECINCT": "49-7", "POLICE DISTRICT": "24", "COMMUNITY AREA": "1", "COMMUNITY AREA NAME": "ROGERS PARK", "NEIGHBORHOOD": "ROGERS PARK", "LICENSE CODE": "1010", "LICENSE DESCRIPTION": "Limited Business License", "BUSINESS ACTIVITY ID": NaN, "BUSINESS ACTIVITY": NaN, "LICENSE NUMBER": "40561", "APPLICATION TYPE": "RENEW", "APPLICATION CREATED DATE": NaN, "APPLICATION REQUIREMENTS COMPLETE": "08/15/2026", "PAYMENT DATE": "08/17/2026", "CONDITIONAL APPROVAL": "N", "LICENSE TERM START DATE": "10/16/2026", "LICENSE TERM EXPIRATION DATE": "10/15/2028", "LICENSE APPROVED FOR ISSUANCE": "08/17/2026", "DATE ISSUED": "08/18/2026", "LICENSE STATUS": "AAI", "LICENSE STATUS CHANGE DATE": NaN, "SSA": "54", "LATITUDE": "42.0050836914", "LONGITUDE": "-87.6607268964", "LOCATION": "POINT (-87.66072689641621 42.00508369143515)"}
```
