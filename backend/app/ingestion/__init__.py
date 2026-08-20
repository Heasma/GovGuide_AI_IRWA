"""
GovGuide AI — CSV Ingestion Pipeline

Architecture:
    CSV
     ↓
    csv_reader.py    — stream-reads CSV in configurable batches
     ↓
    validators.py    — validates each raw row; produces ValidationResult
     ↓
    transformers.py  — coerces types (dates, floats, ints, booleans)
     ↓
    license_mapper.py — maps LICENSE CODE → GovernmentService.id
     ↓
    loader.py        — upserts BusinessLicenseHolder + BusinessLicense
     ↓
    PostgreSQL (govguide_db)

Phase 3 Constraint:
    - Dry-run mode: validate + transform + map but do NOT call db.commit()
    - Full ingestion: run after Phase 3 dry-run validation is confirmed
"""
