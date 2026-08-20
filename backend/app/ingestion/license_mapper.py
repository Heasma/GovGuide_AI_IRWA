"""
GovGuide AI — License Code Mapper

Maps CSV LICENSE CODE values to GovernmentService records.

Primary mapping key: LICENSE CODE (numeric string, e.g. "1006")
Secondary verification: LICENSE DESCRIPTION (used only for sanity checking)

Mapping source: data/supplementary/government_services_template.csv

If a LICENSE CODE has no corresponding GovernmentService in the database,
it is flagged as UNMAPPED_LICENSE_CODE. No GovernmentService is invented.

The mapper also handles seeding GovernmentOffice and GovernmentService records
from the template CSV into the database (called once during ingestion setup).
"""

import csv
import logging
import uuid
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import psycopg2

logger = logging.getLogger(__name__)

NOT_AVAILABLE = "NOT_AVAILABLE"

# Path relative to project root
TEMPLATE_CSV_PATH = Path(__file__).parents[3] / "data" / "supplementary" / "government_services_template.csv"


class LicenseMapper:
    """
    Loads GovernmentService mappings from PostgreSQL.
    service_code (= LICENSE CODE) → GovernmentService.id (UUID string)

    Usage:
        mapper = LicenseMapper(db_url)
        mapper.load()
        service_id = mapper.get_service_id("1006")  # or None if unmapped
    """

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url
        # license_code (str) → GovernmentService.id (str)
        self._code_to_id: Dict[str, str] = {}
        self._loaded = False

    def load(self) -> None:
        """Load service_code → id mapping from the database."""
        conn = psycopg2.connect(self._db_url)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT service_code, id::text FROM government_services "
                "WHERE service_code IS NOT NULL"
            )
            rows = cur.fetchall()
            self._code_to_id = {r[0]: r[1] for r in rows}
            logger.info(
                "LicenseMapper loaded %d service_code mappings from DB.",
                len(self._code_to_id),
            )
        finally:
            conn.close()
        self._loaded = True

    def get_service_id(self, license_code: str) -> Optional[str]:
        """
        Return the GovernmentService UUID for the given license code.
        Returns None if the code is not mapped (UNMAPPED_LICENSE_CODE).
        """
        if not self._loaded:
            raise RuntimeError("LicenseMapper.load() must be called before get_service_id()")
        return self._code_to_id.get(license_code)

    def is_mapped(self, license_code: str) -> bool:
        """Return True if the license code is mapped to a GovernmentService."""
        return license_code in self._code_to_id

    @property
    def mapped_codes(self) -> List[str]:
        return list(self._code_to_id.keys())

    @property
    def total_mapped(self) -> int:
        return len(self._code_to_id)


def _parse_bool_field(val: str) -> Optional[bool]:
    """Parse True/False/True strings from template CSV."""
    if not val or val.strip() in (NOT_AVAILABLE, "", "nan"):
        return None
    v = val.strip().lower()
    if v == "true":
        return True
    if v == "false":
        return False
    return None


def _parse_int_field(val: str) -> Optional[int]:
    """Parse integer field from template CSV."""
    if not val or val.strip() in (NOT_AVAILABLE, "", "nan"):
        return None
    try:
        return int(float(val.strip()))
    except (ValueError, TypeError):
        return None


def _clean_text(val: str) -> Optional[str]:
    """Return None if val is blank or NOT_AVAILABLE."""
    if not val or val.strip() in (NOT_AVAILABLE, "", "nan"):
        return None
    return val.strip()


