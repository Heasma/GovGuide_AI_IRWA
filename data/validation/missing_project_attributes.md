# GovGuide AI -- Missing Project Attributes Analysis

**Dataset**: Business_Licenses_-_Current_Active_20260819.csv  
**Analysis Date**: 2026-08-19  
**Basis**: Actual CSV profiling (53,091 rows, 37 columns confirmed)

---

## Purpose

This document evaluates whether the dataset provides the information required
for a complete GovGuide AI government service knowledge base.

---

## Attribute Availability Matrix

| Required Attribute | Availability | CSV Field(s) Available | Gap Description |
|-------------------|-------------|----------------------|-----------------|
| **Service Name** | Partially Available | `LICENSE DESCRIPTION` (56 unique values), `BUSINESS ACTIVITY` (2,463 unique combos) | LICENSE DESCRIPTION provides license TYPE name (e.g., "Limited Business License") but not a citizen-facing service name like "Apply for a Business License" |
| **Service Category** | Partially Available | `LICENSE CODE` (56 unique codes), `LICENSE DESCRIPTION` | Categories exist but are license-type codes, not standardized GovGuide categories |
| **Service Description** | Partially Available | `BUSINESS ACTIVITY` | Activity descriptions exist but are regulated activity labels (e.g., "Retail Sales of General Merchandise"), not procedural service descriptions |
| **Eligibility Criteria** | Not Available | None | No field describes who is eligible to apply for a license |
| **Required Documents** | Not Available | None | No field lists required application documents |
| **Application Procedure** | Not Available | None | No step-by-step procedure described. Only APPLICATION TYPE (ISSUE/RENEW) provides workflow hint |
| **Application Requirements** | Partially Available | `APPLICATION REQUIREMENTS COMPLETE` (date field) | Only confirms WHEN requirements were met, not WHAT they are |
| **Fees** | Not Available | `PAYMENT DATE` (date field only) | Payment date confirms a fee was paid, but amount is absent |
| **Processing Time** | Partially Available (Derived) | `APPLICATION CREATED DATE`, `DATE ISSUED` | Processing time can be DERIVED for records where both dates exist (but APPLICATION CREATED DATE is 78.9% missing) |
| **License Validity Period** | Available | `LICENSE TERM START DATE`, `LICENSE TERM EXPIRATION DATE` | Full validity period is available with high completeness |
| **Renewal Procedure** | Partially Available | `APPLICATION TYPE` = "RENEW" | Confirms renewal exists but provides no procedural steps |
| **Responsible Government Office** | Not Available | None | No field identifies the city department/bureau responsible for issuing the license |
| **Official Website/URL** | Not Available | None | No URL field in the dataset |
| **Official Source** | Not Available | None | No reference to official policy documents, ordinances, or circulars |
| **Contact Information** | Not Available | None | No phone number, email, or office address for the issuing authority |
| **Geographic Jurisdiction** | Available | `WARD`, `COMMUNITY AREA NAME`, `NEIGHBORHOOD`, `POLICE DISTRICT` | Rich geographic data enabling location-based filtering |
| **Application Type** | Partially Available | `APPLICATION TYPE` (6 values: ISSUE, RENEW, C_LOC, C_SBA, C_CAPA, C_EXPA) | Types identified but not human-described |
| **License Status** | Available | `LICENSE STATUS` | Currently only "AAI" (Active After Issuance) -- entire dataset is current active |
| **Business Identity** | Available | `LEGAL NAME`, `DOING BUSINESS AS NAME` | Full business name data available |
| **License Number** | Available | `LICENSE NUMBER`, `LICENSE ID` | Unique identifiers available |
| **Physical Location** | Available | `ADDRESS`, `CITY`, `STATE`, `ZIP CODE`, `LATITUDE`, `LONGITUDE` | Rich location data with geocoding |

---

## Summary Counts

| Status | Count | Examples |
|--------|-------|---------|
| Available | 6 | License validity period, business identity, license number, physical location, geographic jurisdiction, license status |
| Partially Available | 7 | Service name, service category, service description, application requirements, processing time (derived), renewal procedure, application type |
| Not Available | 7 | Eligibility, required documents, application procedure, fees, responsible office, official URL, contact information |
| Needs GS Office Data | 7 | All "Not Available" items require supplementary official data |

---

## Critical Gap: The Dataset Describes Results, Not Procedures

The Business Licenses dataset is an **operational record** of issued licenses.
It tells us:

- WHAT licenses exist (LICENSE DESCRIPTION, BUSINESS ACTIVITY)
- WHO holds them (LEGAL NAME, ACCOUNT NUMBER)
- WHERE they operate (ADDRESS, WARD, LATITUDE, LONGITUDE)
- WHEN they were issued and expire (DATE ISSUED, LICENSE TERM EXPIRATION DATE)
- WHAT STATUS they currently have (LICENSE STATUS = AAI for all records)

It does NOT tell us:

- HOW to apply
- WHAT documents to bring
- HOW MUCH it costs
- WHO to contact
- WHERE to apply
- WHAT the eligibility requirements are

---

## Derived Information Possible From Dataset

| Derived Attribute | Method | Feasibility |
|-------------------|--------|-------------|
| Average processing time | DATE_ISSUED minus APPLICATION_CREATED_DATE | Limited -- 78.9% of APPLICATION CREATED DATE is NULL |
| License term duration | LICENSE TERM EXPIRATION DATE minus LICENSE TERM START DATE | High -- both fields nearly complete |
| Active business count by ward | GROUP BY WARD, COUNT(*) | High |
| License type distribution | GROUP BY LICENSE CODE / LICENSE DESCRIPTION | High -- 56 categories |
| Business density by neighborhood | GROUP BY NEIGHBORHOOD | High |
| Multi-activity businesses | Count of pipe-delimited BUSINESS ACTIVITY entries | Medium |

---

## Recommendation

The dataset alone is insufficient for a complete GovGuide AI knowledge base.

It provides excellent STRUCTURED DATA for:
- License type categorization
- Geographic service mapping
- Business identity lookup
- License status verification

It requires SUPPLEMENTARY OFFICIAL CONTENT for:
- Procedural guidance (how to apply)
- Eligibility rules
- Required documents
- Fee schedules
- Responsible office details
- Official policy sources

See `gs_office_additional_data_requirements.md` for the full supplementary data collection plan.
