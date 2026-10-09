"""
GovGuide AI — Intent Classifier

Classifies user query intent into domain categories:
- service_information / service_lookup: Inquiries about service details, descriptions, requirements
- eligibility: Questions regarding eligibility criteria, qualification, restrictions
- required_documents: Inquiries about forms, IDs, certifications, paperwork
- application_procedure / procedure: Step-by-step application guidance, how to apply
- fees: Fee schedules, pricing, cost of licenses, payments
- renewal: License renewal cycles, expiration, renewal procedures
- office_information: Department locations, hours, phone numbers, contacts
- general: Broad conversational greetings or general queries
- unknown: Ambiguous or unclassified requests
"""

import re
from typing import Dict, List, Optional, Tuple
from app.orchestrator.message_schema import Intent

# Categorized keyword and phrase patterns ordered by specificity
_INTENT_PATTERNS: Dict[Intent, List[str]] = {
    Intent.COMPARISON: [
        "difference between", "differences between", "differ between",
        "compare", "comparison", "versus", "vs", "differ from",
        "difference in", "which is better", "should i get", "or should i get",
    ],
    Intent.SOURCE_EVIDENCE: [
        "what official source", "where did this information come from",
        "where did this come from", "source of this", "official source",
        "legal reference", "municipal code", "mcc chapter", "supporting evidence",
        "official evidence", "source documents", "source citation", "citation",
        "legal basis", "what law", "governing law", "ordinance",
    ],
    Intent.FEES: [
        "fees for", "fee for", "how much is", "how much does", "cost of",
        "fee schedule", "how much do i need to pay", "how much to pay",
        "fee", "fees", "cost", "how much", "price", "payment", "pay",
        "dollar", "dollars", "pricing", "charge", "charges", "$",
    ],
    Intent.REQUIRED_DOCUMENTS: [
        "what documents do i need", "what paperwork is required", "what documents",
        "what papers", "required documents", "what do i need to bring", "paperwork required",
        "document", "documents", "paperwork", "form", "forms",
        "identification", "id proof", "lease", "affidavit", "certificate of occupancy",
        "zoning certificate", "floor plan", "inspection report",
    ],
    Intent.APPLICATION_PROCEDURE: [
        "how can i apply", "how do i apply", "how to apply", "how can i get", "how to get",
        "how do i get", "what are the steps", "steps to apply", "steps for application",
        "steps to", "process for", "application procedure", "procedure",
        "application process", "steps for", "where do i submit", "online application",
        "chicago business direct", "walk-in", "in person application",
    ],
    Intent.GEOGRAPHIC_ELIGIBILITY: [
        "currently in sri lanka", "in sri lanka", "from sri lanka", "living in sri lanka",
        "living outside", "from abroad", "outside the us", "outside the united states",
        "foreign national", "foreign citizen", "apply remotely", "apply from abroad",
        "apply from another country", "international applicant", "non-resident",
        "living in canada", "living in india", "living in the uk", "living in",
        "from another country", "outside chicago", "out of country",
    ],
    Intent.ELIGIBILITY: [
        "am i eligible", "do i qualify", "who can apply", "who is eligible",
        "eligibility criteria", "eligibility requirements", "qualify for",
        "can i apply", "eligibility", "requirements", "criteria", "qualifications",
        "age requirement", "restrictions", "disqualified",
    ],
    Intent.RENEWAL: [
        "how often do i renew", "how often to renew", "how to renew", "renewal process", "renewal fee",
        "how long is it valid", "how long is", "how long valid",
        "renew", "renewal", "renewing", "expire", "expiration", "validity",
        "biennial", "annual renewal", "re-apply",
    ],
    Intent.OFFICE_INFORMATION: [
        "where is the office", "where is city hall", "office address", "office hours",
        "phone number", "small business center", "city hall", "room 800",
        "bacp office", "department location", "who to call", "contact information",
        "office", "location", "address", "where is", "hours", "contact",
    ],
    Intent.LICENSE_CATALOG: [
        "what business licenses are available", "what business licences are available",
        "what licenses are available", "what licences are available",
        "available business licenses", "available business licences",
        "available licenses", "available licences",
        "show me all available business licenses", "show me all available business licences",
        "show all available business licenses", "show all available business licences",
        "show me available business licenses", "show me available business licences",
        "show available business licenses", "show available business licences",
        "what licenses can i apply for", "what licences can i apply for",
        "what business license options do you have", "what business licence options do you have",
        "what business license options", "what business licence options",
        "what licensing options are available", "list all business licenses", "list all business licences",
        "list of business licenses", "list of business licences",
        "all business licenses", "all business licences",
        "catalog of licenses", "catalog of licences",
        "license catalog", "licence catalog",
        "available government services", "what services are available",
        "all available licenses", "all available licences",
        "what business licenses can i apply for here", "what business licences can i apply for here",
        "what business licenses are available here", "what business licences are available here",
        "all government services", "all 56 government services",
        "56 government service summary", "56 government services summary",
        "government service summary", "government services summary",
        "list all government services", "list of all government services",
        "show all 56 services", "show all 56 government services",
        "show all services", "show all government services",
        "business license services summary", "all business license services",
        "all license summary", "all business license types",
        "give me summary of all government services",
        "summary of all government services", "summary of 56 government services",
        "i need 56 government service summary", "i need 56 government services summary",
        "i need government service summary", "i need government services summary",
        "enna enna government services irukku", "56 services summary venum",
        "56 government service oda summary venum", "56 government services summary venum",
        "enna enna business license inga edukkalam", "enna enna business licence inga edukkalam",
        "enna enna business license inga edulkkalam", "enna enna business licence inga edulkkalam",
        "enna enna license inga edukkalam", "enna enna licence inga edukkalam",
        "inga enna enna business license irukku", "inga enna enna business licence irukku",
        "enna enna business license", "enna enna business licence",
        "enna enna license", "enna enna licence",
        "ella licnce pathium summary venum", "ella licence pathium summary venum",
        "ella license pathium summary venum", "ennaku ella licnce pathium summary venum",
        "ennaku ella licence pathium summary venum", "ennaku ella license pathium summary venum",
        "ella license summary venum", "ella licence summary venum",
        "give me summary of all business licenses", "i need a summary of all business licenses",
        "summary of all business licenses", "summary of all business licences",
        "all business licenses summary", "all business licences summary",
    ],
    Intent.SERVICE_LOOKUP: [
        "what is license", "what is licence", "what is service", "what is code",
        "tell me about", "information about", "details for", "details about",
        "service details", "license details", "licence details", "service information",
        "what license do i need for", "what licence do i need for",
        "what license do i need", "what licence do i need",
        "which license is required", "which licence is required",
        "what license", "what licence", "which license", "which licence",
        "license for", "licence for", "types of licenses", "types of licences",
        "what is a", "what is the", "find service",
        "look up", "search for", "business license", "business licence", "retail food",
        "pathi sollunga", "details venum", "service details venum",
    ],
}

