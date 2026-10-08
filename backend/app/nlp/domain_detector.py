"""
GovGuide AI — Domain Detector & Classifier

Identifies the operational domain of citizen and business queries:
- Domain.BUSINESS_LICENSE: Municipal commercial licensing (Retail Food, LBL, Liquor, PPA, etc.)
- Domain.GOVERNMENT_SERVICE: General municipal offices, city hall services, 311
- Domain.DRIVER_LICENSE: Personal driving licences, permits, DMV / Secretary of State
- Domain.VEHICLE_REGISTRATION: Personal license plates, vehicle titles, registration stickers
- Domain.AVIATION: Pilot licences, aircraft registration, helicopter permits
- Domain.TAX: Personal income tax, IRS filings, state taxes
- Domain.HEALTH: Personal healthcare, Medicaid, Medicare
- Domain.EDUCATION: School admissions, student aid, university enrollment
- Domain.OTHER / UNKNOWN: Other unsupported domain categories
"""

import re
from typing import Set, Tuple, List, Optional
from app.orchestrator.message_schema import Domain

# Knowledge base supported domains in GovGuide AI (City of Chicago BACP focus)
SUPPORTED_DOMAINS: Set[Domain] = {
    Domain.BUSINESS_LICENSE,
    Domain.GOVERNMENT_SERVICE,
    Domain.UNKNOWN,
}

UNSUPPORTED_DOMAINS: Set[Domain] = {
    Domain.DRIVER_LICENSE,
    Domain.AVIATION,
    Domain.VEHICLE_REGISTRATION,
    Domain.TAX,
    Domain.HEALTH,
    Domain.EDUCATION,
    Domain.OTHER,
}


def is_domain_supported(domain: Domain) -> bool:
    """Checks whether a domain is supported by the knowledge base."""
    return domain not in UNSUPPORTED_DOMAINS


# ── Domain Pattern Definitions ───────────────────────────────────────────────

_DRIVER_LICENSE_PATTERNS = [
    # Explicit driver/driving license phrases (handling both 'license' and 'licence')
    r"\b(driver'?s?\s+licen[sc]e|driving\s+licen[sc]e)\b",
    r"\b(licen[sc]e\s+to\s+drive|licen[sc]e\s+for\s+driving)\b",
    r"\b(drive\s+(a\s+)?car|driving\s+(a\s+)?car|drive\s+(a\s+)?vehicle|driving\s+(a\s+)?vehicle)\b",
    r"\b(need\s+(to\s+)?drive|want\s+(to\s+)?drive|learning\s+to\s+drive)\b",
    r"\b(learner'?s?\s+permit|provisional\s+licen[sc]e|instruction\s+permit)\b",
    r"\b(dmv|dmv\s+licen[sc]e|secretary\s+of\s+state\s+driver|cyberdriveillinois)\b",
    r"\b(class\s+([a-z0-9]+|\w+)\s+licen[sc]e)\b",
    r"\b(licen[sc]e\s+(do\s+i\s+need|is\s+needed|required)?\s*for\s+(a\s+)?(car|vehicle))\b",
    r"\b(standard\s+driver|commercial\s+driver'?s?\s+licen[sc]e|cdl\s+driver)\b",
    r"\b(driving\s+test|driver'?s?\s+test|road\s+test)\b",
    r"\b(motorcycle\s+driver'?s?\s+licen[sc]e|ride\s+a\s+motorcycle\s+licen[sc]e)\b",
]

_AVIATION_PATTERNS = [
    r"\b(pilot\s+licen[sc]e|private\s+pilot|commercial\s+pilot)\b",
    r"\b(fly\s+(a\s+)?(plane|airplane|helicopter|aircraft|drone))\b",
    r"\b(aviation\s+licen[sc]e|aircraft\s+permit|faa\s+licen[sc]e)\b",
]

_SPACE_PATTERNS = [
    r"\b(space\s+station|moon|mars|spacecraft|spaceship|rocket|satellite|outer\s+space)\b",
]

_VEHICLE_REGISTRATION_PATTERNS = [
    r"\b(licen[sc]e\s+plates?|registration\s+sticker|vehicle\s+title|car\s+title)\b",
    r"\b(register\s+(my\s+)?car|vehicle\s+registration|plate\s+renewal)\b",
]

_TAX_PATTERNS = [
    r"\b(income\s+tax|personal\s+tax|irs|file\s+taxes|tax\s+return|tax\s+refund|w-2|1099)\b",
    r"\b(property\s+tax\s+appeal|individual\s+tax)\b",
]

_HEALTH_PATTERNS = [
    r"\b(medicaid|medicare|health\s+insurance\s+card|personal\s+medical\s+records?)\b",
    r"\b(patient\s+portal|doctor\s+appointment|vaccine\s+card)\b",
]

_EDUCATION_PATTERNS = [
    r"\b(fafsa|student\s+loan|school\s+enrollment|college\s+admission|university\s+degree)\b",
]

