"""
GovGuide AI — Phase 3 Unit Tests: CSV Ingestion Pipeline

Tests for:
- All 37 columns detected by csv_reader
- CSV parsing and column validation
- Date conversion (MM/DD/YYYY → datetime.date)
- Float conversion (latitude, longitude)
- Integer conversion (ward, precinct, police district, community area)
- Boolean conversion (Y/N → True/False)
- License code mapping
- Duplicate license_id detection
- Missing required field validation
- Malformed value handling
"""

import csv
import io
import sys
import os
from datetime import date
from pathlib import Path
from typing import Dict, List
import pytest

# Add backend dir to path
PROJECT_ROOT = Path(__file__).parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from app.ingestion.csv_reader import (
    EXPECTED_COLUMNS,
    validate_columns,
    stream_csv,
    ColumnMismatchError,
)
from app.ingestion.validators import (
    validate_row,
    validate_batch,
    KNOWN_LICENSE_CODES,
    ValidationResult,
)
from app.ingestion.transformers import (
    parse_date,
    parse_bool_yn,
    parse_float_optional,
    parse_int_optional,
    parse_str_optional,
    transform_row,
)

# ── Paths ─────────────────────────────────────────────────────────────────────
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "Business_Licenses_-_Current_Active_20260819.csv"
TEMPLATE_CSV = PROJECT_ROOT / "data" / "supplementary" / "government_services_template.csv"

# ── Helpers ───────────────────────────────────────────────────────────────────

def make_valid_row(**overrides) -> Dict[str, str]:
    """Return a minimally valid CSV row dict."""
    base = {
        "ID": "2948166-20280716",
        "LICENSE ID": "9999999",
        "ACCOUNT NUMBER": "123456",
        "SITE NUMBER": "1",
        "LEGAL NAME": "TEST BUSINESS LLC",
        "DOING BUSINESS AS NAME": "Test Business",
        "ADDRESS": "123 N MAIN ST",
        "CITY": "CHICAGO",
        "STATE": "IL",
        "ZIP CODE": "60601",
        "WARD": "42",
        "PRECINCT": "5",
        "WARD PRECINCT": "42-5",
        "POLICE DISTRICT": "18",
        "COMMUNITY AREA": "8",
        "COMMUNITY AREA NAME": "NEAR NORTH SIDE",
        "NEIGHBORHOOD": "NEAR NORTH SIDE",
        "LICENSE CODE": "1006",
        "LICENSE DESCRIPTION": "Retail Food Establishment",
        "BUSINESS ACTIVITY ID": "501",
        "BUSINESS ACTIVITY": "Food Preparation",
        "LICENSE NUMBER": "2948166",
        "APPLICATION TYPE": "RENEW",
        "APPLICATION CREATED DATE": "",
        "APPLICATION REQUIREMENTS COMPLETE": "07/28/2026",
        "PAYMENT DATE": "07/29/2026",
        "CONDITIONAL APPROVAL": "N",
        "LICENSE TERM START DATE": "07/16/2026",
        "LICENSE TERM EXPIRATION DATE": "07/15/2028",
        "LICENSE APPROVED FOR ISSUANCE": "07/29/2026",
        "DATE ISSUED": "07/30/2026",
        "LICENSE STATUS": "AAI",
        "LICENSE STATUS CHANGE DATE": "",
        "SSA": "",
        "LATITUDE": "41.970352506",
        "LONGITUDE": "-87.6501347448",
        "LOCATION": "POINT (-87.65 41.97)",
    }
    base.update(overrides)
    return base


# ── CSV Reader Tests ──────────────────────────────────────────────────────────