_INTENT_REGEX_MAP: List[Tuple[Intent, str]] = [
    (
        Intent.LICENSE_CATALOG,
        r"\b("
        r"what\s+(?:business\s+)?licen[cs]es?\s+(?:are\s+)?available|"
        r"what\s+(?:business\s+)?licen[cs]es?\s+can\s+i\s+(?:apply\s+for|get|obtain)|"
        r"show\s+(?:me\s+)?(?:all\s+)?available\s+(?:business\s+)?licen[cs]es?|"
        r"what\s+(?:business\s+)?licensing\s+options|"
        r"what\s+(?:business\s+)?licen[cs]e\s+options|"
        r"list\s+(?:all\s+)?(?:business\s+)?(?:licen[cs]es?|government\s+services?|services?)|"
        r"list\s+of\s+(?:all\s+)?(?:business\s+)?(?:licen[cs]es?|government\s+services?|services?)|"
        r"all\s+available\s+(?:business\s+)?(?:licen[cs]es?|government\s+services?|services?)|"
        r"available\s+(?:business\s+)?(?:licen[cs]es?|government\s+services?|services?)|"
        r"what\s+(?:government\s+)?services\s+are\s+available|"
        r"available\s+services|"
        r"what\s+licen[cs]es?\s+do\s+you\s+(?:have|support|offer)|"
        r"what\s+are\s+(?:the\s+)?available\s+(?:business\s+)?licen[cs]es?|"
        r"what\s+business\s+licen[cs]es?\s+(?:can\s+i\s+apply\s+for\s+here|are\s+available\s+here)|"
        r"(?:i\s+need\s+)?(?:a\s+)?summary\s+of\s+(?:all\s+)?(?:56\s+)?(?:government\s+|business\s+)?(?:services?|licen[cs]es?)|"
        r"(?:i\s+need\s+)?(?:all\s+)?(?:56\s+)?(?:government\s+|business\s+)?(?:services?|licen[cs]es?)\s+(?:summary|options|catalog|list|overview)|"
        r"(?:give\s+me\s+)?(?:a\s+)?summary\s+of\s+(?:all\s+)?(?:56\s+)?(?:government\s+|business\s+)?(?:services?|licen[cs]es?)|"
        r"show\s+(?:me\s+)?(?:all\s+)?(?:56\s+)?(?:government\s+|business\s+)?(?:services?|licen[cs]es?)|"
        r"all\s+(?:56\s+)?(?:government\s+|business\s+)?(?:services?|licen[cs]es?)(?:\s+types|\s+summary|\s+services|\s+pathium)?|"
        r"all\s+(?:business\s+)?licen[cs]e\s+types|"
        r"(?:(?:ennaku|enakku|enaku)\s+)?(?:ella|ellam|yella|yellam)\s+(?:business\s+|government\s+)?(?:licen[cs]e|licnce|services?)(?:s)?(?:\s+(?:pathium|pathiyum|pathina|pathi|oda))?\s+summary(?:\s+(?:venum|vendum|kudunga|theva|thevai))?|"
        r"(?:(?:inga|ingga|inge|ingey)\s+)?(?:enna+\s*[-]?\s*enna+|enna+enna+|yena+\s*[-]?\s*yena+|yena+yena+)\s+(?:business\s+|government\s+)?(?:licen[cs]e|services?)|"
        r"(?:inga|ingga|inge|ingey)\s+(?:enna+|yena+)\s+(?:business\s+|government\s+)?(?:licen[cs]e|services?)"
        r")\b"
    ),
    (
        Intent.GEOGRAPHIC_ELIGIBILITY,
        r"\b(currently\s+in\s+sri\s+lanka|in\s+sri\s+lanka|from\s+sri\s+lanka|living\s+in\s+sri\s+lanka|living\s+outside|from\s+abroad|outside\s+the\s+(?:us|united\s+states)|foreign\s+national|foreign\s+citizen|apply\s+remotely|apply\s+from\s+abroad|apply\s+from\s+another\s+country|international\s+applicant|non-resident|living\s+in\s+canada|living\s+in\s+india|living\s+in\s+the\s+uk|out\s+of\s+country)\b"
    ),
    (
        Intent.COMPARISON,
        r"\b(differences?\s+between|differ\s+between|compare|comparison|versus|\bvs\b|differ\s+from|difference\s+in|which\s+is\s+better|should\s+i\s+get\s+.+\s+or)\b"
    ),
    (
        Intent.SOURCE_EVIDENCE,
        r"\b(what\s+official\s+source|where\s+did\s+this\s+information\s+come\s+from|where\s+did\s+this\s+come\s+from|source\s+of\s+this|official\s+source|legal\s+reference|municipal\s+code|\bmcc\b|supporting\s+evidence|official\s+evidence|source\s+documents|source\s+citation|citation|legal\s+basis|what\s+law|governing\s+law|ordinance)\b"
    ),
    (
        Intent.SERVICE_LOOKUP,
        r"\b("
        r"what\s+is\s+(?:the\s+)?(?:business\s+)?licen[cs]e(?:\s+code)?\s*[0-9]{4}|"
        r"what\s+is\s+licen[cs]e\s*[0-9]{4}|"
        r"what\s+is\s+service\s*[0-9]{4}|"
        r"tell\s+me\s+about|"
        r"information\s+about|"
        r"details\s+(?:for|about|of)|"
        r"what\s+licenses?\s+do\s+i\s+need|"
        r"which\s+licenses?\s+(?:is\s+)?required|"
        r"what\s+licenses?|which\s+licenses?|licenses?\s+for|types\s+of\s+licenses|"
        r"what\s+permits?\s+do\s+i\s+need|which\s+permits?|what\s+permits?|"
        r"what\s+licenses?\s+is\s+needed|what\s+type\s+of\s+licenses?|what\s+kind\s+of\s+licenses?|"
        r"what\s+licenses?\s+applies|"
        r"which\s+licenses?\s+(?:is\s+)?(?:perfect|suitable|best|needed|required|right|good)\s+for\s+me|"
        r"which\s+licenses?\s+(?:do\s+i\s+need|should\s+i\s+get)|"
        r"start\s+(?:a\s+)?(?:new\s+)?(?:food\s+|restaurant\s+|retail\s+)?business|"
        r"open\s+(?:a\s+)?(?:new\s+)?(?:food\s+|restaurant\s+|retail\s+)?business|"
        r"(?:pathi|pathina)\s+(?:sollunga|solla)|"
        r"service\s+details\s+(?:venum|vendum|theva|thevai|kudunga)"
        r")\b"
    ),
    (
        Intent.FEES,
        r"\b(fees?\s+for|how\s+much|cost\s+of|fee\s+schedule|pricing|payment|pay|\$|\bfees?\b|\bcost\b|\bprice\b|\bcharges?\b)\b"
    ),
    (
        Intent.REQUIRED_DOCUMENTS,
        r"\b(what\s+documents|what\s+paperwork|what\s+papers|required\s+documents?|documents?\s+(?:are\s+)?required|documents?\s+(?:are\s+)?needed|paperwork\s+required|documents?\s+checklist|what\s+do\s+i\s+need\s+to\s+bring|\bdocuments?\b|\bpaperwork\b|\bforms?\b|\bidentification\b|\bid\s+proof\b|\blease\b|\baffidavit\b|\bcertificate\s+of\s+occupancy\b|\bzoning\s+certificate\b|\bfloor\s+plan\b|\binspection\s+report\b|\brequirements?\b)\b"
    ),
    (
        Intent.APPLICATION_PROCEDURE,
        r"\b(how\s+(?:can|do)\s+i\s+apply|how\s+to\s+apply|how\s+(?:can|do)\s+i\s+get|how\s+to\s+get|how\s+(?:can|do)\s+i\s+obtain|how\s+to\s+obtain|how\s+(?:can|do)\s+i\s+acquire|what\s+are\s+the\s+steps|steps\s+to\s+apply|steps\s+for\s+application|steps\s+to|process\s+for|application\s+procedure|application\s+process|what\s+is\s+the\s+procedure|procedure\s+for|procedure\s+to|\bprocedures?\b|where\s+do\s+i\s+submit|online\s+application|chicago\s+business\s+direct|walk-in|in\s+person\s+application)\b"
    ),
    (
        Intent.RENEWAL,
        r"\b(how\s+often\s+(?:do\s+i\s+need\s+to\s+)?renew|how\s+often\s+to\s+renew|how\s+to\s+renew|renewal\s+process|renewal\s+fee|how\s+long\s+is\s+it\s+valid|how\s+long\s+is|how\s+long\s+valid|\brenew\b|\brenewal\b|\brenewing\b|\bexpire\b|\bexpiration\b|\bvalidity\b|\bbiennial\b|\bannual\s+renewal\b|\bre-apply\b)\b"
    ),
    (
        Intent.ELIGIBILITY,
        r"\b(am\s+i\s+eligible|do\s+i\s+qualify|who\s+can\s+apply|who\s+is\s+eligible|eligibility\s+criteria|eligibility\s+requirements|qualify\s+for|can\s+i\s+apply|\beligibility\b|\bqualifications?\b|\brestrictions?\b|\bdisqualified\b)\b"
    ),
    (
        Intent.OFFICE_INFORMATION,
        r"\b(where\s+is\s+the\s+office|where\s+is\s+city\s+hall|where\s+(?:should|can|do)\s+i\s+go|where\s+to\s+go|where\s+should\s+we\s+go|office\s+address|office\s+hours|phone\s+number|small\s+business\s+center|city\s+hall|room\s+800|bacp\s+office|department\s+location|who\s+to\s+call|contact\s+information|\boffice\b|\blocation\b|\baddress\b|\bwhere\b|\bhours\b|\bcontact\b)\b"
    ),
]