_BUSINESS_LICENSE_PATTERNS = [
    r"\b(business\s+licen[sc]e|commercial\s+licen[sc]e|city\s+licen[sc]e)\b",
    r"\b(retail\s+food|restaurant|cafe|bakery|diner|bistro|eatery|coffee\s+shop)\b",
    r"\b(mobile\s+food|food\s+truck|food\s+cart|peddler)\b",
    r"\b(liquor|tavern|bar|consumption\s+on\s+premises|beer|wine|spirits|alcohol)\b",
    r"\b(limited\s+business\s+licen[sc]e|lbl|general\s+business)\b",
    r"\b(public\s+place\s+of\s+amusement|ppa|entertainment\s+venue|theater|music\s+venue)\b",
    r"\b(tobacco|smoke\s+shop|vape|cigar|cigarettes)\b",
    r"\b(children('s|\s+)?services|daycare|childcare|preschool)\b",
    r"\b(motor\s+vehicle\s+repair\s+business|auto\s+repair\s+shop|garage\s+licen[sc]e|body\s+shop\s+licen[sc]e)\b",
    r"\b(massage\s+establishment|spa\s+licen[sc]e)\b",
    r"\b(shared\s+kitchen|commissary\s+licen[sc]e)\b",
    r"\b(valet\s+parking\s+operator|parking\s+garage\s+licen[sc]e)\b",
    r"\b(home\s+occupation|home-based\s+business)\b",
    r"\b(animal\s+care\s+facility|pet\s+shop|veterinary)\b",
    r"\b(hotel\s+licen[sc]e|bed\s+and\s+breakfast|vacation\s+rental)\b",
    r"\b(open\s+a\s+(business|shop|store|company)|start\s+a\s+(business|company))\b",
    r"\b(bacp|small\s+business\s+center|business\s+affairs)\b",
    r"\b(1006|1010|1011|1002|1004|1005|1012|1014|1016|1020|1030|1050)\b",
    r"\b(license\s+services?|all\s+licenses?|all\s+business\s+licenses?|business\s+license\s+types?)\b",
]

_GOVERNMENT_SERVICE_PATTERNS = [
    r"\b(city\s+hall|small\s+business\s+center|121\s+n\s+lasalle|room\s+800)\b",
    r"\b(311\s+service|311|city\s+clerk|zoning\s+department|building\s+inspection)\b",
    r"\b(chicago\s+department|municipal\s+office)\b",
    r"\b(government\s+services?|city\s+services?|municipal\s+services?|56\s+services?|services?\s+summary|all\s+services|show\s+all\s+services|all\s+56\s+services)\b",
]


def classify_domain(query: str) -> Domain:
    """
    Classifies the domain of a query into a Domain enum.

    Args:
        query: Raw or normalized user query string.

    Returns:
        The matched Domain enum value.
    """
    if not query or not query.strip():
        return Domain.UNKNOWN

    lower = query.lower()

    # 1. Check Driver License domain first (protect against vehicle/drive confusion)
    for pattern in _DRIVER_LICENSE_PATTERNS:
        if re.search(pattern, lower, re.I):
            # Verify it's not explicitly about operating a commercial auto repair/dealership business
            if not re.search(r"\b(open\s+an?\s+auto|start\s+an?\s+auto|repair\s+business|garage\s+business|dealership)\b", lower):
                return Domain.DRIVER_LICENSE

    # 2. Check Aviation domain
    for pattern in _AVIATION_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.AVIATION

    # 3. Check Vehicle Registration
    for pattern in _VEHICLE_REGISTRATION_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.VEHICLE_REGISTRATION

    # 4. Check Tax domain
    for pattern in _TAX_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.TAX

    # 5. Check Health domain
    for pattern in _HEALTH_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.HEALTH

    # 6. Check Education domain
    for pattern in _EDUCATION_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.EDUCATION

    # 6b. Check Space / Astronomy domain (Unsupported)
    for pattern in _SPACE_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.OTHER

    # 7. Check Government Service domain (Supported)
    for pattern in _GOVERNMENT_SERVICE_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.GOVERNMENT_SERVICE

    # 8. Check Business License domain (Supported)
    for pattern in _BUSINESS_LICENSE_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.BUSINESS_LICENSE

    # General / Unknown defaults
    if any(k in lower for k in ("license", "licence", "permit", "fee", "apply", "renewal", "renew")):
        # Default to business license if asking general regulatory/licensing question
        return Domain.BUSINESS_LICENSE

    return Domain.UNKNOWN


class DomainDetector:
    """Reusable domain detection component for agent and retrieval pipelines."""

    def __init__(self, supported_domains: Optional[Set[Domain]] = None):
        self.supported_domains = supported_domains or SUPPORTED_DOMAINS

    def detect(self, query: str) -> Tuple[Domain, bool]:
        domain = classify_domain(query)
        is_supported = self.is_supported(domain)
        return domain, is_supported

    def is_supported(self, domain: Domain) -> bool:
        return domain in self.supported_domains
