"""
GovGuide AI — Ingestion Loader

Writes validated + transformed BusinessLicenseHolder and BusinessLicense
records to PostgreSQL.

Key properties:
- Batch processing: commits one batch at a time; a batch failure rolls back
  only that batch, not prior successfully committed batches.
- Duplicate protection: upserts holders on (account_number, site_number);
  skips licenses with duplicate license_id.
- Foreign-key safety: holders are upserted before licenses in every batch.
- Dry-run support: when dry_run=True, all processing happens but
  db.commit() is never called. Useful for validation without side effects.

Phase 3 constraint:
    Only the first 100 records are loaded during the dry run.
    Full production ingestion is a Phase 4 activity.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import psycopg2
import psycopg2.extras
from psycopg2.errors import UniqueViolation

logger = logging.getLogger(__name__)


# ── Ingestion statistics ─────────────────────────────────────────────────────

@dataclass
class IngestionStats:
    total_processed: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    unmapped_license_codes: int = 0
    missing_required_fields: int = 0
    date_errors: int = 0
    coordinate_errors: int = 0
    boolean_errors: int = 0
    transformation_errors: int = 0
    holders_created: int = 0
    holders_updated: int = 0
    licenses_created: int = 0
    licenses_skipped: int = 0
    validation_errors: List[Dict[str, Any]] = field(default_factory=list)
    unmapped_codes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_processed": self.total_processed,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "duplicate_records": self.duplicate_records,
            "unmapped_license_codes": self.unmapped_license_codes,
            "missing_required_fields": self.missing_required_fields,
            "date_errors": self.date_errors,
            "coordinate_errors": self.coordinate_errors,
            "boolean_errors": self.boolean_errors,
            "transformation_errors": self.transformation_errors,
            "holders_created": self.holders_created,
            "holders_updated": self.holders_updated,
            "licenses_created": self.licenses_created,
            "licenses_skipped": self.licenses_skipped,
            "validation_error_sample": self.validation_errors[:50],
            "unmapped_license_code_list": list(set(self.unmapped_codes)),
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _date_to_str(d: Optional[date]) -> Optional[str]:
    """Convert date to ISO string for JSON reporting."""
    return d.isoformat() if d else None


def _upsert_holder(
    cur,
    transformed: Dict[str, Any],
    holder_id_cache: Dict[Tuple[str, str], str],
    stats: IngestionStats,
) -> str:
    """
    Upsert a BusinessLicenseHolder record.

    Deduplication key: (account_number, site_number).

    Returns:
        holder_id (UUID string)
    """
    acct = transformed["ACCOUNT NUMBER"]
    site = transformed["SITE NUMBER"]
    cache_key = (acct, site)

    if cache_key in holder_id_cache:
        return holder_id_cache[cache_key]

    # Check DB for existing holder
    cur.execute(
        "SELECT id::text FROM business_license_holders "
        "WHERE account_number = %s AND site_number = %s LIMIT 1",
        (acct, site)
    )
    row = cur.fetchone()

    if row:
        holder_id = row[0]
        # Update with latest data (e.g., new address or geography)
        cur.execute(
            """
            UPDATE business_license_holders SET
                legal_name              = %s,
                doing_business_as_name  = %s,
                address                 = %s,
                city                    = %s,
                state                   = %s,
                zip_code                = %s,
                ward                    = %s,
                precinct                = %s,
                ward_precinct           = %s,
                police_district         = %s,
                community_area          = %s,
                community_area_name     = %s,
                neighborhood            = %s,
                latitude                = %s,
                longitude               = %s
            WHERE id = %s::uuid
            """,
            (
                transformed["LEGAL NAME"],
                transformed["DOING BUSINESS AS NAME"],
                transformed["ADDRESS"],
                transformed["CITY"],
                transformed["STATE"],
                transformed["ZIP CODE"],
                transformed["WARD"],
                transformed["PRECINCT"],
                transformed["WARD PRECINCT"],
                transformed["POLICE DISTRICT"],
                transformed["COMMUNITY AREA"],
                transformed["COMMUNITY AREA NAME"],
                transformed["NEIGHBORHOOD"],
                transformed["LATITUDE"],
                transformed["LONGITUDE"],
                holder_id,
            )
        )
        stats.holders_updated += 1
    else:
        holder_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO business_license_holders
                (id, account_number, site_number, legal_name, doing_business_as_name,
                 address, city, state, zip_code,
                 ward, precinct, ward_precinct, police_district,
                 community_area, community_area_name, neighborhood,
                 latitude, longitude, raw_metadata)
            VALUES
                (%s::uuid, %s, %s, %s, %s,
                 %s, %s, %s, %s,
                 %s, %s, %s, %s,
                 %s, %s, %s,
                 %s, %s, '{}'::jsonb)
            """,
            (
                holder_id,
                acct, site,
                transformed["LEGAL NAME"],
                transformed["DOING BUSINESS AS NAME"],
                transformed["ADDRESS"],
                transformed["CITY"],
                transformed["STATE"],
                transformed["ZIP CODE"],
                transformed["WARD"],
                transformed["PRECINCT"],
                transformed["WARD PRECINCT"],
                transformed["POLICE DISTRICT"],
                transformed["COMMUNITY AREA"],
                transformed["COMMUNITY AREA NAME"],
                transformed["NEIGHBORHOOD"],
                transformed["LATITUDE"],
                transformed["LONGITUDE"],
            )
        )
        stats.holders_created += 1

    holder_id_cache[cache_key] = holder_id
    return holder_id