_CONVERSATION_TYPE_PATTERNS = [
    ("GOODBYE", [
        r"^(thank\s+you,?\s*goodbye|thanks,?\s*goodbye|thank\s+you\s+and\s+goodbye|goodbye|bye\s+bye|bye|see\s+you|have\s+a\s+(?:great|good|nice)\s+day|farewell)[!.]*$"
    ]),
    ("THANKS", [
        r"^(?:ok|okay|seri|sari|alright|all\s+right|great|super)?\s*,?\s*(?:thank\s+you\s+for\s+(?:your\s+|the\s+)?information|thanks\s+for\s+(?:your\s+|the\s+)?information|thank\s+you\s+for\s+(?:your\s+|the\s+)?help|thanks\s+for\s+(?:your\s+|the\s+)?help|great,?\s*thank\s+you|great,?\s*thanks|thank\s+you\s+so\s+much|thanks\s+so\s+much|thanks\s+a\s+lot|thank\s+you\s+a\s+lot|many\s+thanks|thank\s+you\s+very\s+much|i\s+appreciate\s+(?:your\s+)?help|i\s+appreciate\s+it|appreciate\s+it|much\s+appreciated|thank\s+you\s+bro|thanks\s+bro|thank\s+you|thanks|nandri|mikka\s+nandri|sthuthi|bohoma\s+sthuthi)[!.]*$"
    ]),
    ("ACKNOWLEDGEMENT", [
        r"^(you(?:'re|\s+are|\s+re)?\s+welcome|your\s+welcome|happy\s+to\s+help|no\s+problem|my\s+pleasure|don't\s+mention\s+it|okay,?\s*got\s+it|ok,?\s*got\s+it|thanks,?\s*got\s+it|thank\s+you,?\s*got\s+it|got\s+it,?\s*thanks|got\s+it,?\s*thank\s+you|got\s+it|understood|alright|all\s+right|okay|ok|seri|sari|hari|ela|makes\s+sense|perfect|great|super|sounds\s+good|cool)[!.]*$",
        r"\b(you(?:'re|\s+are|\s+re)?\s+welcome|your\s+welcome|happy\s+to\s+help|no\s+problem|my\s+pleasure|don't\s+mention\s+it|that'?s\s+(?:very\s+)?helpful|that\s+is\s+(?:very\s+)?helpful|this\s+is\s+(?:very\s+)?helpful)\b"
    ]),
    ("GREETING", [
        r"^(hi|hello|hey|good\s+(morning|afternoon|evening)|greetings|hi\s+there|hello\s+there|howdy|vanakkam|ayubowan)[!.]*$"
    ]),
]

