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
    Intent.SERVICE_LOOKUP: [
        "what license do i need for", "what license do i need", "which license is required", "what license",
        "which license", "license for", "types of licenses",
        "what is a", "what is the", "tell me about", "information about", "find service",
        "look up", "search for", "business license", "retail food",
    ],
}

_INTENT_REGEX_MAP: List[Tuple[Intent, str]] = [
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
        r"\b(what\s+license\s+do\s+i\s+need|which\s+license\s+(?:is\s+)?required|what\s+license|which\s+license|license\s+for|types\s+of\s+licenses|what\s+permit\s+do\s+i\s+need|which\s+permit|what\s+permit|what\s+license\s+is\s+needed|what\s+type\s+of\s+license|what\s+kind\s+of\s+license|what\s+license\s+applies)\b"
    ),
    (
        Intent.FEES,
        r"\b(fees?\s+for|how\s+much\s+(?:is|does|do|to)|cost\s+of|fee\s+schedule|pricing|payment|pay|\$|\bfees?\b|\bcost\b|\bprice\b|\bcharges?\b)\b"
    ),
    (
        Intent.REQUIRED_DOCUMENTS,
        r"\b(what\s+documents|what\s+paperwork|what\s+papers|required\s+documents?|documents?\s+(?:are\s+)?required|documents?\s+(?:are\s+)?needed|paperwork\s+required|documents?\s+checklist|what\s+do\s+i\s+need\s+to\s+bring|\bdocuments?\b|\bpaperwork\b|\bforms?\b|\bidentification\b|\bid\s+proof\b|\blease\b|\baffidavit\b|\bcertificate\s+of\s+occupancy\b|\bzoning\s+certificate\b|\bfloor\s+plan\b|\binspection\s+report\b)\b"
    ),
    (
        Intent.APPLICATION_PROCEDURE,
        r"\b(how\s+(?:can|do)\s+i\s+apply|how\s+to\s+apply|how\s+(?:can|do)\s+i\s+get|how\s+to\s+get|what\s+are\s+the\s+steps|steps\s+to\s+apply|steps\s+for\s+application|steps\s+to|process\s+for|application\s+procedure|application\s+process|where\s+do\s+i\s+submit|online\s+application|chicago\s+business\s+direct|walk-in|in\s+person\s+application)\b"
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
        r"\b(where\s+is\s+the\s+office|where\s+is\s+city\s+hall|office\s+address|office\s+hours|phone\s+number|small\s+business\s+center|city\s+hall|room\s+800|bacp\s+office|department\s+location|who\s+to\s+call|contact\s+information|\boffice\b|\blocation\b|\baddress\b|where\s+is|\bhours\b|\bcontact\b)\b"
    ),
]

_CONVERSATION_TYPE_PATTERNS = [
    ("GOODBYE", [
        r"\b(thank\s+you,?\s*goodbye|thanks,?\s*goodbye|thank\s+you\s+and\s+goodbye|goodbye|bye\s+bye|bye|see\s+you|have\s+a\s+(?:great|good|nice)\s+day|farewell)\b"
    ]),
    ("THANKS", [
        r"\b(thank\s+you\s+for\s+(?:your\s+|the\s+)?information|thanks\s+for\s+(?:your\s+|the\s+)?information|thank\s+you\s+for\s+(?:your\s+|the\s+)?help|thanks\s+for\s+(?:your\s+|the\s+)?help|great,?\s*thank\s+you|great,?\s*thanks|thank\s+you\s+so\s+much|thanks\s+so\s+much|many\s+thanks|thank\s+you\s+very\s+much|i\s+appreciate\s+(?:your\s+)?help|i\s+appreciate\s+it|appreciate\s+it|much\s+appreciated|thank\s+you|thanks)\b"
    ]),
    ("ACKNOWLEDGEMENT", [
        r"\b(you(?:'re|\s+are|\s+re)?\s+welcome|your\s+welcome|happy\s+to\s+help|no\s+problem|my\s+pleasure|don't\s+mention\s+it|okay,?\s*got\s+it|ok,?\s*got\s+it|thanks,?\s*got\s+it|thank\s+you,?\s*got\s+it|got\s+it,?\s*thanks|got\s+it,?\s*thank\s+you|that'?s\s+(?:very\s+)?helpful|that\s+is\s+(?:very\s+)?helpful|this\s+is\s+(?:very\s+)?helpful|got\s+it|understood|alright|all\s+right|okay|ok|makes\s+sense|perfect|sounds\s+good|cool)\b"
    ]),
    ("GREETING", [
        r"^(hi|hello|hey|good\s+(morning|afternoon|evening)|greetings|hi\s+there|hello\s+there|howdy)[!.]*$"
    ]),
]

_SUBSTANTIVE_QUESTION_PATTERNS = [
    r"\b(what\s+license|which\s+license|license\s+for|how\s+much|cost|fee|fees|price|pay|pricing)\b",
    r"\b(document|documents|paperwork|form|forms|id\s+proof|lease|affidavit)\b",
    r"\b(how\s+(?:can|do)\s+i\s+apply|how\s+to\s+apply|steps\s+to|application\s+process|procedure)\b",
    r"\b(who\s+is\s+eligible|who\s+can\s+apply|am\s+i\s+eligible|do\s+i\s+qualify|criteria|qualifications)\b",
    r"\b(renew|renewal|validity|expire|expiration)\b",
    r"\b(where\s+is\s+the\s+office|city\s+hall|small\s+business\s+center|hours|phone)\b",
    r"\b(difference\s+between|compare|comparison|versus|vs)\b",
    r"\b(sri\s+lanka|abroad|outside\s+the\s+us|remotely|foreign\s+national|international\s+applicant)\b",
]


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

    conv_type = classify_conversation_type(query)
    if not conv_type:
        return False

    lower = query.lower().strip()
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


