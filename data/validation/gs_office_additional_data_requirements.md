# GovGuide AI -- Government Service Office Additional Data Requirements

**Dataset**: Business_Licenses_-_Current_Active_20260819.csv  
**Analysis Date**: 2026-08-19  
**Basis**: Phase 1 profiling findings (53,091 records, 37 columns)

---

## Overview

The Business Licenses dataset covers 56 distinct license types (LICENSE CODE / LICENSE DESCRIPTION)
issued by the City of Chicago to businesses operating in Chicago.

The dataset is an **operational record** and lacks the procedural, eligibility,
and contact information required by GovGuide AI to answer citizen queries.

This document specifies exactly what additional official information must be
collected from the relevant Government Service (GS) Office -- the
**City of Chicago Department of Business Affairs and Consumer Protection (BACP)** --
to build a complete GovGuide AI knowledge base.

---

## Primary GS Office

**Department**: City of Chicago -- Department of Business Affairs and Consumer Protection (BACP)  
**Likely URL**: https://www.chicago.gov/city/en/depts/bacp.html  
**License Portal**: https://businesslicenses.cityofchicago.org  

---

## Required Information Per License Type

The following must be collected **for each of the 56 license types** identified in the dataset.

### 1. License Type Identity

| Required Item | Status in Dataset | Source |
|---------------|------------------|--------|
| License code (numeric) | Available (LICENSE CODE) | BACP official list |
| License description (name) | Available (LICENSE DESCRIPTION) | BACP official list |
| Plain-language service name | Not Available | BACP website |
| License type overview / summary | Not Available | BACP website / ordinance |

### 2. Eligibility Criteria

| Required Item | Status in Dataset | Source |
|---------------|------------------|--------|
| Who can apply (individual / business / entity type) | Not Available | BACP website per license type |
| Minimum requirements (age, residency, citizenship) | Not Available | BACP ordinance / regulations |
| Business type eligibility (LLC, sole proprietor, etc.) | Not Available | BACP guidelines |
| Zoning or location restrictions | Not Available | Chicago Zoning Ordinance |
| Prior license or certification requirements | Not Available | BACP per license type |
| Disqualifying conditions | Not Available | BACP ordinance |

### 3. Required Documents

| Required Item | Status in Dataset | Source |
|---------------|------------------|--------|
| List of required documents per license type | Not Available | BACP checklist per license |
| Government-issued ID requirements | Not Available | BACP checklist |
| Business registration documents | Not Available | Illinois Secretary of State |
| Insurance certificates required | Not Available | BACP per license type |
| Inspection certificates required | Not Available | BACP per license type |
| Tax clearance requirements | Not Available | Chicago Department of Revenue |
| Health department clearance | Not Available | Chicago CDPH (if applicable) |

### 4. Application Procedure

| Required Item | Status in Dataset | Source |
|---------------|------------------|--------|
| Step-by-step application process | Not Available | BACP website |
| Online application portal URL | Not Available | businesslicenses.cityofchicago.org |
| In-person application location and hours | Not Available | BACP offices |
| Required forms or form numbers | Not Available | BACP website |
| Application submission method (online / in-person / mail) | Not Available | BACP website |
| Inspection scheduling steps | Not Available | BACP / relevant dept |
| Pre-application consultation availability | Not Available | BACP website |

### 5. Fees

| Required Item | Status in Dataset | Source |
|---------------|------------------|--------|
| License fee amount by license type | Not Available | BACP fee schedule |
| Late renewal penalty fees | Not Available | BACP fee schedule |
| Inspection fees (if separate) | Not Available | BACP / inspection dept |
| Fee waiver eligibility | Not Available | BACP / city ordinance |
| Payment methods accepted | Not Available | BACP website |
| Currency format | Not Available | BACP fee schedule |

### 6. Processing Time

| Required Item | Status in Dataset | Source |
|---------------|------------------|--------|
| Standard processing time per license type | Not Available | BACP SLA / website |
| Expedited processing availability | Not Available | BACP website |
| Inspection wait times | Not Available | BACP / relevant dept |
| Peak period delays | Not Available | BACP operational data |

