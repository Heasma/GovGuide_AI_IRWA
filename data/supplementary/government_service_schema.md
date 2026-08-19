# GovGuide AI — Supplementary Government Service Data Schema

**Version**: 1.0  
**Date**: 2026-08-19  
**Phase**: 2 — Supplementary Official Government Data Design  
**Status**: DESIGN ONLY — No database changes made  

---

## Overview

This schema defines the canonical structure for supplementary official government-service
information that complements the Business Licenses CSV dataset.

The CSV dataset provides operational license records (who has a license, where, when).
This supplementary schema provides procedural service information (how to apply, what to bring, costs).

---

## Schema Definition

### Section 1: Identity

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `license_code` | STRING(20) | NO | Numeric code from the CSV (e.g., "1010") |
| `license_description` | STRING(200) | NO | Official license type name from the CSV |
| `service_name` | STRING(300) | YES | Citizen-facing service name (e.g., "Apply for a Limited Business License") |
| `service_category` | STRING(100) | YES | Standardized category (see categories below) |
| `service_subcategory` | STRING(100) | YES | Optional sub-category |
| `service_overview` | TEXT | YES | Plain-language overview paragraph |

### Standardized Service Categories

- `food_beverage` — Food and beverage establishments
- `liquor_alcohol` — Liquor and alcohol licenses
- `childcare_education` — Children's services and educational facilities
- `animal_services` — Animal care and pet services
- `entertainment_amusement` — Entertainment venues, amusement parks, music
- `retail_general` — General retail businesses
- `tobacco` — Tobacco and e-cigarette retailers
- `motor_vehicle` — Automotive services, repair, towing
- `transportation` — Taxis, rideshare, vessels, valet
- `health_medical` — Medical facilities and health services
- `real_estate_property` — Shared housing, hotels
- `manufacturing_wholesale` — Manufacturing and wholesale operations
- `financial_pawnbroker` — Financial services, pawnbrokers, secondhand dealers
- `nonprofit_social` — Not-for-profit organizations
- `events_special` — Special events and temporary permits
- `other` — Uncategorized or mixed-purpose

---

### Section 2: Eligibility

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `eligibility_summary` | TEXT | YES | Plain-English summary of who can apply |
| `eligible_entity_types` | TEXT | YES | Allowed entity types (individual, LLC, corporation, partnership, etc.) |
| `eligibility_restrictions` | TEXT | YES | Restrictions (age, residency, criminal history, zoning, distance, etc.) |
| `state_license_required` | BOOLEAN | YES | Whether a state-level license is also required |
| `state_license_details` | TEXT | YES | Details of required state license (issuing agency, type) |

---

### Section 3: Required Documents

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `required_documents` | TEXT | YES | Pipe-delimited list of required documents |
| `required_documents_notes` | TEXT | YES | Additional notes on document requirements |

---

### Section 4: Application Procedure

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `application_steps` | TEXT | YES | Numbered, pipe-delimited procedure steps |
| `application_method` | STRING(100) | YES | online | in_person | both |
| `application_portal_url` | TEXT | YES | Official online application URL |
| `in_person_address` | STRING(300) | YES | Walk-in application address |
| `required_forms` | TEXT | YES | List of required forms with form numbers |
| `inspection_required` | BOOLEAN | YES | Whether an inspection is required |
| `inspection_agencies` | TEXT | YES | Agencies responsible for inspection |
| `zoning_review_required` | BOOLEAN | YES | Whether a zoning review is required |
| `background_check_required` | BOOLEAN | YES | Whether a fingerprint background check is required |

---

### Section 5: Fees

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `fee_amount` | STRING(100) | YES | Fee amount(s) as string (may be tiered) |
| `fee_description` | TEXT | YES | Plain-English description of the fee structure |
| `fee_effective_date` | DATE | YES | Date from which this fee applies |
| `payment_methods` | STRING(200) | YES | Accepted payment methods |
| `fee_non_refundable` | BOOLEAN | YES | Whether the fee is non-refundable |

---

### Section 6: Processing Time

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `estimated_processing_time` | STRING(100) | YES | Typical processing time (e.g., "2–4 weeks") |
| `processing_time_notes` | TEXT | YES | Caveats (inspection scheduling, peak periods, etc.) |

---

### Section 7: Renewal

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `license_term_years` | INTEGER | YES | License validity period in years |
| `renewal_required` | BOOLEAN | YES | Whether renewal is required |
| `renewal_period` | STRING(100) | YES | Renewal timing (e.g., "Every 2 years") |
| `renewal_steps` | TEXT | YES | Renewal procedure steps |
| `renewal_fee` | STRING(100) | YES | Renewal fee if different from initial |
| `renewal_portal_url` | TEXT | YES | Online renewal URL |

---

### Section 8: Responsible Authority

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `government_department` | STRING(300) | YES | Primary department (e.g., "City of Chicago BACP") |
| `responsible_division` | STRING(300) | YES | Division or unit within the department |
| `office_address` | STRING(500) | YES | Official office address |
| `phone` | STRING(50) | YES | Official phone number |
| `email` | STRING(200) | YES | Official email address |
| `business_hours` | STRING(200) | YES | Office hours |
| `website_url` | TEXT | YES | Official department website URL |

---

### Section 9: Official Sources

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `official_url` | TEXT | YES | Primary official information URL |
| `source_title` | STRING(300) | YES | Title of the source page/document |
| `source_type` | STRING(50) | YES | webpage | pdf | ordinance | portal |
| `source_last_updated` | DATE | YES | Date the source was last updated (if shown) |
| `legal_reference` | STRING(200) | YES | Municipal Code section (e.g., "MCC 4-60") |
| `additional_sources` | TEXT | YES | Pipe-delimited list of additional source URLs |

---

### Section 10: Metadata

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `source_verified_date` | DATE | YES | Date this record was verified |
| `source_confidence` | STRING(20) | YES | VERIFIED | PARTIALLY_VERIFIED | NOT_FOUND | REQUIRES_MANUAL_VERIFICATION |
| `data_gaps` | TEXT | YES | Description of what information could not be verified |
| `notes` | TEXT | YES | Any additional notes or caveats |

---

## NOT_AVAILABLE Convention

When official information cannot be found from a verified government source:

- Use the literal string `NOT_AVAILABLE` in the field value
- Never leave a field blank if it was checked and found to be absent
- Add a note in `data_gaps` explaining what was searched and why it was not found

## Empty vs NOT_AVAILABLE

| Value | Meaning |
|-------|---------|
| Empty / NULL | Field not yet checked |
| `NOT_AVAILABLE` | Field was checked; information not found in official sources |
| Any other value | Information found and verified |