_SUBSTANTIVE_QUESTION_PATTERNS = [
    r"\b(what\s+licenses?|which\s+licenses?|licenses?\s+for|how\s+much|cost|fee|fees|price|pay|pricing)\b",
    r"\b(document|documents|paperwork|form|forms|id\s+proof|lease|affidavit)\b",
    r"\b(how\s+(?:can|do)\s+i\s+apply|how\s+to\s+apply|steps\s+to|application\s+process|procedure|steps)\b",
    r"\b(who\s+is\s+eligible|who\s+can\s+apply|am\s+i\s+eligible|do\s+i\s+qualify|criteria|qualifications|eligibility)\b",
    r"\b(renew|renewal|validity|expire|expiration)\b",
    r"\b(where\s+is\s+the\s+office|city\s+hall|small\s+business\s+center|hours|phone|where\s+to\s+go|where\s+should\s+i\s+go)\b",
    r"\b(difference\s+between|compare|comparison|versus|vs)\b",
    r"\b(sri\s+lanka|abroad|outside\s+the\s+us|remotely|foreign\s+national|international\s+applicant)\b",
    r"\b(start\s+(?:a\s+)?(?:new\s+)?(?:food\s+|restaurant\s+|retail\s+)?business|open\s+(?:a\s+)?(?:new\s+)?(?:food\s+|restaurant\s+|retail\s+)?business)\b",
    r"\b(food\s+business|restaurant|retail\s+food|business\s+license|licenses?|licences?)\b",
    r"\b(ithukku|ithoda|ithuku|ithula|ennaku|theva|thevai|venum|vendum|kudunga|sollunga|solla|evvalavu|evalavu|epdi|yepdi|enna|yena)\b",
]

