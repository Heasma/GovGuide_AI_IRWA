"""
GovGuide AI — CSV Reader

Safely streams the Business Licenses CSV in configurable batches.
Does NOT load the entire file into memory at once.

Key guarantees:
- Source file is NEVER modified (read-only opens)
- All 37 expected columns are verified at startup
- Unexpected or missing columns are reported, not silently ignored
- Each row is returned as a plain dict with original CSV column names
"""

import csv
import logging
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Expected columns (all 37, in CSV order) ───────────────────────────────────
EXPECTED_COLUMNS: List[str] = [
    "ID",
    "LICENSE ID",
    "ACCOUNT NUMBER",
    "SITE NUMBER",
    "LEGAL NAME",
    "DOING BUSINESS AS NAME",
    "ADDRESS",
    "CITY",
    "STATE",
    "ZIP CODE",
    "WARD",
    "PRECINCT",
    "WARD PRECINCT",
    "POLICE DISTRICT",
    "COMMUNITY AREA",
    "COMMUNITY AREA NAME",
    "NEIGHBORHOOD",
    "LICENSE CODE",
    "LICENSE DESCRIPTION",
    "BUSINESS ACTIVITY ID",
    "BUSINESS ACTIVITY",
    "LICENSE NUMBER",
    "APPLICATION TYPE",
    "APPLICATION CREATED DATE",
    "APPLICATION REQUIREMENTS COMPLETE",
    "PAYMENT DATE",
    "CONDITIONAL APPROVAL",
    "LICENSE TERM START DATE",
    "LICENSE TERM EXPIRATION DATE",
    "LICENSE APPROVED FOR ISSUANCE",
    "DATE ISSUED",
    "LICENSE STATUS",
    "LICENSE STATUS CHANGE DATE",
    "SSA",
    "LATITUDE",
    "LONGITUDE",
    "LOCATION",
]


class ColumnMismatchError(Exception):
    """Raised when the CSV header does not match expected columns."""


class CSVColumnReport:
    """Result of column header validation."""

    def __init__(
        self,
        found: List[str],
        missing: List[str],
        unexpected: List[str],
    ) -> None:
        self.found = found
        self.missing = missing
        self.unexpected = unexpected
        self.is_valid = len(missing) == 0

    def __repr__(self) -> str:
        return (
            f"CSVColumnReport(found={len(self.found)}, "
            f"missing={self.missing}, unexpected={self.unexpected})"
        )


def validate_columns(csv_path: Path) -> CSVColumnReport:
    """
    Read only the header row of the CSV and compare against expected columns.

    Returns a CSVColumnReport with missing / unexpected column details.
    Raises ColumnMismatchError if any required columns are absent.
    """
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)

    found_set = set(header)
    expected_set = set(EXPECTED_COLUMNS)

    missing = [c for c in EXPECTED_COLUMNS if c not in found_set]
    unexpected = [c for c in header if c not in expected_set]

    report = CSVColumnReport(
        found=header,
        missing=missing,
        unexpected=unexpected,
    )

    if missing:
        raise ColumnMismatchError(
            f"CSV is missing required columns: {missing}"
        )

    if unexpected:
        logger.warning(
            "CSV contains unexpected columns (will be ignored): %s", unexpected
        )

    logger.info(
        "Column validation passed: %d columns found, %d unexpected (ignored).",
        len(header),
        len(unexpected),
    )
    return report


def stream_csv(
    csv_path: Path,
    batch_size: int = 500,
    max_rows: Optional[int] = None,
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Generator that yields batches of raw CSV rows as plain dicts.

    Args:
        csv_path:   Absolute path to the source CSV file.
        batch_size: Number of rows per batch (default: 500).
        max_rows:   If set, stop after this many rows (useful for dry-run).

    Yields:
        List[dict] — each dict has original CSV column names as keys
                     and raw string values (empty string for null/blank).

    Notes:
        - File is opened read-only; source is never modified.
        - LOCATION column is included in the dict but ingestion ignores it.
        - Memory usage is bounded by batch_size, not the full CSV size.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    total_yielded = 0
    batch: List[Dict[str, Any]] = []

    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if max_rows is not None and total_yielded >= max_rows:
                break
            batch.append(dict(row))
            total_yielded += 1
            if len(batch) >= batch_size:
                logger.debug("Yielding batch of %d rows (total so far: %d)", len(batch), total_yielded)
                yield batch
                batch = []

    if batch:
        logger.debug("Yielding final batch of %d rows (total: %d)", len(batch), total_yielded)
        yield batch

    logger.info("CSV streaming complete. Total rows streamed: %d", total_yielded)
