"""
GovGuide AI — Full Dataset Ingestion Script

Performs full production ingestion of the Business Licenses CSV dataset
into PostgreSQL (govguide_db).

Features:
- Stream-reads CSV in configurable batches (default: 1000 rows)
- Validates and transforms every row
- Upserts BusinessLicenseHolder on (account_number, site_number)
- Inserts BusinessLicense on license_id (duplicate protection)
- Maps LICENSE CODE to GovernmentService
- Writes full ingestion report to data/processed/full_ingestion_report.json
"""

import json
import logging
import sys
import time
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add backend and project root to path
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.ingestion.csv_reader import validate_columns, stream_csv, EXPECTED_COLUMNS
from app.ingestion.validators import validate_batch
from app.ingestion.transformers import transform_row
from app.ingestion.license_mapper import LicenseMapper, seed_government_data
from app.ingestion.loader import IngestionStats, load_batch, write_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("full_ingestion")

CSV_PATH = PROJECT_ROOT / "data" / "raw" / "Business_Licenses_-_Current_Active_20260819.csv"
FULL_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "full_ingestion_report.json"
VALIDATION_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "validation_report.json"


def run_full_ingestion(batch_size: int = 1000, max_rows: Optional[int] = None) -> IngestionStats:
    start_time = time.time()
    settings = get_settings()
    db_url = settings.DATABASE_SYNC_URL
    logger.info("Database URL: %s", db_url)
    logger.info("Starting full ingestion from: %s", CSV_PATH)

    # 1. Validate CSV header
    logger.info("Step 1: Validating CSV column schema...")
    col_report = validate_columns(CSV_PATH)
    logger.info("Column validation passed (37 columns confirmed).")

    # 2. Seed GovernmentOffice and GovernmentServices (BACP & 56 license services)
    logger.info("Step 2: Ensuring GovernmentOffice and GovernmentService records are seeded...")
    bacp_id, service_map = seed_government_data(db_url)
    logger.info("Seeded BACP office ID: %s (%d service categories)", bacp_id, len(service_map))

    # 3. Load mapper
    logger.info("Step 3: Loading LicenseMapper...")
    mapper = LicenseMapper(db_url)
    mapper.load()
    logger.info("LicenseMapper loaded %d service codes.", mapper.total_mapped)

    # 4. Stream & Load
    logger.info("Step 4: Beginning batch ingestion (batch_size=%d)...", batch_size)
    stats = IngestionStats()
    seen_license_ids: Set[str] = set()
    holder_id_cache: Dict[Tuple[str, str], str] = {}
    row_offset = 0

    for raw_batch in stream_csv(CSV_PATH, batch_size=batch_size, max_rows=max_rows):
        val_results = validate_batch(raw_batch, row_offset, seen_license_ids=set())
        row_offset += len(raw_batch)

        batch_for_loader: List[Tuple[Dict[str, Any], Optional[str], List[str]]] = []

        for raw_row, val_result in zip(raw_batch, val_results):
            error_codes = [e.code for e in val_result.errors]

            for e in val_result.errors:
                if "DATE" in e.code:
                    stats.date_errors += 1
                elif "COORDINATE" in e.code:
                    stats.coordinate_errors += 1
                elif "BOOLEAN" in e.code:
                    stats.boolean_errors += 1

            if error_codes:
                transformed = {k: raw_row.get(k, "") for k in EXPECTED_COLUMNS}
                batch_for_loader.append((transformed, None, error_codes))
                if len(stats.validation_errors) < 50:
                    stats.validation_errors.append({
                        "row_index": val_result.row_index,
                        "license_id": val_result.license_id,
                        "raw_record_reference": val_result.raw_record_reference,
                        "errors": [{"field": e.field, "code": e.code, "message": e.message} for e in val_result.errors],
                    })
                continue

            try:
                transformed = transform_row(raw_row)
            except ValueError as exc:
                stats.transformation_errors += 1
                batch_for_loader.append(({k: raw_row.get(k, "") for k in EXPECTED_COLUMNS}, None, ["TRANSFORMATION_ERROR"]))
                continue

            code = transformed.get("LICENSE CODE", "")
            service_id = mapper.get_service_id(code) if code else None

            batch_for_loader.append((transformed, service_id, []))

        # Commit batch to database (live)
        load_batch(
            batch_for_loader,
            db_url,
            holder_id_cache,
            seen_license_ids,
            stats,
            dry_run=False,
        )

        if row_offset % 5000 == 0 or (max_rows and row_offset >= max_rows):
            elapsed = time.time() - start_time
            rate = row_offset / elapsed if elapsed > 0 else 0
            logger.info(
                "Progress: %d rows processed | Holders: %d | Licenses: %d | %.1f rows/sec",
                row_offset,
                stats.holders_created,
                stats.licenses_created,
                rate,
            )

    elapsed = time.time() - start_time
    logger.info(
        "Ingestion completed in %.2f seconds (%d total rows processed).",
        elapsed,
        stats.total_processed,
    )

    # 5. Write reports
    final_report = {
        "mode": "FULL_INGESTION",
        "elapsed_seconds": round(elapsed, 2),
        "total_source_rows": stats.total_processed,
        "valid_records": stats.valid_records,
        "invalid_records": stats.invalid_records,
        "duplicate_records": stats.duplicate_records,
        "unmapped_license_codes": stats.unmapped_license_codes,
        "holders_created": stats.holders_created,
        "holders_updated": stats.holders_updated,
        "licenses_created": stats.licenses_created,
        "licenses_skipped": stats.licenses_skipped,
        "date_errors": stats.date_errors,
        "coordinate_errors": stats.coordinate_errors,
        "boolean_errors": stats.boolean_errors,
        "transformation_errors": stats.transformation_errors,
        "database_summary": {
            "business_license_holders": stats.holders_created,
            "business_licenses": stats.licenses_created,
            "government_services": mapper.total_mapped,
        },
    }

    FULL_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FULL_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)
    logger.info("Full ingestion report saved to: %s", FULL_REPORT_PATH)

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GovGuide AI — Full Ingestion")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size (default: 1000)")
    parser.add_argument("--max-rows", type=int, default=None, help="Optional max rows")
    args = parser.parse_args()

    result = run_full_ingestion(batch_size=args.batch_size, max_rows=args.max_rows)
    print("\n=== FULL INGESTION SUMMARY ===")
    print(json.dumps(result.to_dict(), indent=2, default=str))