_DOMAIN_KEYWORDS_BLOCKING_CONV = re.compile(
    r"\b(license|licenses|licence|licences|business|food|restaurant|permit|permits|"
    r"fee|fees|cost|price|document|documents|paperwork|form|forms|apply|applying|"
    r"application|procedure|steps|eligibility|eligible|renew|renewal|office|address|"
    r"location|hours|phone|start|open|where|how|which|what|who)\b",
    re.I
)


def classify_conversation_type(query: str) -> Optional[str]:
    """
    Identifies the sub-category of a conversational message:
    THANKS | ACKNOWLEDGEMENT | GOODBYE | GREETING | None
    """
    if not query:
        return None

    lower = query.lower().strip()
    for conv_type, patterns in _CONVERSATION_TYPE_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, lower, re.I):
                return conv_type
    return None


def is_conversational_query(query: str) -> bool:
    """
    Returns True if the query is purely conversational (no substantive licensing question).
    """
    if not query:
        return False

    lower = query.lower().strip()

    conv_type = classify_conversation_type(lower)
    if not conv_type:
        return False

    # Check if there is a substantive question embedded
    for pattern in _SUBSTANTIVE_QUESTION_PATTERNS:
        if re.search(pattern, lower, re.I):
            return False

    return True


def classify_intents(query: str) -> List[Intent]:
    """
    Classifies a natural-language query string into one or more matched Intents,
    ordered by their occurrence in the query.

    Args:
        query: Raw or normalized user query string.

    Returns:
        List of matched Intent enum values. Guaranteed non-empty.
    """
    if not query:
        return [Intent.UNKNOWN]

    lower = query.lower().strip()

    # 1. Purely conversational check
    if is_conversational_query(query):
        return [Intent.CONVERSATIONAL]

    # 2. Find all matching substantive intents with their earliest position
    matches: List[Tuple[int, Intent]] = []
    has_geographic = False

    for intent, pattern in _INTENT_REGEX_MAP:
        m = re.search(pattern, lower, re.I)
        if m:
            if intent == Intent.GEOGRAPHIC_ELIGIBILITY:
                has_geographic = True
            matches.append((m.start(), intent))

    if not matches:
        return [Intent.GENERAL]

    # If geographic eligibility is present, remove redundant general eligibility
    if has_geographic:
        matches = [m for m in matches if m[1] != Intent.ELIGIBILITY]

    # Sort matched intents by appearance order in query
    matches.sort(key=lambda item: item[0])
    
    # Deduplicate while preserving order
    ordered_intents: List[Intent] = []
    for _, intent in matches:
        if intent not in ordered_intents:
            ordered_intents.append(intent)

    return ordered_intents if ordered_intents else [Intent.GENERAL]


def classify_intent(query: str) -> Intent:
    """
    Classifies a natural-language query string into the primary matched Intent.

    Args:
        query: Raw or normalized user query string.

    Returns:
        The primary matched Intent enum value.
    """
    intents = classify_intents(query)
    return intents[0]


class IntentClassifier:
    """Convenience wrapper for intent classification."""

    def classify(self, query: str) -> Intent:
        return classify_intent(query)

    def classify_all(self, query: str) -> List[Intent]:
        return classify_intents(query)