class TestCSVColumnDetection:
    """Tests for csv_reader.EXPECTED_COLUMNS and validate_columns()."""

    def test_expected_columns_count(self):
        """All 37 expected columns must be listed."""
        assert len(EXPECTED_COLUMNS) == 37

    def test_expected_columns_contain_all_required(self):
        """Key required columns must be in the expected list."""
        required = [
            "LICENSE ID", "ACCOUNT NUMBER", "SITE NUMBER", "LEGAL NAME",
            "LICENSE CODE", "LICENSE DESCRIPTION", "LICENSE NUMBER",
            "LICENSE STATUS", "CONDITIONAL APPROVAL", "DATE ISSUED",
            "LATITUDE", "LONGITUDE",
        ]
        for col in required:
            assert col in EXPECTED_COLUMNS, f"Missing: {col}"

    @pytest.mark.skipif(not RAW_CSV.exists(), reason="Raw CSV not available")
    def test_actual_csv_columns_match(self):
        """Actual CSV header must match all 37 expected columns."""
        report = validate_columns(RAW_CSV)
        assert report.is_valid, f"Missing columns: {report.missing}"
        assert len(report.found) == 37

    @pytest.mark.skipif(not RAW_CSV.exists(), reason="Raw CSV not available")
    def test_no_unexpected_columns(self):
        """Actual CSV should have no extra columns beyond expected."""
        report = validate_columns(RAW_CSV)
        assert report.unexpected == []

    def test_validate_columns_with_missing_column(self, tmp_path):
        """validate_columns() must raise ColumnMismatchError if a column is absent."""
        incomplete_headers = EXPECTED_COLUMNS[:36]  # drop last column
        csv_content = ",".join(incomplete_headers) + "\n"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")
        with pytest.raises(ColumnMismatchError):
            validate_columns(csv_file)

    @pytest.mark.skipif(not RAW_CSV.exists(), reason="Raw CSV not available")
    def test_stream_csv_first_100_rows(self):
        """stream_csv with max_rows=100 must yield exactly 100 rows."""
        rows = []
        for batch in stream_csv(RAW_CSV, batch_size=50, max_rows=100):
            rows.extend(batch)
        assert len(rows) == 100

    @pytest.mark.skipif(not RAW_CSV.exists(), reason="Raw CSV not available")
    def test_stream_csv_all_expected_keys_present(self):
        """Each streamed row must have all 37 expected column keys."""
        for batch in stream_csv(RAW_CSV, batch_size=10, max_rows=10):
            for row in batch:
                for col in EXPECTED_COLUMNS:
                    assert col in row, f"Column '{col}' missing from row"
            break


# ── Date Parsing Tests ────────────────────────────────────────────────────────

class TestDateParsing:
    """Tests for transformers.parse_date()."""

    def test_valid_date(self):
        assert parse_date("07/30/2026", "DATE ISSUED") == date(2026, 7, 30)

    def test_empty_string_returns_none(self):
        assert parse_date("", "DATE ISSUED") is None

    def test_whitespace_returns_none(self):
        assert parse_date("   ", "DATE ISSUED") is None

    def test_invalid_format_raises_value_error(self):
        with pytest.raises(ValueError, match="Expected format MM/DD/YYYY"):
            parse_date("2026-07-30", "DATE ISSUED")  # ISO format — wrong

    def test_invalid_date_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_date("13/40/2026", "DATE ISSUED")  # month 13, day 40

    def test_correct_month_day_year_parsing(self):
        """Ensure MM/DD/YYYY not misread as YYYY-MM-DD."""
        result = parse_date("01/15/2025", "TEST")
        assert result.month == 1
        assert result.day == 15
        assert result.year == 2025


# ── Float Parsing Tests ───────────────────────────────────────────────────────

class TestFloatParsing:
    """Tests for transformers.parse_float_optional()."""

    def test_valid_latitude(self):
        result = parse_float_optional("41.970352506", "LATITUDE")
        assert abs(result - 41.970352506) < 1e-6

    def test_valid_longitude(self):
        result = parse_float_optional("-87.6501347448", "LONGITUDE")
        assert abs(result - (-87.6501347448)) < 1e-6

    def test_empty_returns_none(self):
        assert parse_float_optional("", "LATITUDE") is None

    def test_invalid_float_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_float_optional("not-a-float", "LATITUDE")

    def test_integer_string_parsed_as_float(self):
        assert parse_float_optional("42", "LATITUDE") == 42.0


# ── Integer Parsing Tests ─────────────────────────────────────────────────────

