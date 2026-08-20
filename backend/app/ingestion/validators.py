"""
GovGuide AI — Row Validators

Validates each raw CSV row dict (string values) against business rules.
Invalid records are NEVER silently discarded — they are flagged in the
ValidationResult and preserved in the validation report.

Validation does NOT mutate input values. Type coercion is delegated to
transformers.py.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

# All 56 known LICENSE CODEs from the dataset
KNOWN_LICENSE_CODES: Set[str] = {
    "1003", "1006", "1007", "1009", "1010", "1023", "1032", "1039",
    "1050", "1056", "1070", "1075", "1082", "1253", "1275", "1329",
    "1470", "1471", "1472", "1473", "1474", "1475", "1476", "1477",
    "1480", "1481", "1594", "1625", "1683", "1781", "2101", "3717",
    "4404", "4405", "4406", "4408", "4409", "7002", "7003", "7006",
    "7008", "7009", "7013", "7020", "7029", "7030", "7032", "7034",
    "7035", "7036", "8340", "8342", "8343", "8344", "8345", "8604",
}

KNOWN_APPLICATION_TYPES: Set[str] = {
    "RENEW", "ISSUE", "C_LOC", "C_SBA", "C_CAPA", "C_EXPA",
}

KNOWN_LICENSE_STATUSES: Set[str] = {"AAI"}

DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")

# ── Validation result ────────────────────────────────────────────────────────

@dataclass
class ValidationError:
    """A single validation failure on one field."""
    field: str
    code: str     # e.g. MISSING_REQUIRED, INVALID_DATE, INVALID_LICENSE_CODE
    raw_value: Any
    message: str


@dataclass
class ValidationResult:
    """
    Aggregated result of validating one CSV row.

    is_valid is True only if there are zero errors.
    Warnings do not affect is_valid — they are informational.
    """
    row_index: int                        # 0-based index in the CSV
    raw_record_reference: str             # CSV 'ID' column
    license_id: str                       # CSV 'LICENSE ID' column
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, field_name: str, code: str, raw: Any, msg: str) -> None:
        self.errors.append(ValidationError(
            field=field_name, code=code, raw_value=raw, message=msg
        ))

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# ── Helper functions ─────────────────────────────────────────────────────────

def _is_blank(value: str) -> bool:
    return not value or not value.strip()


def _validate_required(result: ValidationResult, row: Dict[str, str], field_name: str, error_code: str) -> bool:
    """Check that a field is present and non-blank. Returns True if valid."""
    val = row.get(field_name, "")
    if _is_blank(val):
        result.add_error(field_name, error_code, val, f"{field_name} is required but missing or blank")
        return False
    return True


def _validate_date_optional(result: ValidationResult, row: Dict[str, str], field_name: str) -> None:
    """If a date field is non-blank, verify it matches MM/DD/YYYY format."""
    val = row.get(field_name, "")
    if _is_blank(val):
        return  # null is acceptable for optional date fields
    if not DATE_PATTERN.match(val.strip()):
        result.add_error(
            field_name,
            "INVALID_DATE",
            val,
            f"{field_name} has invalid date format '{val}'. Expected MM/DD/YYYY.",
        )


def _validate_float_optional(
    result: ValidationResult,
    row: Dict[str, str],
    field_name: str,
    min_val: float,
    max_val: float,
) -> None:
    """If a float field is non-blank, verify it's a valid float in range."""
    val = row.get(field_name, "")
    if _is_blank(val):
        return
    try:
        f = float(val.strip())
        if not (min_val <= f <= max_val):
            result.add_error(
                field_name,
                "INVALID_COORDINATE",
                val,
                f"{field_name}={val} is out of valid range [{min_val}, {max_val}]",
            )
    except ValueError:
        result.add_error(
            field_name,
            "INVALID_COORDINATE",
            val,
            f"{field_name}='{val}' cannot be parsed as a float",
        )


def _validate_integer_optional(
    result: ValidationResult,
    row: Dict[str, str],
    field_name: str,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
) -> None:
    """If an integer field is non-blank, verify it's a valid integer (optionally in range)."""
    val = row.get(field_name, "")
    if _is_blank(val):
        return
    try:
        i = int(val.strip())
        if min_val is not None and i < min_val:
            result.add_error(
                field_name, "INVALID_INTEGER_RANGE", val,
                f"{field_name}={i} is below minimum {min_val}",
            )
        if max_val is not None and i > max_val:
            result.add_error(
                field_name, "INVALID_INTEGER_RANGE", val,
                f"{field_name}={i} is above maximum {max_val}",
            )
    except ValueError:
        result.add_error(
            field_name, "INVALID_INTEGER", val,
            f"{field_name}='{val}' cannot be parsed as an integer",
        )


# ── Main validator ────────────────────────────────────────────────────────────

