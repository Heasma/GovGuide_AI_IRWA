# GovGuide AI — Supplementary Data Validation Rules

**Date**: 2026-08-19  
**Phase**: 2 — Supplementary Data Design  
**Status**: DESIGN ONLY

---

## Overview

These validation rules apply to all supplementary government service records in:
- `data/supplementary/government_services_template.csv`
- Any future supplementary data collection
- Pydantic validators (to be implemented in Phase 3)

---

## Rule Set

### Rule 1: license_code is Present

**Field**: `license_code`  
**Condition**: Must be a non-empty string matching a value from `license_types.csv`  
**Error**: `MISSING_LICENSE_CODE`  
**Implementation**:
```python
assert len(str(record["license_code"]).strip()) > 0
assert record["license_code"] in valid_license_codes
```

---

### Rule 2: license_description is Present

**Field**: `license_description`  
**Condition**: Must be a non-empty string  
**Error**: `MISSING_LICENSE_DESCRIPTION`  
**Implementation**:
```python
assert len(str(record["license_description"]).strip()) > 0
```

---

### Rule 3: service_name is Present or Explicitly NOT_AVAILABLE

**Field**: `service_name`  
**Condition**: Must be either a non-empty string describing the citizen-facing service name,  
or the literal string `NOT_AVAILABLE`  
**Error**: `INVALID_SERVICE_NAME`  
**Forbidden values**: `""`, `None`, `NaN`, any blank string  
**Implementation**:
```python
assert record["service_name"] in {"NOT_AVAILABLE"} or \
       (isinstance(record["service_name"], str) and len(record["service_name"].strip()) > 0)
```

---

### Rule 4: official_url is a Valid HTTP/HTTPS URL When Present

**Field**: `official_url`  
**Condition**: If populated (not empty and not `NOT_AVAILABLE`), must begin with `http://` or `https://`  
and have a valid domain structure  
**Error**: `INVALID_OFFICIAL_URL`  
**Implementation**:
```python
import re
URL_RE = re.compile(r"^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+$")
if record["official_url"] not in ("", "NOT_AVAILABLE"):
    assert URL_RE.match(record["official_url"]), f"Invalid URL: {record['official_url']}"
```

---

### Rule 5: government_department is Present When Verified

**Field**: `government_department`  
**Condition**: When `source_confidence` is `VERIFIED` or `PARTIALLY_VERIFIED`,  
`government_department` must be a non-empty string (not `NOT_AVAILABLE`)  
**Error**: `MISSING_DEPARTMENT_FOR_VERIFIED_RECORD`  
**Implementation**:
```python
if record["source_confidence"] in ("VERIFIED", "PARTIALLY_VERIFIED"):
    assert record["government_department"] not in ("", "NOT_AVAILABLE", None)
```

---

### Rule 6: No Fabricated Values

**Field**: All fields  
**Condition**: Values must never be invented. If information is unavailable from official sources,
the field must contain `NOT_AVAILABLE`, not guessed content.  
**Error**: Cannot be automatically detected; enforced by data collection policy.  
**Policy**: All non-`NOT_AVAILABLE` values must have a `source_url` in `source_registry.csv`  
and a `source_verified_date`.

---

### Rule 7: source_url Must Correspond to an Official Government Domain

**Field**: `source_url` (in source_registry.csv) and `official_url`  
**Condition**: If populated, the URL domain must be in the approved official domain list  
**Error**: `UNOFFICIAL_SOURCE_DOMAIN`  
**Approved domains** (official government sources only):
```
chicago.gov
cityofchicago.org
chicityclerk.com
chicagocitytreasurer.com
illinois.gov
illinoisattorneygeneral.gov
cookcountyil.gov
municode.com  (for Chicago Municipal Code)
amlegal.com   (for Chicago Zoning Ordinance)
```
**Implementation**:
```python
APPROVED_DOMAINS = {
    "chicago.gov", "cityofchicago.org", "chicityclerk.com",
    "chicagocitytreasurer.com", "illinois.gov", "illinoisattorneygeneral.gov",
    "cookcountyil.gov", "municode.com", "amlegal.com"
}
from urllib.parse import urlparse
if url not in ("", "NOT_AVAILABLE"):
    domain = urlparse(url).netloc.lower().lstrip("www.")
    assert any(domain.endswith(d) for d in APPROVED_DOMAINS), \
           f"Unofficial source domain: {domain}"
```