class TestIntegerParsing:
    """Tests for transformers.parse_int_optional()."""

    def test_valid_integer(self):
        assert parse_int_optional("42", "WARD") == 42

    def test_empty_returns_none(self):
        assert parse_int_optional("", "WARD") is None

    def test_float_string_truncated_to_int(self):
        assert parse_int_optional("3.0", "WARD") == 3

    def test_invalid_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_int_optional("abc", "WARD")


# ── Boolean Parsing Tests ─────────────────────────────────────────────────────

class TestBooleanParsing:
    """Tests for transformers.parse_bool_yn()."""

    def test_y_returns_true(self):
        assert parse_bool_yn("Y", "CONDITIONAL APPROVAL") is True

    def test_n_returns_false(self):
        assert parse_bool_yn("N", "CONDITIONAL APPROVAL") is False

    def test_lowercase_y_returns_true(self):
        assert parse_bool_yn("y", "CONDITIONAL APPROVAL") is True

    def test_invalid_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_bool_yn("YES", "CONDITIONAL APPROVAL")

    def test_empty_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_bool_yn("", "CONDITIONAL APPROVAL")


# ── Validator Tests ───────────────────────────────────────────────────────────

class TestRowValidation:
    """Tests for validators.validate_row()."""

    def test_valid_row_passes(self):
        row = make_valid_row()
        result = validate_row(row, 0)
        assert result.is_valid, f"Expected valid, got errors: {result.errors}"

    def test_missing_license_id_fails(self):
        row = make_valid_row(**{"LICENSE ID": ""})
        result = validate_row(row, 0)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert "MISSING_LICENSE_ID" in codes

    def test_missing_account_number_fails(self):
        row = make_valid_row(**{"ACCOUNT NUMBER": ""})
        result = validate_row(row, 0)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert "MISSING_ACCOUNT_NUMBER" in codes

    def test_missing_license_code_fails(self):
        row = make_valid_row(**{"LICENSE CODE": ""})
        result = validate_row(row, 0)
        assert not result.is_valid

    def test_invalid_license_code_fails(self):
        row = make_valid_row(**{"LICENSE CODE": "9999"})
        result = validate_row(row, 0)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert "INVALID_LICENSE_CODE" in codes

    def test_all_56_known_codes_pass(self):
        """Every known license code must pass validation."""
        for code in KNOWN_LICENSE_CODES:
            row = make_valid_row(**{"LICENSE CODE": code})
            result = validate_row(row, 0)
            code_errors = [e for e in result.errors if e.field == "LICENSE CODE"]
            assert not code_errors, f"Code {code} failed: {code_errors}"

    def test_invalid_conditional_approval_fails(self):
        row = make_valid_row(**{"CONDITIONAL APPROVAL": "X"})
        result = validate_row(row, 0)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert "INVALID_BOOLEAN" in codes

    def test_invalid_date_fails(self):
        row = make_valid_row(**{"DATE ISSUED": "2026-07-30"})  # wrong format
        result = validate_row(row, 0)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert "INVALID_DATE" in codes

    def test_empty_optional_date_passes(self):
        row = make_valid_row(**{"APPLICATION CREATED DATE": ""})
        result = validate_row(row, 0)
        assert result.is_valid

    def test_invalid_latitude_out_of_range(self):
        row = make_valid_row(**{"LATITUDE": "999.0"})
        result = validate_row(row, 0)
        assert not result.is_valid
        codes = [e.code for e in result.errors]
        assert "INVALID_COORDINATE" in codes

    def test_invalid_longitude_out_of_range(self):
        row = make_valid_row(**{"LONGITUDE": "-200.0"})
        result = validate_row(row, 0)
        assert not result.is_valid

    def test_ward_out_of_range_fails(self):
        row = make_valid_row(**{"WARD": "51"})  # Chicago max is 50
        result = validate_row(row, 0)
        assert not result.is_valid

    def test_empty_ward_passes(self):
        row = make_valid_row(**{"WARD": ""})
        result = validate_row(row, 0)
        assert result.is_valid