def _insert_license(
    cur,
    transformed: Dict[str, Any],
    holder_id: str,
    service_id: Optional[str],
    seen_license_ids: Set[str],
    stats: IngestionStats,
) -> bool:
    """
    Insert a BusinessLicense record.

    Returns True if inserted, False if skipped (duplicate).
    """
    lid = transformed["LICENSE ID"]

    if lid in seen_license_ids:
        stats.duplicate_records += 1
        stats.licenses_skipped += 1
        return False

    try:
        cur.execute(
            """
            INSERT INTO business_licenses
                (id, license_id, license_number, license_code, license_description,
                 business_activity_id, business_activity,
                 application_type, application_created_date,
                 application_requirements_complete, payment_date,
                 conditional_approval, license_term_start_date,
                 license_term_expiration_date, license_approved_for_issuance,
                 date_issued, license_status, license_status_change_date,
                 ssa, raw_record_reference, holder_id, government_service_id)
            VALUES
                (%s::uuid, %s, %s, %s, %s,
                 %s, %s,
                 %s, %s,
                 %s, %s,
                 %s, %s,
                 %s, %s,
                 %s, %s, %s,
                 %s, %s, %s::uuid, %s)
            """,
            (
                str(uuid.uuid4()),
                lid,
                transformed["LICENSE NUMBER"],
                transformed["LICENSE CODE"],
                transformed["LICENSE DESCRIPTION"],
                transformed["BUSINESS ACTIVITY ID"],
                transformed["BUSINESS ACTIVITY"],
                transformed["APPLICATION TYPE"],
                transformed["APPLICATION CREATED DATE"],
                transformed["APPLICATION REQUIREMENTS COMPLETE"],
                transformed["PAYMENT DATE"],
                transformed["CONDITIONAL APPROVAL"],
                transformed["LICENSE TERM START DATE"],
                transformed["LICENSE TERM EXPIRATION DATE"],
                transformed["LICENSE APPROVED FOR ISSUANCE"],
                transformed["DATE ISSUED"],
                transformed["LICENSE STATUS"],
                transformed["LICENSE STATUS CHANGE DATE"],
                transformed["SSA"],
                transformed["ID"],
                holder_id,
                service_id,
            )
        )
        seen_license_ids.add(lid)
        stats.licenses_created += 1
        return True

    except UniqueViolation:
        # Race condition or pre-existing record — skip gracefully
        stats.duplicate_records += 1
        stats.licenses_skipped += 1
        return False


# ── Main loader ───────────────────────────────────────────────────────────────

def load_batch(
    batch_transformed: List[Tuple[Dict[str, Any], Optional[str], List[str]]],
    db_url: str,
    holder_id_cache: Dict[Tuple[str, str], str],
    seen_license_ids: Set[str],
    stats: IngestionStats,
    dry_run: bool = True,
) -> None:
    """
    Load one batch of transformed + mapped rows into the database.

    Args:
        batch_transformed: List of (transformed_row, service_id_or_None, error_codes).
        db_url:            PostgreSQL sync connection string.
        holder_id_cache:   Cross-batch cache of (account_number, site_number) → holder_id.
        seen_license_ids:  Cross-batch set of seen LICENSE IDs.
        stats:             Mutable statistics object (updated in place).
        dry_run:           If True, all logic runs but conn.commit() is NOT called.
    """
    conn = psycopg2.connect(db_url)
    conn.autocommit = False

    try:
        cur = conn.cursor()

        for transformed, service_id, error_codes in batch_transformed:
            stats.total_processed += 1

            if error_codes:
                # Row had validation/transformation errors — count but skip DB write
                stats.invalid_records += 1
                if any(c.startswith("MISSING_") for c in error_codes):
                    stats.missing_required_fields += 1
                if any(c == "DUPLICATE_LICENSE_ID" for c in error_codes):
                    stats.duplicate_records += 1
                continue

            # Track unmapped license codes
            license_code = transformed.get("LICENSE CODE", "")
            if service_id is None and license_code:
                stats.unmapped_license_codes += 1
                stats.unmapped_codes.append(license_code)

            # Upsert holder
            holder_id = _upsert_holder(cur, transformed, holder_id_cache, stats)

            # Insert license
            _insert_license(cur, transformed, holder_id, service_id, seen_license_ids, stats)
            stats.valid_records += 1

        if dry_run:
            logger.info("DRY RUN: rolling back batch of %d rows.", len(batch_transformed))
            conn.rollback()
        else:
            conn.commit()
            logger.debug("Committed batch of %d rows.", len(batch_transformed))

    except Exception as exc:
        conn.rollback()
        logger.error("Batch failed and rolled back: %s", exc)
        raise
    finally:
        conn.close()


def write_report(stats: IngestionStats, report_path: Path) -> None:
    """Write the ingestion stats to a JSON report file."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(stats.to_dict(), fh, indent=2, default=str)
    logger.info("Report written to %s", report_path)