def seed_government_data(db_url: str, template_csv_path: Optional[Path] = None) -> Tuple[str, Dict[str, str]]:
    """
    Seed GovernmentOffice and GovernmentService records from the template CSV.

    This function is idempotent: if a service with the same service_code
    already exists, it is updated (upsert). The BACP office is created once.

    Args:
        db_url:             PostgreSQL sync connection string.
        template_csv_path:  Path to government_services_template.csv.
                            Defaults to the standard project location.

    Returns:
        Tuple of (bacp_office_id: str, service_code_to_id: Dict[str, str])
    """
    if template_csv_path is None:
        template_csv_path = TEMPLATE_CSV_PATH

    if not template_csv_path.exists():
        raise FileNotFoundError(f"Template CSV not found: {template_csv_path}")

    # Load template rows
    with open(template_csv_path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        template_rows = list(reader)

    logger.info("Loaded %d rows from template CSV.", len(template_rows))

    conn = psycopg2.connect(db_url)
    conn.autocommit = False

    try:
        cur = conn.cursor()

        # ── Upsert BACP Government Office ────────────────────────────────
        # All 56 license codes belong to BACP (verified from template CSV).
        sample = template_rows[0]
        bacp_name = "City of Chicago — Department of Business Affairs and Consumer Protection (BACP)"
        bacp_dept = "Department of Business Affairs and Consumer Protection"

        # Check if BACP already exists
        cur.execute(
            "SELECT id::text FROM government_offices WHERE name = %s LIMIT 1",
            (bacp_name,)
        )
        row = cur.fetchone()

        if row:
            bacp_id = row[0]
            logger.info("BACP GovernmentOffice already exists: %s", bacp_id)
            # Update contact info
            cur.execute(
                """
                UPDATE government_offices SET
                    department     = %s,
                    street_address = %s,
                    city           = %s,
                    state          = %s,
                    zip_code       = %s,
                    phone          = %s,
                    email          = %s,
                    business_hours = %s,
                    website_url    = %s
                WHERE id = %s::uuid
                """,
                (
                    bacp_dept,
                    _clean_text(sample.get("office_address", "")),
                    "Chicago",
                    "IL",
                    "60602",
                    _clean_text(sample.get("phone", "")),
                    _clean_text(sample.get("email", "")),
                    _clean_text(sample.get("business_hours", "")),
                    _clean_text(sample.get("website_url", "")),
                    bacp_id,
                )
            )
        else:
            bacp_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO government_offices
                    (id, name, department, street_address, city, state, zip_code,
                     phone, email, business_hours, website_url, raw_metadata)
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    bacp_id,
                    bacp_name,
                    bacp_dept,
                    _clean_text(sample.get("office_address", "")),
                    "Chicago",
                    "IL",
                    "60602",
                    _clean_text(sample.get("phone", "")),
                    _clean_text(sample.get("email", "")),
                    _clean_text(sample.get("business_hours", "")),
                    _clean_text(sample.get("website_url", "")),
                    "{}",
                )
            )
            logger.info("Created BACP GovernmentOffice: %s", bacp_id)

        # ── Upsert GovernmentService per license code ─────────────────────
        service_code_to_id: Dict[str, str] = {}

        for tmpl in template_rows:
            code = tmpl.get("license_code", "").strip()
            desc = tmpl.get("license_description", "").strip()
            if not code:
                logger.warning("Template row missing license_code, skipping.")
                continue

            # Service name: use service_name if available, else license_description
            svc_name = _clean_text(tmpl.get("service_name", "")) or desc

            cur.execute(
                "SELECT id::text FROM government_services WHERE service_code = %s LIMIT 1",
                (code,)
            )
            existing = cur.fetchone()

            service_data = (
                code,                                               # service_code
                svc_name,                                          # name
                _clean_text(tmpl.get("service_overview", "")),     # description
                _clean_text(tmpl.get("service_category", "")),     # category
                bacp_id,                                           # office_id
                True,                                              # is_active
                _clean_text(tmpl.get("official_url", "")),         # source_url
                _parse_int_field(tmpl.get("license_term_years", "")),       # license_term_years
                _clean_text(tmpl.get("fee_amount", "")),                     # fee_amount
                _clean_text(tmpl.get("fee_description", "")),                # fee_description
                _clean_text(tmpl.get("application_portal_url", "")),         # application_portal_url
                _clean_text(tmpl.get("eligibility_summary", "")),            # eligibility_summary
                _clean_text(tmpl.get("required_documents", "")),             # required_documents
                _clean_text(tmpl.get("application_steps", "")),              # application_steps
                _parse_bool_field(tmpl.get("inspection_required", "")),      # inspection_required
                _parse_bool_field(tmpl.get("renewal_required", "")),         # renewal_required
                _clean_text(tmpl.get("renewal_period", "")),                 # renewal_period
                _clean_text(tmpl.get("legal_reference", "")),                # legal_reference
                _clean_text(tmpl.get("source_confidence", "")) or "REQUIRES_MANUAL_VERIFICATION",  # source_confidence
            )

            if existing:
                service_id = existing[0]
                cur.execute(
                    """
                    UPDATE government_services SET
                        service_code           = %s,
                        name                   = %s,
                        description            = %s,
                        category               = %s,
                        office_id              = %s::uuid,
                        is_active              = %s,
                        source_url             = %s,
                        license_term_years     = %s,
                        fee_amount             = %s,
                        fee_description        = %s,
                        application_portal_url = %s,
                        eligibility_summary    = %s,
                        required_documents     = %s,
                        application_steps      = %s,
                        inspection_required    = %s,
                        renewal_required       = %s,
                        renewal_period         = %s,
                        legal_reference        = %s,
                        source_confidence      = %s
                    WHERE id = %s::uuid
                    """,
                    (*service_data, service_id)
                )
            else:
                service_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO government_services
                        (id, service_code, name, description, category, office_id,
                         is_active, source_url,
                         license_term_years, fee_amount, fee_description,
                         application_portal_url, eligibility_summary, required_documents,
                         application_steps, inspection_required, renewal_required,
                         renewal_period, legal_reference, source_confidence, raw_metadata)
                    VALUES (%s::uuid, %s, %s, %s, %s, %s::uuid,
                            %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, '{}'::jsonb)
                    """,
                    (service_id, *service_data)
                )
                logger.debug("Created GovernmentService code=%s id=%s", code, service_id)

            service_code_to_id[code] = service_id

        conn.commit()
        logger.info(
            "Seeded %d GovernmentService records under BACP office %s",
            len(service_code_to_id),
            bacp_id,
        )
        return bacp_id, service_code_to_id

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
