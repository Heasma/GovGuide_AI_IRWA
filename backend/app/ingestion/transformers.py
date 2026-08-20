"""
GovGuide AI — Data Transformers

Coerces raw CSV string values into Python-native types suitable for
SQLAlchemy model attributes.

Rules:
- Raw values are NEVER modified — transformers return new objects.
- Empty string and whitespace-only values → None for nullable fields.
- Transformation errors raise ValueError with a descriptive message.
- Callers (loader.py) catch ValueError and log the issue as a
  transformation error, not a validation error.
"""

import logging
from datetime import datetime, date
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Date transformation ───────────────────────────────────────────────────────

_DATE_FORMAT = "%m/%d/%Y"


def parse_date(raw: str, field_name: str = "") -> Optional[date]:
    """
    Parse a date from MM/DD/YYYY format.

    Args:
        raw:        Raw CSV string value.
        field_name: Column name for error messages.

    Returns:
        datetime.date or None if the field is blank.

    Raises:
        ValueError: If the value is non-blank but does not match MM/DD/YYYY.
    """
    if not raw or not raw.strip():
        return None
    try:
        return datetime.strptime(raw.strip(), _DATE_FORMAT).date()
    except ValueError:
        raise ValueError(
            f"Field '{field_name}': cannot parse date '{raw}'. "
            f"Expected format MM/DD/YYYY."
        )


# ── Boolean transformation ────────────────────────────────────────────────────

def parse_bool_yn(raw: str, field_name: str = "") -> bool:
    """
    Parse Y/N boolean encoding.

    Args:
        raw:        Raw CSV string value ('Y' or 'N').
        field_name: Column name for error messages.

    Returns:
        True for 'Y', False for 'N'.

    Raises:
        ValueError: If value is not 'Y' or 'N'.
    """
    stripped = (raw or "").strip().upper()
    if stripped == "Y":
        return True
    if stripped == "N":
        return False
    raise ValueError(
        f"Field '{field_name}': expected 'Y' or 'N', got '{raw}'."
    )


# ── Numeric transformations ───────────────────────────────────────────────────

def parse_float_optional(raw: str, field_name: str = "") -> Optional[float]:
    """
    Parse a float from a string. Returns None for blank values.

    Raises:
        ValueError: If value is non-blank but cannot be parsed as float.
    """
    if not raw or not raw.strip():
        return None
    try:
        return float(raw.strip())
    except ValueError:
        raise ValueError(
            f"Field '{field_name}': cannot parse float '{raw}'."
        )


def parse_int_optional(raw: str, field_name: str = "") -> Optional[int]:
    """
    Parse an integer from a string. Returns None for blank values.

    Raises:
        ValueError: If value is non-blank but cannot be parsed as integer.
    """
    if not raw or not raw.strip():
        return None
    try:
        # Handle floats encoded as strings (e.g., "3.0") by truncating
        return int(float(raw.strip()))
    except ValueError:
        raise ValueError(
            f"Field '{field_name}': cannot parse integer '{raw}'."
        )


def parse_str_optional(raw: str) -> Optional[str]:
    """Return the stripped string, or None if blank."""
    if not raw:
        return None
    stripped = raw.strip()
    return stripped if stripped else None


# ── Full row transformation ───────────────────────────────────────────────────

