"""
GovGuide AI — Canonical Government Service Document Builder

Generates deterministic, structured textual representations of GovernmentService
records across 9 standardized knowledge sections.

Rules:
- Missing/empty fields MUST be represented as NOT_AVAILABLE.
- DO NOT invent missing government information.
- Every document retains complete source attribution.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import uuid

NOT_AVAILABLE = "NOT_AVAILABLE"


def _clean_val(val: Any) -> str:
    """Return stripped string or NOT_AVAILABLE if empty, None, or placeholder."""
    if val is None:
        return NOT_AVAILABLE
    if isinstance(val, bool):
        return "Yes" if val else "No"
    s = str(val).strip()
    if not s or s.upper() in ("NONE", "NULL", "NAN", "NOT_AVAILABLE"):
        return NOT_AVAILABLE
    return s


@dataclass
class CanonicalDocument:
    """
    Deterministic representation of a government service for retrieval and RAG.
    """
    service_id: str
    service_code: str
    service_name: str
    category: str
    source_id: str
    source_url: str
    source_title: str
    source_confidence: str
    sections: Dict[str, str] = field(default_factory=dict)
    full_text: str = ""

    def get_section(self, section_name: str) -> str:
        return self.sections.get(section_name, NOT_AVAILABLE)


def build_service_document(
    service: Any,
    office: Optional[Any] = None,
) -> CanonicalDocument:
    """
    Build a deterministic CanonicalDocument from a GovernmentService ORM object or dict.
    """
    # Extract service fields (supports ORM model or dict)
    def _get(obj: Any, attr: str, default: Any = None) -> Any:
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    service_id = str(_get(service, "id") or uuid.uuid4())
    service_code = _clean_val(_get(service, "service_code"))
    service_name = _clean_val(_get(service, "name"))
    category = _clean_val(_get(service, "category"))
    description = _clean_val(_get(service, "description"))
    source_url = _clean_val(_get(service, "source_url"))
    license_term_years = _get(service, "license_term_years")
    fee_amount = _clean_val(_get(service, "fee_amount"))
    fee_description = _clean_val(_get(service, "fee_description"))
    application_portal_url = _clean_val(_get(service, "application_portal_url"))
    eligibility_summary = _clean_val(_get(service, "eligibility_summary"))
    required_documents = _clean_val(_get(service, "required_documents"))
    application_steps = _clean_val(_get(service, "application_steps"))
    inspection_required = _get(service, "inspection_required")
    renewal_required = _get(service, "renewal_required")
    renewal_period = _clean_val(_get(service, "renewal_period"))
    legal_reference = _clean_val(_get(service, "legal_reference"))
    source_confidence = _clean_val(_get(service, "source_confidence")) or "REQUIRES_MANUAL_VERIFICATION"

    # Office details (linked office or passed office)
    linked_office = office or _get(service, "office")
    office_name = _clean_val(_get(linked_office, "name")) if linked_office else "City of Chicago -- Department of Business Affairs and Consumer Protection (BACP)"
    office_dept = _clean_val(_get(linked_office, "department")) if linked_office else "Department of Business Affairs and Consumer Protection"
    office_addr = _clean_val(_get(linked_office, "street_address")) if linked_office else NOT_AVAILABLE
    office_city = _clean_val(_get(linked_office, "city")) if linked_office else "Chicago"
    office_state = _clean_val(_get(linked_office, "state")) if linked_office else "IL"
    office_zip = _clean_val(_get(linked_office, "zip_code")) if linked_office else "60602"
    office_phone = _clean_val(_get(linked_office, "phone")) if linked_office else NOT_AVAILABLE
    office_email = _clean_val(_get(linked_office, "email")) if linked_office else NOT_AVAILABLE
    office_hours = _clean_val(_get(linked_office, "business_hours")) if linked_office else NOT_AVAILABLE
    office_website = _clean_val(_get(linked_office, "website_url")) if linked_office else source_url

    source_title = f"City of Chicago Official Guide: {service_name} (Code {service_code})"
    source_id = f"src-{service_code}" if service_code != NOT_AVAILABLE else f"src-{service_id[:8]}"

    # ── 1. Overview Section ──────────────────────────────────────────────────
    sec_overview = (
        f"Service Name: {service_name}\n"
        f"License Code: {service_code}\n"
        f"Category: {category}\n"
        f"Responsible Department: {office_name}\n"
        f"Overview: {description}"
    )

    # ── 2. Eligibility Section ───────────────────────────────────────────────
    sec_eligibility = (
        f"Service: {service_name} (Code {service_code})\n"
        f"Eligibility Criteria: {eligibility_summary}"
    )

    # ── 3. Required Documents Section ─────────────────────────────────────────
    sec_documents = (
        f"Service: {service_name} (Code {service_code})\n"
        f"Required Documentation: {required_documents}"
    )

    # ── 4. Application Procedure Section ──────────────────────────────────────
    insp_str = _clean_val(inspection_required)
    sec_procedure = (
        f"Service: {service_name} (Code {service_code})\n"
        f"Online Application Portal: {application_portal_url}\n"
        f"Step-by-Step Procedure: {application_steps}\n"
        f"Inspection Required: {insp_str}"
    )

    # ── 5. Fees Section ───────────────────────────────────────────────────────
    sec_fees = (
        f"Service: {service_name} (Code {service_code})\n"
        f"License Fee Amount: {fee_amount}\n"
        f"Fee Details: {fee_description}"
    )

    # ── 6. Renewal Section ────────────────────────────────────────────────────
    term_str = f"{license_term_years} years" if license_term_years else NOT_AVAILABLE
    renew_str = _clean_val(renewal_required)
    sec_renewal = (
        f"Service: {service_name} (Code {service_code})\n"
        f"License Term Validity: {term_str}\n"
        f"Renewal Required: {renew_str}\n"
        f"Renewal Period: {renewal_period}"
    )

    # ── 7. Responsible Office Section ─────────────────────────────────────────
    sec_office = (
        f"Responsible Authority: {office_name}\n"
        f"Department: {office_dept}\n"
        f"Service Covered: {service_name} (Code {service_code})"
    )

    # ── 8. Contact Information Section ────────────────────────────────────────
    full_address = f"{office_addr}, {office_city}, {office_state} {office_zip}".replace("NOT_AVAILABLE, ", "")
    sec_contact = (
        f"Office Location: {full_address}\n"
        f"Phone: {office_phone}\n"
        f"Email: {office_email}\n"
        f"Business Hours: {office_hours}\n"
        f"Official Website: {office_website}"
    )

    # ── 9. Legal / Source Information Section ─────────────────────────────────
    sec_legal = (
        f"Service: {service_name} (Code {service_code})\n"
        f"Legal Reference: {legal_reference}\n"
        f"Source Confidence: {source_confidence}\n"
        f"Official Source URL: {source_url}"
    )

    sections = {
        "overview": sec_overview,
        "eligibility": sec_eligibility,
        "required_documents": sec_documents,
        "application_procedure": sec_procedure,
        "fees": sec_fees,
        "renewal": sec_renewal,
        "responsible_office": sec_office,
        "contact_information": sec_contact,
        "legal_source_information": sec_legal,
    }

    full_text_blocks = [
        f"=== {sec_name.upper().replace('_', ' ')} ===\n{sec_content}"
        for sec_name, sec_content in sections.items()
    ]
    full_text = "\n\n".join(full_text_blocks)

    return CanonicalDocument(
        service_id=service_id,
        service_code=service_code,
        service_name=service_name,
        category=category,
        source_id=source_id,
        source_url=source_url,
        source_title=source_title,
        source_confidence=source_confidence,
        sections=sections,
        full_text=full_text,
    )


def build_documents_from_services(services: List[Any]) -> List[CanonicalDocument]:
    """Build canonical documents for a collection of GovernmentService objects."""
    return [build_service_document(svc) for svc in services]