---

### Rule 8: source_verified_date is Present for VERIFIED Sources

**Field**: `source_verified_date`  
**Condition**: When `source_confidence` is `VERIFIED`, `source_verified_date` must be  
a valid date string in `YYYY-MM-DD` format  
**Error**: `MISSING_VERIFIED_DATE`  
**Implementation**:
```python
from datetime import datetime
if record["source_confidence"] == "VERIFIED":
    assert record["source_verified_date"] not in ("", None)
    datetime.strptime(str(record["source_verified_date"]), "%Y-%m-%d")
```

---

### Rule 9: Duplicate license_code + source_url Combinations Are Rejected

**Field**: `license_code` + `source_url` composite  
**Condition**: No two records in the source registry may have the same (license_code, source_url) pair  
**Error**: `DUPLICATE_SOURCE_RECORD`  
**Implementation**:
```python
seen = set()
for record in source_records:
    key = (record["license_code"], record["source_url"])
    assert key not in seen, f"Duplicate source record: {key}"
    seen.add(key)
```

---

### Rule 10: Required Documents and Procedures Must Have Supporting Sources

**Field**: `required_documents`, `application_steps`  
**Condition**: If `required_documents` or `application_steps` is populated with anything other  
than `NOT_AVAILABLE`, the corresponding `official_url` must also be populated  
**Error**: `UNDOCUMENTED_REQUIRED_FIELD`  
**Implementation**:
```python
substantive = lambda v: v and v not in ("NOT_AVAILABLE", "")
if substantive(record["required_documents"]) or substantive(record["application_steps"]):
    assert substantive(record["official_url"]), \
           f"Required documents/steps present without official URL for license {record['license_code']}"
```

---

### Rule 11: Fees Must Have Supporting Sources

**Field**: `fee_amount`  
**Condition**: If `fee_amount` is populated with a dollar amount, `official_url` must also be populated  
**Error**: `UNDOCUMENTED_FEE`  
**Implementation**:
```python
if record["fee_amount"] and record["fee_amount"] != "NOT_AVAILABLE" and "$" in str(record["fee_amount"]):
    assert record["official_url"] and record["official_url"] != "NOT_AVAILABLE", \
           f"Fee present without official URL for license {record['license_code']}"
```

---

### Rule 12: Eligibility Claims Must Have Supporting Sources

**Field**: `eligibility_summary`, `eligibility_restrictions`  
**Condition**: If substantive eligibility information is present, `official_url` must also be present  
**Error**: `UNDOCUMENTED_ELIGIBILITY`  
**Implementation**:
```python
if record.get("eligibility_restrictions") not in ("NOT_AVAILABLE", "", None):
    assert record.get("official_url") not in ("NOT_AVAILABLE", "", None), \
           f"Eligibility present without official URL for license {record['license_code']}"
```

---

## Validation Implementation Reference

These rules are implemented in:

```
tests/unit/test_supplementary_validation.py
```

The test file runs all 12 rules against the generated template CSV.

---

## Source Quality Tiers

| Confidence Level | Meaning | Rules Applied |
|-----------------|---------|---------------|
| `VERIFIED` | Information confirmed from official chicago.gov, BACP, or Chicago Business Direct | Rules 1-12 |
| `PARTIALLY_VERIFIED` | Some information confirmed; some requires manual follow-up | Rules 1-9 |
| `REQUIRES_MANUAL_VERIFICATION` | No detailed information found; domain placeholder only | Rules 1-4, 7, 9 |
| `NOT_FOUND` | Officially confirmed as not available online | Rules 1-3, 9 |
