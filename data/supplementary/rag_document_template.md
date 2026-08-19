# GovGuide AI — RAG Document Template

**Date**: 2026-08-19  
**Phase**: 2 — Supplementary Data Design  
**Purpose**: Canonical document structure for RAG-ready service content

---

## Overview

This template defines the canonical structure for GovGuide AI's knowledge base documents.
Each document represents one government service (license type) and will be:
1. Stored as an `OfficialSource` record
2. Chunked into `DocumentChunk` records for vector retrieval
3. Used by the `ResearchAgent` and `AdvisoryAgent` to answer citizen queries

---

## Template Structure

```
================================================================================
GOVGUIDE AI — GOVERNMENT SERVICE DOCUMENT
================================================================================

Service Name:         [Citizen-facing name, e.g., "Apply for a Limited Business License"]
License Type:         [LICENSE DESCRIPTION from CSV, e.g., "Limited Business License"]
License Code:         [LICENSE CODE from CSV, e.g., "1010"]
Responsible Department: [Government department, e.g., "City of Chicago BACP"]
Document Version:     [Date verified, e.g., "2026-08-19"]
Official Source URL:  [Primary URL where this information was obtained]

================================================================================
OVERVIEW
================================================================================

[1-2 paragraph plain-language description of what this license/service is,
 who needs it, and why it exists.]

Source: [URL]

================================================================================
ELIGIBILITY
================================================================================

Who can apply:
- [Eligible entity types: individual, LLC, corporation, etc.]

Requirements:
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

Restrictions:
- [Restriction 1, e.g., zoning, distance, age]
- [Restriction 2]

State license required: [Yes/No — If Yes: [State agency and license type]]

Source: [URL]

================================================================================
REQUIRED DOCUMENTS
================================================================================

[Numbered or bulleted list of required documents]

1. [Document 1, e.g., Proof of property (lease or ownership)]
2. [Document 2, e.g., Business entity documents (Articles of Incorporation)]
3. [Document 3, e.g., Federal Employer Identification Number (EIN)]
4. [Document 4, e.g., Illinois Department of Revenue account]
5. [Document 5 — if inspection-specific]

Notes:
- [Any notes on document requirements, e.g., "must be originals not copies"]

Source: [URL]

================================================================================
APPLICATION PROCEDURE
================================================================================

How to Apply: [Online | In-Person | Both]

Online Application: [URL to portal, e.g., https://www.chicago.gov/BusinessDirect]

In-Person Location:
  [Address, e.g., City Hall, 121 N. LaSalle Street, Room 800, Chicago, IL 60602]
  Hours: [Business hours]

Step-by-Step Process:

1. [Step 1, e.g., Determine your specific license type at the BACP website]
2. [Step 2, e.g., Apply online via Chicago Business Direct or in-person at SBC]
3. [Step 3, e.g., Undergo zoning review for your business location]
4. [Step 4, e.g., Complete the full license application]
5. [Step 5, e.g., Schedule and pass required inspections]
6. [Step 6, e.g., Pay the license fee]
7. [Step 7, e.g., Receive your license]

Required Inspections: [Yes/No]
Inspecting Agencies:
- [Agency 1, e.g., Chicago Department of Public Health (CDPH)]
- [Agency 2, e.g., Chicago Fire Department]

Zoning Review Required: [Yes/No]
Background Check Required: [Yes/No — If Yes: [fingerprinting details]]

Source: [URL]

================================================================================
FEES
================================================================================

License Fee: [Fee amount, e.g., "$500 for a 2-year term"]

Fee Structure:
[If tiered — describe tiers]
[If flat rate — state flat rate]

Additional Fees:
- [Any additional fees, e.g., "$40 per person for fingerprinting"]
- [Publication fees, inspection fees]

Payment Methods: [Online payment | In-person at City Hall | etc.]
Non-Refundable: [Yes/No]
Fee Effective Date: [Date fees apply from]

Source: [URL]

================================================================================
PROCESSING TIME
================================================================================

Estimated Processing Time: [e.g., "2-4 weeks after all requirements are met"]

Notes:
- [Caveats, e.g., "Processing time depends on inspection scheduling"]
- [Peak period notes, e.g., "Longer during January-March renewal period"]

Source: [URL or "NOT_AVAILABLE — contact BACP for current processing times"]

================================================================================
LICENSE VALIDITY & RENEWAL
================================================================================

License Term: [e.g., "2 years"]
Renewal Required: [Yes/No]

Renewal Process:
1. [Renewal step 1, e.g., Renew online via Chicago Business Direct]
2. [Renewal step 2, e.g., Pay renewal fee before expiration date]
3. [Renewal step 3, e.g., Confirm any updated requirements have been met]

Renewal Fee: [Same as initial fee / Different amount]
Renewal Portal: [URL]

Source: [URL]

================================================================================
CONTACT INFORMATION
================================================================================

Department: [Full department name]
Division/Unit: [Specific unit if applicable]

Address:
  [Street address]
  [City, State, ZIP]

Phone: [Phone number]
Email: [Email address]
Business Hours: [Hours]
Website: [Department website URL]
Online Application: [Portal URL]

================================================================================
OFFICIAL SOURCES
================================================================================

Primary Source:
- Title: [Source title]
- URL: [Source URL]
- Source Type: [webpage | pdf | ordinance | portal]
- Last Verified: [Date]

Additional Sources:
- [Source 2 URL — if applicable]
- [Source 3 URL — if applicable]

================================================================================
LEGAL REFERENCES
================================================================================

Municipal Code: [MCC section, e.g., "MCC Title 4, Chapter 4-60"]
Ordinance Reference: [Ordinance number if applicable]
Relevant Regulations: [Any other legal references]

Source: [Municipal Code URL: https://www.chicityclerk.com/about-city-government-chicago-city-council/municipal-code]

================================================================================
DATA QUALITY NOTES
================================================================================

Source Confidence: [VERIFIED | PARTIALLY_VERIFIED | REQUIRES_MANUAL_VERIFICATION]
Data Gaps: [Description of any information that could not be verified]
Verification Date: [Date]

================================================================================
END OF DOCUMENT
================================================================================
```

