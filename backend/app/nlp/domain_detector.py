"""
GovGuide AI — Domain Detector & Classifier

Identifies the operational domain of citizen and business queries:
- Domain.BUSINESS_LICENSE: Municipal commercial licensing (Retail Food, LBL, Liquor, PPA, etc.)
- Domain.GOVERNMENT_SERVICE: General municipal offices, city hall services, 311, 56 services catalog
- Domain.DRIVER_LICENSE: Personal driving licences, permits, DMV / Secretary of State
- Domain.VEHICLE_REGISTRATION: Personal license plates, vehicle titles, registration stickers
- Domain.AVIATION: Pilot licences, aircraft registration, helicopter permits
- Domain.TAX: Personal income tax, IRS filings, state taxes
- Domain.HEALTH: Personal healthcare, Medicaid, Medicare
- Domain.EDUCATION: School admissions, student aid, university enrollment
- Domain.OTHER / Domain.UNKNOWN: Other unsupported out-of-domain categories (sports, cooking, jokes, consumer tech, math, etc.)
"""

import re
from typing import Set, Tuple, List, Optional
from app.orchestrator.message_schema import Domain
from app.nlp.language_detector import LanguageCode, resolve_query_language

# Strictly supported domains in GovGuide AI knowledge base
SUPPORTED_DOMAINS: Set[Domain] = {
    Domain.BUSINESS_LICENSE,
    Domain.GOVERNMENT_SERVICE,
}

UNSUPPORTED_DOMAINS: Set[Domain] = {
    Domain.DRIVER_LICENSE,
    Domain.AVIATION,
    Domain.VEHICLE_REGISTRATION,
    Domain.TAX,
    Domain.HEALTH,
    Domain.EDUCATION,
    Domain.OTHER,
    Domain.UNKNOWN,
}


def is_domain_supported(domain: Domain) -> bool:
    """Checks whether a domain is supported by the GovGuide AI knowledge base."""
    return domain in SUPPORTED_DOMAINS


# ── Out-of-Domain Response Templates ─────────────────────────────────────────

OUT_OF_DOMAIN_EN = (
    "Sorry, GovGuide AI does not provide information on this topic. "
    "It is designed to assist with government services, business licences, eligibility, "
    "required documents, application procedures, fees, renewal, and related official information."
)

OUT_OF_DOMAIN_THANGLISH = (
    "Mannikkavum, indha topic pathina information GovGuide AI system-la available illa. "
    "Indha system government services, business licences, eligibility, documents, fees, "
    "renewal, application procedure matrum related official information-ku mattum design seyyappattullathu."
)

OUT_OF_DOMAIN_TAMIL = (
    "மன்னிக்கவும், இந்த தலைப்பு குறித்த தகவல்கள் GovGuide AI அமைப்பில் கிடைக்கவில்லை. "
    "இந்த அமைப்பு அரசு சேவைகள், வணிக உரிமங்கள், தகுதி, தேவையான ஆவணங்கள், விண்ணப்ப நடைமுறைகள், "
    "கட்டணங்கள், புதுப்பித்தல் மற்றும் தொடர்புடைய அதிகாரப்பூர்வ தகவல்களுக்கு மட்டுமே வடிவமைக்கப்பட்டுள்ளது."
)

OUT_OF_DOMAIN_SINHALA = (
    "සමාවන්න, මෙම මාතෘකාව පිළිබඳ තොරතුරු GovGuide AI පද්ධතියේ නොමැත. "
    "මෙම පද්ධතිය රජයේ සේවාවන්, ව්‍යාපාර බලපත්‍ර, සුදුසුකම්, අවශ්‍ය ලියකියවිලි, "
    "අයදුම් කිරීමේ ක්‍රියා පටිපාටි, ගාස්තු, අලුත් කිරීම් සහ අදාළ නිල තොරතුරු සඳහා පමණක් නිර්මාණය කර ඇත."
)