def validate_row(row: Dict[str, str], row_index: int) -> ValidationResult:
    """
    Validate a single raw CSV row dict.

    Args:
        row:       Dict from csv.DictReader — all values are strings.
        row_index: 0-based row index in the CSV (for reporting).

    Returns:
        ValidationResult with all errors and warnings collected.
        A row is considered valid only if ValidationResult.is_valid is True.
    """
    result = ValidationResult(
        row_index=row_index,
        raw_record_reference=row.get("ID", ""),
        license_id=row.get("LICENSE ID", ""),
    )

    # ── Required identifier fields ─────────────────────────────────────────
    _validate_required(result, row, "LICENSE ID",          "MISSING_LICENSE_ID")
    _validate_required(result, row, "LICENSE NUMBER",      "MISSING_LICENSE_NUMBER")
    _validate_required(result, row, "LICENSE CODE",        "MISSING_LICENSE_CODE")
    _validate_required(result, row, "LICENSE DESCRIPTION", "MISSING_LICENSE_DESCRIPTION")
    _validate_required(result, row, "ACCOUNT NUMBER",      "MISSING_ACCOUNT_NUMBER")
    _validate_required(result, row, "SITE NUMBER",         "MISSING_SITE_NUMBER")
    _validate_required(result, row, "LEGAL NAME",          "MISSING_LEGAL_NAME")

    # ── License code validation ────────────────────────────────────────────
    license_code = row.get("LICENSE CODE", "").strip()
    if license_code and license_code not in KNOWN_LICENSE_CODES:
        result.add_error(
            "LICENSE CODE",
            "INVALID_LICENSE_CODE",
            license_code,
            f"LICENSE CODE '{license_code}' is not in the known 56 codes",
        )

    # ── License status validation ──────────────────────────────────────────
    status = row.get("LICENSE STATUS", "").strip()
    if status and status not in KNOWN_LICENSE_STATUSES:
        result.add_warning(
            f"Unexpected LICENSE STATUS '{status}'. Known values: {KNOWN_LICENSE_STATUSES}"
        )

    # ── Application type validation ────────────────────────────────────────
    app_type = row.get("APPLICATION TYPE", "").strip()
    if app_type and app_type not in KNOWN_APPLICATION_TYPES:
        result.add_warning(
            f"Unexpected APPLICATION TYPE '{app_type}'. Known values: {KNOWN_APPLICATION_TYPES}"
        )

    # ── Conditional approval validation ───────────────────────────────────
    cond_approval = row.get("CONDITIONAL APPROVAL", "").strip()
    if cond_approval not in ("Y", "N"):
        result.add_error(
            "CONDITIONAL APPROVAL",
            "INVALID_BOOLEAN",
            cond_approval,
            f"CONDITIONAL APPROVAL must be 'Y' or 'N', got '{cond_approval}'",
        )

    # ── Date field validation ─────────────────────────────────────────────
    date_fields = [
        "APPLICATION CREATED DATE",
        "APPLICATION REQUIREMENTS COMPLETE",
        "PAYMENT DATE",
        "LICENSE TERM START DATE",
        "LICENSE TERM EXPIRATION DATE",
        "LICENSE APPROVED FOR ISSUANCE",
        "DATE ISSUED",
        "LICENSE STATUS CHANGE DATE",
    ]
    for df in date_fields:
        _validate_date_optional(result, row, df)

    # ── Coordinate validation ─────────────────────────────────────────────
    _validate_float_optional(result, row, "LATITUDE",  -90.0,  90.0)
    _validate_float_optional(result, row, "LONGITUDE", -180.0, 180.0)

    # ── Integer field validation ──────────────────────────────────────────
    _validate_integer_optional(result, row, "WARD",            min_val=1, max_val=50)
    _validate_integer_optional(result, row, "PRECINCT",        min_val=1)
    _validate_integer_optional(result, row, "POLICE DISTRICT", min_val=1)
    _validate_integer_optional(result, row, "COMMUNITY AREA",  min_val=0, max_val=77)

    return result


def validate_batch(
    rows: List[Dict[str, str]],
    start_index: int,
    seen_license_ids: Set[str],
) -> List[ValidationResult]:
    """
    Validate a batch of rows and track duplicate LICENSE IDs across batches.

    Args:
        rows:             List of raw CSV row dicts.
        start_index:      Row index of the first row in this batch (for reporting).
        seen_license_ids: Set of already-seen LICENSE IDs (mutated in place).

    Returns:
        List of ValidationResult, one per row.
    """
    results: List[ValidationResult] = []

    for i, row in enumerate(rows):
        vr = validate_row(row, start_index + i)

        # Duplicate license_id detection
        lid = row.get("LICENSE ID", "").strip()
        if lid:
            if lid in seen_license_ids:
                vr.add_error(
                    "LICENSE ID",
                    "DUPLICATE_LICENSE_ID",
                    lid,
                    f"LICENSE ID '{lid}' has already been seen in this ingestion run",
                )
            else:
                seen_license_ids.add(lid)

        results.append(vr)

    return results
