"""
GovGuide AI -- Phase 2 Supplementary Data Unit Tests
Tests for: license type extraction, schema validation, URL validation,
duplicate detection, NOT_AVAILABLE handling, official source validation.

Run: backend/.venv/Scripts/python -m pytest tests/unit/test_supplementary_validation.py -v
"""

import csv
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
import pytest

# ─── Paths ────────────────────────────────────────────────────────────────
# tests/unit/test_supplementary_validation.py  -> parents[0]=unit, [1]=tests, [2]=project_root
PROJECT_ROOT = Path(__file__).parents[2]
SUPP         = PROJECT_ROOT / "data" / "supplementary"
RAW_CSV      = PROJECT_ROOT / "data" / "raw" / "Business_Licenses_-_Current_Active_20260819.csv"
LICENSE_TYPES_CSV = SUPP / "license_types.csv"
TEMPLATE_CSV      = SUPP / "government_services_template.csv"
SOURCE_REG_CSV    = SUPP / "source_registry.csv"

# ─── Approved official government domains ─────────────────────────────────
APPROVED_DOMAINS = {
    "chicago.gov",
    "cityofchicago.org",
    "chicityclerk.com",
    "chicagocitytreasurer.com",
    "illinois.gov",
    "illinoisattorneygeneral.gov",
    "cookcountyil.gov",
    "municode.com",
    "amlegal.com",
}