> Note: AVERAGE processing time CAN be derived from the dataset where
> APPLICATION_CREATED_DATE and DATE_ISSUED are both populated (approximately
> 21% of records have APPLICATION_CREATED_DATE).

### 7. Renewal Procedure

| Required Item | Status in Dataset | Source |
|---------------|------------------|--------|
| Renewal timeline (when to start) | Not Available | BACP website |
| Renewal procedure steps | Not Available | BACP website |
| Renewal fee schedule | Not Available | BACP fee schedule |
| Grace period after expiry | Not Available | BACP ordinance |
| Documents required for renewal | Not Available | BACP renewal checklist |

### 8. Responsible Office and Contact Information

| Required Item | Status in Dataset | Source |
|---------------|------------------|--------|
| Responsible city department name | Not Available | BACP / city org chart |
| Office address (walk-in location) | Not Available | BACP website |
| Phone number | Not Available | BACP website |
| Email address or contact form URL | Not Available | BACP website |
| Business hours | Not Available | BACP website |
| Specific division or unit responsible per license type | Not Available | BACP internal directory |

### 9. Official Sources and Legal References

| Required Item | Status in Dataset | Source |
|---------------|------------------|--------|
| Municipal code reference | Not Available | Chicago Municipal Code (Municode) |
| Official ordinance or regulation number | Not Available | Chicago City Council records |
| Official policy circulars | Not Available | BACP / City Clerk office |
| Official forms (PDF links) | Not Available | BACP website |
| Official FAQ page URL | Not Available | BACP website |
| Last updated / effective date of policy | Not Available | BACP website |

### 10. Special Categories Identified in Dataset

The following specific business activity types appeared frequently in the dataset
and may require license-type-specific supplementary content:

| Business Activity (from CSV) | Frequency | Special Data Needed |
|-----------------------------|-----------|---------------------|
| Retail Sales of General Merchandise | High | Zoning, health permit requirements |
| Operation of a Restaurant | High | Health permit, CDPH inspection |
| Tavern / Sale of Packaged Liquor | High | Illinois Liquor Control Commission data |
| Motor Vehicle Repair | High | Environmental compliance requirements |
| Operation of a Hotel / Motel | Medium | Fire inspection, health requirements |
| Childcare Services | Medium | DCFS requirements, background checks |
| Operation of Medical / Surgical Hospital | Low | State licensing cross-reference |
| Not-For-Profit activities | Low | 501(c)(3) documentation requirements |

---

## Data Collection Priority Order

| Priority | Item | Rationale |
|----------|------|-----------|
| 1 (Highest) | Application procedure per license type | Core GovGuide citizen query |
| 2 | Required documents per license type | Core GovGuide citizen query |
| 3 | Fee schedule per license type | Core GovGuide citizen query |
| 4 | Eligibility criteria per license type | Core GovGuide citizen query |
| 5 | Contact information for BACP | Enables citizen follow-up |
| 6 | Official source URLs per license type | Required for RAG grounding |
| 7 | Processing time per license type | Frequently asked by citizens |
| 8 | Renewal procedure | Renewal = most common query after initial application |
| 9 | Legal references (ordinance numbers) | Required for source citations |
| 10 | Inspection requirements | Specific to higher-risk license types |

---

## Data Collection Methods Recommended

1. **Web scraping**: BACP website (https://www.chicago.gov/city/en/depts/bacp.html)
2. **Chicago Open Data Portal**: Additional datasets on license types, fees, inspections
3. **Chicago Municipal Code (Municode)**: Ordinance text per license category
4. **PDF extraction**: Official BACP application guides and fee schedules
5. **API access**: Business License API if available from Chicago Data Portal

---

## Do NOT Collect

- Personal information about individual license holders
- Tax identification numbers
- Private business financial data
- Individual applicant names
- Private contact details of business owners

---

## Files This Feeds Into (Future Phases)

- `OfficialSource` records (one per license type URL)
- `DocumentChunk` records (chunked procedure text)
- `GovernmentOffice` records (BACP office data)
- `GovernmentService` description enrichment
