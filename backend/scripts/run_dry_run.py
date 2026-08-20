"""
GovGuide AI — Dry Run Ingestion Script

Processes the first 100 records of the Business Licenses CSV.
Validates, transforms, maps license codes — but does NOT commit to DB.

Usage:
    cd backend
    .venv/Scripts/python scripts/run_dry_run.py [--max-rows N]

Output:
    data/processed/dry_run_report.json
    data/processed/validation_report.json
"""

import json
import logging
import sys
import os
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.ingestion.csv_reader import validate_columns, stream_csv, EXPECTED_COLUMNS
from app.ingestion.validators import validate_batch, validate_row, KNOWN_LICENSE_CODES
from app.ingestion.transformers import transform_row
from app.ingestion.license_mapper import LicenseMapper, seed_government_data
from app.ingestion.loader import IngestionStats, load_batch, write_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("dry_run")

CSV_PATH = PROJECT_ROOT / "data" / "raw" / "Business_Licenses_-_Current_Active_20260819.csv"
DRY_RUN_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "dry_run_report.json"
VALIDATION_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "validation_report.json"


def run_dry_run(max_rows: int = 100, dry_run: bool = True) -> IngestionStats:
    settings = get_settings()
    db_url = settings.DATABASE_SYNC_URL
    logger.info("DB: %s (dry_run=%s, max_rows=%d)", db_url, dry_run, max_rows)

    # ── Step 1: Validate CSV columns ─────────────────────────────────────────
    logger.info("Step 1: Validating CSV columns...")
    col_report = validate_columns(CSV_PATH)
    logger.info("Column report: %s", col_report)

    # ── Step 2: Seed GovernmentOffice + GovernmentService (always commits) ─
    logger.info("Step 2: Seeding GovernmentOffice + GovernmentService...")
    bacp_id, service_map = seed_government_data(db_url)
    logger.info("BACP office_id=%s, mapped %d service codes", bacp_id, len(service_map))

    # ── Step 3: Load LicenseMapper from DB ───────────────────────────────────
    logger.info("Step 3: Loading LicenseMapper...")
    mapper = LicenseMapper(db_url)
    mapper.load()
    logger.info("Mapper loaded: %d service codes", mapper.total_mapped)

    # ── Step 4: Stream + validate + transform + load ──────────────────────────
    logger.info("Step 4: Processing first %d rows...", max_rows)
    stats = IngestionStats()
    seen_license_ids: Set[str] = set()
    holder_id_cache: Dict[Tuple[str, str], str] = {}
    all_validation_results = []

    batch_size = min(100, max_rows)
    row_offset = 0

    for raw_batch in stream_csv(CSV_PATH, batch_size=batch_size, max_rows=max_rows):
        # Validate
        val_results = validate_batch(raw_batch, row_offset, seen_license_ids=set())
        all_validation_results.extend(val_results)
        row_offset += len(raw_batch)

        # Build transformed + mapped batch
        batch_for_loader: List[Tuple[Dict[str, Any], Optional[str], List[str]]] = []

        for i, (raw_row, val_result) in enumerate(zip(raw_batch, val_results)):
            error_codes = [e.code for e in val_result.errors]

            # Count specific error types in stats
            for e in val_result.errors:
                if e.code == "DUPLICATE_LICENSE_ID":
                    pass  # counted in loader
                elif e.code.startswith("MISSING_"):
                    pass  # counted in loader
                elif "DATE" in e.code:
                    stats.date_errors += 1
                elif "COORDINATE" in e.code:
                    stats.coordinate_errors += 1
                elif "BOOLEAN" in e.code:
                    stats.boolean_errors += 1

            if error_codes:
                # Pass raw row through with errors — loader will skip DB write
                transformed = {k: raw_row.get(k, "") for k in EXPECTED_COLUMNS}
                batch_for_loader.append((transformed, None, error_codes))
                # Add to validation error sample
                if len(stats.validation_errors) < 50:
                    stats.validation_errors.append({
                        "row_index": val_result.row_index,
                        "license_id": val_result.license_id,
                        "raw_record_reference": val_result.raw_record_reference,
                        "errors": [
                            {"field": e.field, "code": e.code, "message": e.message}
                            for e in val_result.errors
                        ],
                    })
                continue

            # Transform
            try:
                transformed = transform_row(raw_row)
            except ValueError as exc:
                stats.transformation_errors += 1
                logger.warning("Transformation error at row %d: %s", val_result.row_index, exc)
                batch_for_loader.append(
                    ({k: raw_row.get(k, "") for k in EXPECTED_COLUMNS}, None, ["TRANSFORMATION_ERROR"])
                )
                continue

            # Map license code
            code = transformed.get("LICENSE CODE", "")
            service_id = mapper.get_service_id(code) if code else None

            batch_for_loader.append((transformed, service_id, []))

        # Load batch (dry_run=True → no commit)
        load_batch(
            batch_for_loader,
            db_url,
            holder_id_cache,
            seen_license_ids,
            stats,
            dry_run=dry_run,
        )

    # ── Step 5: Compile validation report ────────────────────────────────────
    total_rows = row_offset
    valid_count = sum(1 for vr in all_validation_results if vr.is_valid)
    invalid_count = total_rows - valid_count
    date_err_count = sum(
        1 for vr in all_validation_results
        for e in vr.errors if "DATE" in e.code
    )
    coord_err_count = sum(
        1 for vr in all_validation_results
        for e in vr.errors if "COORDINATE" in e.code
    )
    missing_count = sum(
        1 for vr in all_validation_results
        for e in vr.errors if e.code.startswith("MISSING_")
    )
    dup_count = sum(
        1 for vr in all_validation_results
        for e in vr.errors if e.code == "DUPLICATE_LICENSE_ID"
    )
    invalid_code_count = sum(
        1 for vr in all_validation_results
        for e in vr.errors if e.code == "INVALID_LICENSE_CODE"
    )

    validation_report = {
        "total_rows": total_rows,
        "valid_rows": valid_count,
        "invalid_rows": invalid_count,
        "duplicate_rows": dup_count,
        "missing_required_values": missing_count,
        "invalid_license_codes": invalid_code_count,
        "date_errors": date_err_count,
        "coordinate_errors": coord_err_count,
        "column_report": {
            "found_count": len(col_report.found),
            "missing_columns": col_report.missing,
            "unexpected_columns": col_report.unexpected,
        },
    }

    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VALIDATION_REPORT_PATH, "w") as fh:
        json.dump(validation_report, fh, indent=2)
    logger.info("Validation report: %s", VALIDATION_REPORT_PATH)

    # ── Step 6: Write dry run report ─────────────────────────────────────────
    dry_run_report = {
        "mode": "DRY_RUN" if dry_run else "LIVE",
        "max_rows_requested": max_rows,
        **stats.to_dict(),
        "license_mapper": {
            "total_mapped_codes": mapper.total_mapped,
            "mapped_codes": sorted(mapper.mapped_codes),
        },
        "column_validation": {
            "passed": col_report.is_valid,
            "found_count": len(col_report.found),
            "missing": col_report.missing,
            "unexpected": col_report.unexpected,
        },
    }

    write_report(stats, DRY_RUN_REPORT_PATH)
    # Overwrite with the more detailed version
    with open(DRY_RUN_REPORT_PATH, "w") as fh:
        json.dump(dry_run_report, fh, indent=2, default=str)
    logger.info("Dry run report: %s", DRY_RUN_REPORT_PATH)

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GovGuide AI — Dry Run Ingestion")
    parser.add_argument("--max-rows", type=int, default=100, help="Max rows to process")
    parser.add_argument("--live", action="store_true", help="Run in LIVE mode (commits to DB)")
    args = parser.parse_args()

    result = run_dry_run(max_rows=args.max_rows, dry_run=not args.live)
    print("\n=== DRY RUN SUMMARY ===")
    print(json.dumps(result.to_dict(), indent=2, default=str))