def get_out_of_domain_response(language: str | LanguageCode = "en", domain: Optional[str] = None) -> str:
    """
    Returns standardized out-of-domain refusal message based on query language.
    """
    lang_str = language.value if hasattr(language, "value") else str(language).lower()

    if lang_str in ("thanglish", "mixed"):
        return OUT_OF_DOMAIN_THANGLISH
    elif lang_str in ("tamil", "ta"):
        return OUT_OF_DOMAIN_TAMIL
    elif lang_str in ("sinhala", "si", "singlish"):
        return OUT_OF_DOMAIN_SINHALA
    return OUT_OF_DOMAIN_EN


# ── Domain Pattern Definitions ───────────────────────────────────────────────

# 1. Driver's License & Driving
_DRIVER_LICENSE_PATTERNS = [
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

# 2. Aviation
_AVIATION_PATTERNS = [
    r"\b(pilot\s+licen[sc]e|private\s+pilot|commercial\s+pilot)\b",
    r"\b(fly\s+(a\s+)?(plane|airplane|helicopter|aircraft|drone))\b",
    r"\b(aviation\s+licen[sc]e|aircraft\s+permit|faa\s+licen[sc]e)\b",
]

# 3. Space
_SPACE_PATTERNS = [
    r"\b(space\s+station|moon|mars|spacecraft|spaceship|rocket|satellite|outer\s+space)\b",
]

# 4. Vehicle Registration
_VEHICLE_REGISTRATION_PATTERNS = [
    r"\b(licen[sc]e\s+plates?|registration\s+sticker|vehicle\s+title|car\s+title)\b",
    r"\b(register\s+(my\s+)?car|vehicle\s+registration|plate\s+renewal)\b",
]

# 5. Personal Tax
_TAX_PATTERNS = [
    r"\b(income\s+tax|personal\s+tax|irs|file\s+taxes|tax\s+return|tax\s+refund|w-2|1099)\b",
    r"\b(property\s+tax\s+appeal|individual\s+tax)\b",
]

# 6. Personal Health
_HEALTH_PATTERNS = [
    r"\b(medicaid|medicare|health\s+insurance\s+card|personal\s+medical\s+records?)\b",
    r"\b(patient\s+portal|doctor\s+appointment|vaccine\s+card)\b",
]

# 7. Education
_EDUCATION_PATTERNS = [
    r"\b(fafsa|student\s+loan|school\s+enrollment|college\s+admission|university\s+degree)\b",
]

# 8. Sports & Games (English, Thanglish, Tamil, Sinhala)
_SPORTS_PATTERNS = [
    r"\b(cricket|football|soccer|tennis|basketball|baseball|hockey|badminton|volleyball|rugby|chess)\b",
    r"\b(ipl|fifa|world\s+cup|match|tournament|score|wicket|batsman|bowler|stadium)\b",
    r"\b(who\s+will\s+win|win\s+the\s+match|match\s+prediction|play\s+cricket|how\s+to\s+play)\b",
    r"\b(villadurathu|vilayaduvathu|vilayadurathu|vilayattu|aatam|match-la|matchu)\b",
    r"(கிரிக்கெட்|கால்பந்து|போட்டி|விளையாட்டு)",
    r"(ක්‍රිකට්|පාපන්දු|තරගය)",
]

# 9. Cooking & Food Recipes (Home cooking recipes vs commercial food license)
_COOKING_RECIPE_PATTERNS = [
    r"\b(how\s+(?:do\s+i|to)\s+(?:cook|make|bake|prepare|fry|boil)\s+(?:biryani|briyani|pizza|burger|pasta|curry|cake|tea|coffee|rice|dosa|idli|sambar|noodles|soup|roti|bread))\b",
    r"\b(recipe\s+for|cooking\s+recipe|ingredients\s+for|how\s+to\s+cook|how\s+to\s+make\s+(?:biryani|briyani|food|dishes))\b",
    r"\b(samaikiradhu|samaikirathu|samaikkanum|samayal|seivadhu\s+eppadi|seivathu\s+eppadi|epdi\s+samaikkanum)\b",
    r"(சமையல்|பிரியாணி|செய்வது எப்படி)",
    r"(උයන්නේ කෙසේද|බිරියානි|වට්ටෝරුව)",
]

# 10. Entertainment, Jokes, Fun, Creative Writing
_ENTERTAINMENT_JOKES_PATTERNS = [
    r"\b(tell\s+(?:me\s+)?(?:a\s+)?joke|say\s+a\s+joke|funny\s+joke|make\s+me\s+laugh|crack\s+a\s+joke)\b",
    r"\b(write\s+(?:a\s+)?(?:poem|story|song|essay|script)|sing\s+(?:a\s+)?song)\b",
    r"\b(movie|cinema|actor|actress|hollywood|bollywood|kollywood|box\s+office|padam|padathula)\b",
    r"\b(riddle|comedy|humor|pun|magic\s+trick)\b",
    r"(நகைச்சுவை|பாடல்|கவிதை|திரைப்படம்)",
    r"(විහිළුවක්|ගීතයක්|චිත්‍රපටය)",
]

# 11. Consumer Tech, Gadgets, Shopping Advice
_CONSUMER_TECH_PATTERNS = [
    r"\b(which\s+mobile\s+phone\s+is\s+best|best\s+(?:mobile\s+)?phone|best\s+smartphone|best\s+laptop|buy\s+(?:a\s+)?phone)\b",
    r"\b(iphone|samsung\s+galaxy|xiaomi|pixel\s+[0-9]|android\s+vs\s+ios|which\s+(?:laptop|camera|headphone|smartwatch))\b",
    r"\b(mobile\s+phone\s+edhu\s+nalladhu|phone\s+vangalaam|laptop\s+edhu\s+nalladhu)\b",
    r"(மொபைல் போன்|ஸ்மார்ட்போன்)",
    r"(හොඳම දුරකථනය|ස්මාර්ට් ජංගම දුරකථනය)",
]

# 12. Mathematics, Science, Academic Homework, Coding
_MATH_SCIENCE_PATTERNS = [
    r"\b(explain\s+(?:a\s+)?mathematics\s+problem|math\s+problem|solve\s+(?:this\s+)?(?:math|equation|problem)|calculus|algebra|geometry|trigonometry)\b",
    r"\b(physics\s+problem|chemistry\s+formula|biology|photosynthesis|theory\s+of\s+relativity)\b",
    r"\b(how\s+to\s+code|python\s+code|write\s+(?:a\s+)?program|javascript\s+function|debug\s+code)\b",
    r"(கணித\s+பிரச்சனை|சமன்பாடு|இயற்பியல்)",
    r"(ගණිත ගැටලුව|සමීකරණය)",
]

# 13. General Trivia, Weather, Tourism, Personal Advice
_GENERAL_TRIVIA_PATTERNS = [
    r"\b(weather\s+today|weather\s+forecast|will\s+it\s+rain|temperature\s+in)\b",
    r"\b(tourist\s+places|travel\s+guide|places\s+to\s+visit\s+in)\b",
    r"\b(how\s+to\s+lose\s+weight|gym\s+workout|relationship\s+advice|dating\s+advice|astrology|horoscope)\b",
    r"\b(who\s+is\s+the\s+president\s+of|capital\s+of\s+[a-z]+)\b",
]

# 14. Government Service & Municipal Offices (Supported)
_GOVERNMENT_SERVICE_PATTERNS = [
    r"\b(city\s+hall|small\s+business\s+center|121\s+n\s+lasalle|room\s+800)\b",
    r"\b(311\s+service|311|city\s+clerk|zoning\s+department|building\s+inspection)\b",
    r"\b(chicago\s+department|municipal\s+office|bacp\s+office)\b",
    r"\b(service|services|government\s+services?|city\s+services?|municipal\s+services?|56\s+services?|services?\s+summary|all\s+services|show\s+all\s+services|all\s+56\s+services)\b",
]

# 15. Business Licensing (Supported)
_BUSINESS_LICENSE_PATTERNS = [
    r"\b(business\s+licen[sc]e|commercial\s+licen[sc]e|city\s+licen[sc]e|municipal\s+licen[sc]e)\b",
    r"\b(secondary\s+sports|sports\s+licen[sc]e)\b",
    r"\b(retail\s+food|restaurant|cafe|bakery|diner|bistro|eatery|coffee\s+shop|grocery|supermarket)\b",
    r"\b(mobile\s+food|food\s+truck|food\s+cart|peddler)\b",
    r"\b(liquor|tavern|bar|consumption\s+on\s+premises|beer|wine|spirits|alcohol|package\s+goods)\b",
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
    r"\b(open|start|run|operate|launch)\s+(?:a\s+|an\s+)?(?:[a-z0-9_\-]+\s+)*(?:business|shop|store|company|firm|restaurant|cafe|bakery|salon)\b",
    r"\b(?:[a-z0-9_\-]+\s+)*(?:business|shop|store|company)\s+(?:start|open|run|launch|set\s*up)\b",
    r"\b(cake|bakery|restaurant|food|catering|cafe|diner|bistro|liquor|tavern|bar|auto\s+repair|garage|spa|massage|daycare|childcare|preschool|valet|parking|tobacco|smoke\s+shop|vape|hotel|clothing|tailoring|boutique|electronics|convenience|grocery)\s+(?:business|shop|store|service)\b",
    r"\b(bacp|small\s+business\s+center|business\s+affairs)\b",
    r"\b(1006|1010|1011|1002|1004|1005|1012|1014|1016|1020|1030|1050|1075|1329|1476|1625|1781|4405|7035)\b",
    r"\b(license\s+services?|all\s+licenses?|all\s+business\s+licenses?|business\s+license\s+types?)\b",
]

# 16. Licensing Regulatory Actions (Supported when referring to licenses/permits/city procedures)
_LICENSING_ACTION_PATTERNS = [
    r"\b(how\s+do\s+i\s+apply\s+for\s+(?:a\s+)?licen[sc]e|apply\s+for\s+(?:a\s+)?(?:business\s+)?licen[sc]e)\b",
    r"\b(what\s+licen[sc]e\s+do\s+i\s+need|which\s+licen[sc]e\s+do\s+i\s+need|what\s+type\s+of\s+licen[sc]e)\b",
    r"\b(licen[sc]e\s+fee|fee\s+for\s+licen[sc]e|cost\s+of\s+licen[sc]e|how\s+much\s+is\s+(?:the\s+)?licen[sc]e)\b",
    r"\b(documents?\s+required\s+for\s+licen[sc]e|licen[sc]e\s+requirements|eligibility\s+for\s+licen[sc]e)\b",
    r"\b(renew\s+(?:my\s+)?licen[sc]e|licen[sc]e\s+renewal|expiration\s+of\s+licen[sc]e)\b",
    r"\b(how\s+much\s+is\s+it|how\s+much|how\s+much\s+to\s+pay|what\s+documents\s+for\s+this|what\s+is\s+the\s+eligibility|how\s+do\s+i\s+apply)\b",
    r"\b(business\s+start\s+panna|shop\s+open\s+panna|enna\s+licen[sc]e\s+venum|licen[sc]e\s+eppidi\s+apply)\b",
    r"(வணிக உரிமம்|உரிமம் பெற|விண்ணப்பிப்பது எப்படி|கட்டணம் எவ்வளவு)",
    r"(ව්‍යාපාර බලපත්‍රය|බලපත්‍ර අයදුම්)",
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

    lower = query.lower().strip()

    # ── 1. Check Specific Known Unsupported Domains ───────────────────────────
    # Driver License (protect against vehicle/drive confusion)
    for pattern in _DRIVER_LICENSE_PATTERNS:
        if re.search(pattern, lower, re.I):
            if not re.search(r"\b(open\s+an?\s+auto|start\s+an?\s+auto|repair\s+business|garage\s+business|dealership)\b", lower):
                return Domain.DRIVER_LICENSE

    # Aviation
    for pattern in _AVIATION_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.AVIATION

    # Vehicle Registration
    for pattern in _VEHICLE_REGISTRATION_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.VEHICLE_REGISTRATION

    # Tax
    for pattern in _TAX_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.TAX

    # Health
    for pattern in _HEALTH_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.HEALTH

    # Education
    for pattern in _EDUCATION_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.EDUCATION

    # Space
    for pattern in _SPACE_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.OTHER

    # ── 2. Check General Unrelated / Out-of-Domain Categories ───────────────────
    # Sports & Games
    for pattern in _SPORTS_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.OTHER

    # Cooking & Food Recipes
    for pattern in _COOKING_RECIPE_PATTERNS:
        if re.search(pattern, lower, re.I):
            # Verify it's not asking about commercial licensing (e.g., "retail food license to cook biryani")
            if not re.search(r"\b(licen[sc]e|permit|bacp|commercial|retail\s+food|shared\s+kitchen)\b", lower):
                return Domain.OTHER

    # Entertainment & Jokes
    for pattern in _ENTERTAINMENT_JOKES_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.OTHER

    # Consumer Tech & Gadgets
    for pattern in _CONSUMER_TECH_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.OTHER

    # Mathematics, Science, Academics
    for pattern in _MATH_SCIENCE_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.OTHER

    # General Trivia, Weather, Tourism
    for pattern in _GENERAL_TRIVIA_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.OTHER

    # ── 3. Check Supported Government Service & Business Licensing Domains ────
    # Government Service
    for pattern in _GOVERNMENT_SERVICE_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.GOVERNMENT_SERVICE

    # Business License
    for pattern in _BUSINESS_LICENSE_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.BUSINESS_LICENSE

    # Licensing Action / Regulatory Inquiries
    for pattern in _LICENSING_ACTION_PATTERNS:
        if re.search(pattern, lower, re.I):
            return Domain.BUSINESS_LICENSE

    # If query mentions license/permit/fee/renewal/requirements/documents/eligibility/office in a regulatory context
    if any(k in lower for k in (
        "license", "licence", "permit", "fee", "fees", "cost", "price", "pricing",
        "apply", "applying", "application", "renewal", "renew", "renewing", "expire", "expiration",
        "document", "documents", "paperwork", "form", "forms",
        "eligibility", "eligible", "qualify", "requirement", "requirements",
        "procedure", "procedures", "steps",
        "office", "city hall", "bacp", "small business center", "121 n lasalle", "room 800",
        "where", "where to go", "location", "address", "enga", "enga poganum", "epdi", "eppidi",
        "ithukku", "ithoda", "inga",
    )):
        return Domain.BUSINESS_LICENSE

    # If query mentions specific business trades / activities
    if any(k in lower for k in (
        "tailor", "tailoring", "baking", "cake", "bakery", "restaurant", "catering",
        "grocery", "convenience", "salon", "barber", "dry cleaner", "laundromat",
        "mechanic", "plumber", "electrician", "contractor", "retail", "wholesale",
        "peddler", "food truck", "food cart",
    )):
        return Domain.BUSINESS_LICENSE

    # If query mentions specific business startup
    if re.search(r"\b(start|open)\s+(?:a\s+|an\s+)?(?:business|shop|store|firm|company|restaurant|cafe|bakery|salon)\b", lower):
        return Domain.BUSINESS_LICENSE

    # Otherwise, domain is UNKNOWN / unclassified
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