---

## Chunking Strategy

When this document is split into `DocumentChunk` records for pgvector retrieval:

| Section | Chunk Boundary | Rationale |
|---------|---------------|-----------|
| Overview | 1 chunk | Short — context-setting paragraph |
| Eligibility | 1 chunk | Complete eligibility rules together |
| Required Documents | 1 chunk | Always retrieved together for "what documents" queries |
| Application Procedure | 1-2 chunks | Split at step 4-5 if too long (>300 tokens) |
| Fees | 1 chunk | Always retrieved together for "how much" queries |
| Processing Time | 1 chunk (merged with Fees) | Short — merge with Fees for efficiency |
| Renewal | 1 chunk | Separate — renewal queries are distinct |
| Contact Information | 1 chunk | Always retrieved for "where to apply" queries |

**Target chunk size**: 200–400 tokens  
**Overlap**: 50 tokens between adjacent chunks  
**Metadata fields per chunk**: license_code, license_description, section_name, source_url, verified_date

---

## Example: Completed Document (Limited Business License)

```
================================================================================
GOVGUIDE AI — GOVERNMENT SERVICE DOCUMENT
================================================================================

Service Name:         Apply for a Limited Business License (LBL)
License Type:         Limited Business License
License Code:         1010
Responsible Department: City of Chicago -- Department of Business Affairs and Consumer Protection (BACP)
Document Version:     2026-08-19
Official Source URL:  https://www.chicago.gov/BusinessDirect

================================================================================
OVERVIEW
================================================================================

The Limited Business License (LBL) is the standard city business license for most
general retail and service businesses operating in Chicago that do not require a
more specific license type. It is issued by the City of Chicago Department of
Business Affairs and Consumer Protection (BACP).

If your business activity is not listed under a specific license category (such
as food, liquor, or childcare), you will most likely need an LBL to operate legally.

Source: https://www.chicago.gov/BusinessDirect

================================================================================
ELIGIBILITY
================================================================================

Who can apply:
- Any individual, sole proprietor, partnership, LLC, corporation, or non-profit
  operating a general retail or service business in Chicago.

Requirements:
- Business location must pass a zoning review.
- All outstanding City of Chicago debts must be resolved before a license is issued.
- Business must not require a more specific license type (food, liquor, childcare, etc.).

Restrictions:
- Location must be properly zoned for the proposed business activity.

State license required: No

Source: https://www.chicago.gov/BusinessDirect

================================================================================
REQUIRED DOCUMENTS
================================================================================

1. Proof of property (current lease or proof of ownership)
2. Business entity documents (e.g., Articles of Incorporation/Organization)
3. Federal Employer Identification Number (EIN)
4. Illinois Department of Revenue account number
5. Business Information Sheet (required if applying in person)

Source: https://www.chicago.gov/BusinessDirect

================================================================================
APPLICATION PROCEDURE
================================================================================

How to Apply: Online or In-Person
Online Application: https://www.chicago.gov/BusinessDirect

In-Person Location:
  City Hall, 121 N. LaSalle Street, Room 800, Chicago, IL 60602
  Hours: Monday-Friday 8:00 AM - 5:00 PM

Step-by-Step Process:
1. Verify that the Limited Business License applies to your business activity.
2. Apply online via Chicago Business Direct or visit the Small Business Center (SBC).
3. Undergo a zoning review for your proposed business location.
4. Complete the full license application.
5. Pass any applicable inspections (type varies by business activity).
6. Pay the license fee.
7. Receive your Limited Business License.

Required Inspections: Yes (varies by business activity)
Zoning Review Required: Yes
Background Check Required: No

Source: https://www.chicago.gov/BusinessDirect

================================================================================
FEES
================================================================================

License Fee: $500 (2-year term)
Fee Structure: Flat rate regardless of business size or location.
Payment Methods: Online via Chicago Business Direct | In-person at City Hall
Non-Refundable: Yes
Fee Effective Date: January 1, 2026

Source: https://www.chicago.gov/BusinessDirect

================================================================================
CONTACT INFORMATION
================================================================================

Department: City of Chicago -- Department of Business Affairs and Consumer Protection (BACP)
Division/Unit: Small Business Center (SBC)
Address: City Hall, 121 N. LaSalle Street, Room 800, Chicago, IL 60602
Phone: 312-74-GOBIZ (312-744-6249)
Email: businesslicense@cityofchicago.org
Hours: Monday-Friday 8:00 AM - 5:00 PM
Website: https://www.chicago.gov/city/en/depts/bacp.html
Online Application: https://www.chicago.gov/BusinessDirect

================================================================================
LEGAL REFERENCES
================================================================================

Municipal Code: MCC Title 4, Chapter 4-60

================================================================================
DATA QUALITY NOTES
================================================================================

Source Confidence: VERIFIED
Data Gaps: Specific required documents may vary by business type. Confirm at application.
Verification Date: 2026-08-19
================================================================================
```