class TestDuplicateDetection:
    """Tests for validate_batch() duplicate detection."""

    def test_duplicate_license_id_flagged(self):
        row = make_valid_row(**{"LICENSE ID": "DUP-001"})
        seen: set = {"DUP-001"}  # pre-populate
        results = validate_batch([row], start_index=0, seen_license_ids=seen)
        assert len(results) == 1
        codes = [e.code for e in results[0].errors]
        assert "DUPLICATE_LICENSE_ID" in codes

    def test_unique_license_ids_pass(self):
        rows = [
            make_valid_row(**{"LICENSE ID": "UNIQUE-001"}),
            make_valid_row(**{"LICENSE ID": "UNIQUE-002"}),
        ]
        seen: set = set()
        results = validate_batch(rows, start_index=0, seen_license_ids=seen)
        for r in results:
            assert r.is_valid, f"Expected valid: {r.errors}"


# ── Full Row Transformation Tests ─────────────────────────────────────────────

class TestRowTransformation:
    """Tests for transformers.transform_row()."""

    def test_transform_valid_row(self):
        row = make_valid_row()
        t = transform_row(row)
        assert t["LICENSE ID"] == "9999999"
        assert t["ACCOUNT NUMBER"] == "123456"
        assert t["CONDITIONAL APPROVAL"] is False
        assert t["WARD"] == 42
        assert t["LICENSE TERM START DATE"] == date(2026, 7, 16)
        assert t["APPLICATION CREATED DATE"] is None
        assert isinstance(t["LATITUDE"], float)

    def test_transform_empty_optional_fields_become_none(self):
        row = make_valid_row(**{
            "WARD": "",
            "SSA": "",
            "APPLICATION CREATED DATE": "",
            "LATITUDE": "",
            "NEIGHBORHOOD": "",
        })
        t = transform_row(row)
        assert t["WARD"] is None
        assert t["SSA"] is None
        assert t["APPLICATION CREATED DATE"] is None
        assert t["LATITUDE"] is None
        assert t["NEIGHBORHOOD"] is None

    def test_transform_license_status_change_date_always_none(self):
        """LICENSE STATUS CHANGE DATE is 100% null in dataset."""
        row = make_valid_row(**{"LICENSE STATUS CHANGE DATE": ""})
        t = transform_row(row)
        assert t["LICENSE STATUS CHANGE DATE"] is None


# ── License Code Mapping Tests ────────────────────────────────────────────────

class TestLicenseCodeMapping:
    """Tests for validators — license code validation."""

    def test_all_known_codes_in_set(self):
        """The 56 known license codes must all be present in KNOWN_LICENSE_CODES."""
        assert len(KNOWN_LICENSE_CODES) == 56

    def test_known_codes_include_sample(self):
        sample_codes = ["1006", "1010", "4404", "4405", "1470", "7002", "8604"]
        for code in sample_codes:
            assert code in KNOWN_LICENSE_CODES, f"Expected code {code} to be known"

    def test_unknown_code_flagged(self):
        row = make_valid_row(**{"LICENSE CODE": "0000"})
        result = validate_row(row, 0)
        codes = [e.code for e in result.errors]
        assert "INVALID_LICENSE_CODE" in codes

    @pytest.mark.skipif(not TEMPLATE_CSV.exists(), reason="Template CSV not available")
    def test_template_csv_has_56_rows(self):
        """government_services_template.csv must have exactly 56 license codes."""
        import csv as csv_mod
        with open(TEMPLATE_CSV, encoding="utf-8-sig") as f:
            rows = list(csv_mod.DictReader(f))
        assert len(rows) == 56

    @pytest.mark.skipif(not TEMPLATE_CSV.exists(), reason="Template CSV not available")
    def test_template_csv_codes_match_known_codes(self):
        """All codes in template CSV must match KNOWN_LICENSE_CODES."""
        import csv as csv_mod
        with open(TEMPLATE_CSV, encoding="utf-8-sig") as f:
            template_codes = {row["license_code"].strip() for row in csv_mod.DictReader(f)}
        assert template_codes == KNOWN_LICENSE_CODES