def transform_row(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Transform a validated raw CSV row dict into Python-native types.

    Args:
        row: Raw CSV row dict (all values are strings).

    Returns:
        Dict with the same keys but typed Python values.
        Keys use the original CSV column names.

    Raises:
        ValueError: If a non-nullable field cannot be parsed (e.g., bad date).
                    Callers should catch and log; row should be marked invalid.
    """
    transformed: Dict[str, Any] = {}

    # ── Pass-through strings (required / identity fields) ─────────────────
    transformed["ID"]                  = row.get("ID", "").strip() or None
    transformed["LICENSE ID"]          = row.get("LICENSE ID", "").strip()
    transformed["ACCOUNT NUMBER"]      = row.get("ACCOUNT NUMBER", "").strip()
    transformed["SITE NUMBER"]         = row.get("SITE NUMBER", "").strip()
    transformed["LEGAL NAME"]          = row.get("LEGAL NAME", "").strip()
    transformed["LICENSE CODE"]        = row.get("LICENSE CODE", "").strip()
    transformed["LICENSE DESCRIPTION"] = row.get("LICENSE DESCRIPTION", "").strip()
    transformed["LICENSE NUMBER"]      = row.get("LICENSE NUMBER", "").strip()
    transformed["LICENSE STATUS"]      = row.get("LICENSE STATUS", "").strip()

    # ── Optional strings ──────────────────────────────────────────────────
    transformed["DOING BUSINESS AS NAME"]   = parse_str_optional(row.get("DOING BUSINESS AS NAME", ""))
    transformed["ADDRESS"]                  = parse_str_optional(row.get("ADDRESS", ""))
    transformed["CITY"]                     = parse_str_optional(row.get("CITY", ""))
    transformed["STATE"]                    = parse_str_optional(row.get("STATE", ""))
    transformed["ZIP CODE"]                 = parse_str_optional(row.get("ZIP CODE", ""))
    transformed["WARD PRECINCT"]            = parse_str_optional(row.get("WARD PRECINCT", ""))
    transformed["COMMUNITY AREA NAME"]      = parse_str_optional(row.get("COMMUNITY AREA NAME", ""))
    transformed["NEIGHBORHOOD"]             = parse_str_optional(row.get("NEIGHBORHOOD", ""))
    transformed["BUSINESS ACTIVITY ID"]     = parse_str_optional(row.get("BUSINESS ACTIVITY ID", ""))
    transformed["BUSINESS ACTIVITY"]        = parse_str_optional(row.get("BUSINESS ACTIVITY", ""))
    transformed["APPLICATION TYPE"]         = parse_str_optional(row.get("APPLICATION TYPE", ""))
    transformed["SSA"]                      = parse_str_optional(row.get("SSA", ""))

    # ── Integers ──────────────────────────────────────────────────────────
    transformed["WARD"]            = parse_int_optional(row.get("WARD", ""),            "WARD")
    transformed["PRECINCT"]        = parse_int_optional(row.get("PRECINCT", ""),        "PRECINCT")
    transformed["POLICE DISTRICT"] = parse_int_optional(row.get("POLICE DISTRICT", ""), "POLICE DISTRICT")
    transformed["COMMUNITY AREA"]  = parse_int_optional(row.get("COMMUNITY AREA", ""),  "COMMUNITY AREA")

    # ── Floats ────────────────────────────────────────────────────────────
    transformed["LATITUDE"]  = parse_float_optional(row.get("LATITUDE", ""),  "LATITUDE")
    transformed["LONGITUDE"] = parse_float_optional(row.get("LONGITUDE", ""), "LONGITUDE")

    # ── Boolean ───────────────────────────────────────────────────────────
    transformed["CONDITIONAL APPROVAL"] = parse_bool_yn(row.get("CONDITIONAL APPROVAL", ""), "CONDITIONAL APPROVAL")

    # ── Dates (all optional) ──────────────────────────────────────────────
    transformed["APPLICATION CREATED DATE"]          = parse_date(row.get("APPLICATION CREATED DATE", ""),          "APPLICATION CREATED DATE")
    transformed["APPLICATION REQUIREMENTS COMPLETE"] = parse_date(row.get("APPLICATION REQUIREMENTS COMPLETE", ""), "APPLICATION REQUIREMENTS COMPLETE")
    transformed["PAYMENT DATE"]                      = parse_date(row.get("PAYMENT DATE", ""),                      "PAYMENT DATE")
    transformed["LICENSE TERM START DATE"]           = parse_date(row.get("LICENSE TERM START DATE", ""),           "LICENSE TERM START DATE")
    transformed["LICENSE TERM EXPIRATION DATE"]      = parse_date(row.get("LICENSE TERM EXPIRATION DATE", ""),      "LICENSE TERM EXPIRATION DATE")
    transformed["LICENSE APPROVED FOR ISSUANCE"]     = parse_date(row.get("LICENSE APPROVED FOR ISSUANCE", ""),     "LICENSE APPROVED FOR ISSUANCE")
    transformed["DATE ISSUED"]                       = parse_date(row.get("DATE ISSUED", ""),                       "DATE ISSUED")
    transformed["LICENSE STATUS CHANGE DATE"]        = parse_date(row.get("LICENSE STATUS CHANGE DATE", ""),        "LICENSE STATUS CHANGE DATE")

    # LOCATION column intentionally excluded (derived from LATITUDE/LONGITUDE)

    return transformed