URL_RE = re.compile(r"^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

NOT_AVAILABLE = "NOT_AVAILABLE"


def is_substantive(val: str) -> bool:
    """True if value is a real data value, not empty/null/NOT_AVAILABLE."""
    return str(val).strip() not in ("", NOT_AVAILABLE, "nan", "None")


# ─── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def license_types_df():
    assert LICENSE_TYPES_CSV.exists(), f"Missing: {LICENSE_TYPES_CSV}"
    return pd.read_csv(LICENSE_TYPES_CSV, dtype=str)


@pytest.fixture(scope="module")
def template_df():
    assert TEMPLATE_CSV.exists(), f"Missing: {TEMPLATE_CSV}"
    return pd.read_csv(TEMPLATE_CSV, dtype=str)


@pytest.fixture(scope="module")
def source_registry_df():
    assert SOURCE_REG_CSV.exists(), f"Missing: {SOURCE_REG_CSV}"
    return pd.read_csv(SOURCE_REG_CSV, dtype=str)


@pytest.fixture(scope="module")
def valid_license_codes(license_types_df):
    return set(license_types_df["license_code"].astype(str).tolist())


# ─── Test Group 1: License Type Extraction ───────────────────────────────

class TestLicenseTypeExtraction:

    def test_license_types_file_exists(self):
        assert LICENSE_TYPES_CSV.exists(), "license_types.csv was not generated."

    def test_license_types_count(self, license_types_df):
        assert len(license_types_df) == 56, \
            f"Expected 56 license types, got {len(license_types_df)}"

    def test_license_types_required_columns(self, license_types_df):
        required = {"license_code", "license_description", "record_count"}
        missing = required - set(license_types_df.columns)
        assert not missing, f"Missing columns: {missing}"

    def test_license_codes_are_unique(self, license_types_df):
        codes = license_types_df["license_code"].astype(str)
        assert codes.nunique() == len(codes), "Duplicate license codes detected."

    def test_no_empty_license_codes(self, license_types_df):
        empty = license_types_df["license_code"].isnull().sum()
        assert empty == 0, f"{empty} empty license_code values found."

    def test_no_empty_license_descriptions(self, license_types_df):
        empty = license_types_df["license_description"].isnull().sum()
        assert empty == 0, f"{empty} empty license_description values found."

    def test_record_counts_are_positive(self, license_types_df):
        df = license_types_df.copy()
        df["record_count"] = pd.to_numeric(df["record_count"], errors="coerce")
        assert (df["record_count"] > 0).all(), "All record counts must be > 0."

    def test_total_record_count_matches_expected(self, license_types_df):
        df = license_types_df.copy()
        df["record_count"] = pd.to_numeric(df["record_count"], errors="coerce")
        total = df["record_count"].sum()
        # CSV has 53,091 rows
        assert 52_000 <= total <= 54_000, \
            f"Total record count {total} out of expected range 52000-54000"

    def test_known_license_codes_present(self, valid_license_codes):
        """Spot-check: high-frequency license types must be present."""
        expected = {"1010", "4404", "1006", "1781", "4406", "1475"}
        missing = expected - valid_license_codes
        assert not missing, f"Known license codes missing: {missing}"

    def test_raw_csv_not_modified(self):
        """The raw CSV must never be modified -- verify it still exists."""
        assert RAW_CSV.exists(), "Raw CSV was deleted or moved!"
        stat = RAW_CSV.stat()
        assert stat.st_size > 0, "Raw CSV is empty!"


# ─── Test Group 2: Template Schema Validation ─────────────────────────────

class TestTemplateSchema:

    def test_template_file_exists(self):
        assert TEMPLATE_CSV.exists(), "government_services_template.csv was not generated."

    def test_template_row_count(self, template_df):
        assert len(template_df) == 56, \
            f"Expected 56 rows, got {len(template_df)}"

    def test_template_required_columns(self, template_df):
        required = {
            "license_code", "license_description", "service_name", "service_category",
            "government_department", "official_url", "source_type",
            "source_verified_date", "source_confidence",
        }
        missing = required - set(template_df.columns)
        assert not missing, f"Missing required columns: {missing}"

    def test_license_codes_match_extracted(self, template_df, valid_license_codes):
        template_codes = set(template_df["license_code"].astype(str).tolist())
        extra = template_codes - valid_license_codes
        missing = valid_license_codes - template_codes
        assert not extra,   f"Template has extra codes not in license_types.csv: {extra}"
        assert not missing, f"Template missing codes from license_types.csv: {missing}"

    # Rule 1 — license_code must be present
    def test_rule1_license_code_present(self, template_df):
        empty = template_df["license_code"].apply(
            lambda v: str(v).strip() == ""
        ).sum()
        assert empty == 0, f"Rule 1: {empty} rows have empty license_code."

    # Rule 2 — license_description must be present
    def test_rule2_license_description_present(self, template_df):
        empty = template_df["license_description"].apply(
            lambda v: str(v).strip() == ""
        ).sum()
        assert empty == 0, f"Rule 2: {empty} rows have empty license_description."

    # Rule 3 — service_name must be present or explicitly NOT_AVAILABLE
    def test_rule3_service_name_present_or_not_available(self, template_df):
        invalid = template_df["service_name"].apply(
            lambda v: str(v).strip() not in {NOT_AVAILABLE} and str(v).strip() == ""
        )
        assert not invalid.any(), \
            f"Rule 3: {invalid.sum()} rows have blank service_name (should be NOT_AVAILABLE if unknown)."

    # Rule 5 — government_department present when verified
    def test_rule5_department_present_when_verified(self, template_df):
        verified = template_df[
            template_df["source_confidence"].isin(["VERIFIED", "PARTIALLY_VERIFIED"])
        ]
        missing_dept = verified["government_department"].apply(
            lambda v: str(v).strip() in ("", NOT_AVAILABLE)
        )
        assert not missing_dept.any(), \
            f"Rule 5: {missing_dept.sum()} verified rows missing government_department."

    def test_source_confidence_valid_values(self, template_df):
        valid_conf = {"VERIFIED", "PARTIALLY_VERIFIED", "REQUIRES_MANUAL_VERIFICATION", "NOT_FOUND"}
        invalid = template_df["source_confidence"].apply(
            lambda v: str(v).strip() not in valid_conf
        )
        assert not invalid.any(), \
            f"Invalid source_confidence values: {template_df.loc[invalid, 'source_confidence'].unique().tolist()}"


# ─── Test Group 3: URL Validation ────────────────────────────────────────

class TestUrlValidation:

    # Rule 4 — official_url is valid HTTP/HTTPS when present
    def test_rule4_official_url_format(self, template_df):
        bad = []
        for _, row in template_df.iterrows():
            url = str(row["official_url"]).strip()
            if url in ("", NOT_AVAILABLE):
                continue
            if not URL_RE.match(url):
                bad.append((row["license_code"], url))
        assert not bad, f"Rule 4: Invalid URL formats: {bad}"

    # Rule 7 — source_url must be an official government domain
    def test_rule7_source_url_official_domain(self, source_registry_df):
        bad = []
        for _, row in source_registry_df.iterrows():
            url = str(row["source_url"]).strip()
            if url in ("", NOT_AVAILABLE, "nan"):
                continue
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower().lstrip("www.")
                if not any(domain == d or domain.endswith("." + d)
                           for d in APPROVED_DOMAINS):
                    bad.append((row["license_code"], url, domain))
            except Exception as e:
                bad.append((row["license_code"], url, str(e)))
        assert not bad, f"Rule 7: Unofficial source domains found: {bad}"

    def test_application_portal_url_is_official(self, template_df):
        """Chicago Business Direct portal URL must always be official."""
        for _, row in template_df.iterrows():
            url = str(row.get("application_portal_url", "")).strip()
            if url and url != NOT_AVAILABLE:
                parsed = urlparse(url)
                domain = parsed.netloc.lower().lstrip("www.")
                assert any(domain == d or domain.endswith("." + d)
                           for d in APPROVED_DOMAINS), \
                    f"Non-official application_portal_url: {url} (license: {row['license_code']})"


# ─── Test Group 4: Duplicate Detection ───────────────────────────────────

class TestDuplicateDetection:

    def test_no_duplicate_license_codes_in_template(self, template_df):
        dupes = template_df["license_code"].duplicated()
        assert not dupes.any(), \
            f"Duplicate license codes in template: {template_df.loc[dupes, 'license_code'].tolist()}"

    # Rule 9 — No duplicate license_code + source_url combinations
    def test_rule9_no_duplicate_source_records(self, source_registry_df):
        seen = set()
        dupes = []
        for _, row in source_registry_df.iterrows():
            key = (str(row["license_code"]), str(row["source_url"]))
            if key in seen:
                dupes.append(key)
            seen.add(key)
        assert not dupes, f"Rule 9: Duplicate (license_code, source_url) pairs: {dupes}"

    def test_source_registry_row_count(self, source_registry_df):
        assert len(source_registry_df) == 56, \
            f"Source registry should have 56 rows, got {len(source_registry_df)}"


# ─── Test Group 5: NOT_AVAILABLE Handling ────────────────────────────────

class TestNotAvailableHandling:

    def test_no_blank_required_fields(self, template_df):
        """Required fields must not be blank -- must be NOT_AVAILABLE if unknown."""
        check_cols = [
            "service_name", "service_category", "fee_amount",
            "government_department", "official_url",
        ]
        for col in check_cols:
            blank = template_df[col].apply(
                lambda v: str(v).strip() == "" or str(v).strip().lower() == "nan"
            )
            assert not blank.any(), \
                f"Column '{col}' has {blank.sum()} blank values. Use NOT_AVAILABLE instead."

    def test_not_available_is_literal_string(self, template_df):
        """NOT_AVAILABLE must be the exact literal string, not a variation."""
        check_cols = [
            "service_name", "fee_amount", "required_documents",
            "application_steps", "eligibility_summary",
        ]
        bad_variants = {"N/A", "n/a", "na", "NA", "not available", "Not Available", "TBD", "tbd"}
        for col in check_cols:
            for _, row in template_df.iterrows():
                val = str(row[col]).strip()
                assert val not in bad_variants, \
                    f"Non-standard not-available value '{val}' in column '{col}' for license {row['license_code']}"

    def test_no_guessed_fee_amounts(self, template_df):
        """Fee amounts must come from verified sources, not be fabricated."""
        for _, row in template_df.iterrows():
            fee = str(row["fee_amount"]).strip()
            conf = str(row["source_confidence"]).strip()
            url = str(row["official_url"]).strip()
            # If a fee is stated but source is REQUIRES_MANUAL_VERIFICATION with no specific URL
            if fee not in ("", NOT_AVAILABLE) and "$" in fee:
                if conf == "REQUIRES_MANUAL_VERIFICATION":
                    # This is only allowed if the url is the generic BACP page
                    # (not a fee-specific page), and data_gaps mentions verification needed
                    data_gaps = str(row.get("data_gaps", "")).lower()
                    assert "verification" in data_gaps or "verify" in data_gaps, \
                        f"License {row['license_code']}: fee stated but no verification note."


# ─── Test Group 6: Official Source Validation ─────────────────────────────

class TestOfficialSourceValidation:

    # Rule 8 — source_verified_date present for VERIFIED
    def test_rule8_verified_date_for_verified_sources(self, template_df):
        verified = template_df[template_df["source_confidence"] == "VERIFIED"]
        bad = []
        for _, row in verified.iterrows():
            vdate = str(row.get("source_verified_date", "")).strip()
            if not vdate or not DATE_RE.match(vdate):
                bad.append(row["license_code"])
        assert not bad, \
            f"Rule 8: VERIFIED records missing valid source_verified_date: {bad}"

    # Rule 10 — required_documents and application_steps need source URL
    def test_rule10_required_docs_have_source(self, template_df):
        bad = []
        for _, row in template_df.iterrows():
            docs = str(row.get("required_documents", "")).strip()
            steps = str(row.get("application_steps", "")).strip()
            url = str(row.get("official_url", "")).strip()
            if (is_substantive(docs) or is_substantive(steps)) and not is_substantive(url):
                bad.append(row["license_code"])
        assert not bad, \
            f"Rule 10: Docs/steps present without official URL: {bad}"

    # Rule 11 — fees have source
    def test_rule11_fees_have_source(self, template_df):
        bad = []
        for _, row in template_df.iterrows():
            fee = str(row.get("fee_amount", "")).strip()
            url = str(row.get("official_url", "")).strip()
            if is_substantive(fee) and "$" in fee and not is_substantive(url):
                bad.append(row["license_code"])
        assert not bad, \
            f"Rule 11: Fee present without official URL: {bad}"

    # Rule 12 — eligibility claims have source
    def test_rule12_eligibility_has_source(self, template_df):
        bad = []
        for _, row in template_df.iterrows():
            elig = str(row.get("eligibility_restrictions", "")).strip()
            url  = str(row.get("official_url", "")).strip()
            if is_substantive(elig) and not is_substantive(url):
                bad.append(row["license_code"])
        assert not bad, \
            f"Rule 12: Eligibility present without official URL: {bad}"

    def test_source_registry_status_values(self, source_registry_df):
        valid = {"VERIFIED", "PARTIALLY_VERIFIED", "REQUIRES_MANUAL_VERIFICATION", "NOT_FOUND"}
        invalid = source_registry_df["source_status"].apply(
            lambda v: str(v).strip() not in valid
        )
        assert not invalid.any(), \
            f"Invalid source_status values: {source_registry_df.loc[invalid, 'source_status'].unique().tolist()}"

    def test_verified_sources_have_title(self, source_registry_df):
        verified = source_registry_df[
            source_registry_df["source_status"].isin(["VERIFIED", "PARTIALLY_VERIFIED"])
        ]
        missing_title = verified["source_title"].apply(
            lambda v: str(v).strip() in ("", NOT_AVAILABLE)
        )
        assert not missing_title.any(), \
            f"Verified sources missing title: {source_registry_df.loc[missing_title, 'license_code'].tolist()}"

    def test_supplementary_dir_structure(self):
        """Verify all expected supplementary files exist."""
        expected = [
            "license_types.csv",
            "government_services_template.csv",
            "source_registry.csv",
            "government_service_schema.md",
            "schema_gap_analysis.md",
            "rag_document_template.md",
            "supplementary_data_validation.md",
            "data_collection_checklist.md",
        ]
        for fname in expected:
            assert (SUPP / fname).exists(), f"Missing supplementary file: {fname}"
