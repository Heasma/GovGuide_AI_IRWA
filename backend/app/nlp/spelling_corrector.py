"""
GovGuide AI — Typo & Spelling-Mistake Corrector

Deterministic, domain-aware spelling corrector and typo-normalizer.
Handles:
- Direct common government and licensing typos (O(1) exact mapping)
- Edit-distance (Levenshtein / Damerau-Levenshtein) correction for government domain terms
- Preserves numerical license codes (1006, 1010, 42-5), acronyms (LBL, PPA, BACP), and valid words
- Conservative: Never corrupts valid intent or already-correct English terms.
"""

import re
from typing import Dict, List, Optional, Set, Tuple


# ── Direct High-Frequency Typo Mapping Dictionary ────────────────────────────

_DIRECT_TYPO_MAP: Dict[str, str] = {
    # Business
    "bsness": "business",
    "bussiness": "business",
    "busines": "business",
    "buisness": "business",
    "bisness": "business",
    "bizness": "business",
    "bussines": "business",
    "busniss": "business",
    "bsuiness": "business",
    "bussnes": "business",
    "businesse": "business",
    "bissinness": "business",
    "bissiness": "business",
    "bissnes": "business",
    "biz": "business",
    "bizs": "business",

    # License / Licence
    "licenss": "license",
    "lisence": "license",
    "licnse": "license",
    "lisense": "license",
    "licenc": "license",
    "licens": "license",
    "lincese": "license",
    "liscense": "license",
    "licese": "license",
    "licnece": "license",
    "licensce": "license",
    "licence": "license",
    "licenses": "licenses",
    "licnses": "licenses",
    "lisences": "licenses",
    "licences": "licenses",

    # Tailoring / Alterations
    "tailering": "tailoring",
    "tailorng": "tailoring",
    "tailer": "tailor",
    "tailers": "tailors",
    "taileringg": "tailoring",

    # Clothing / Retail / Grocery
    "cloting": "clothing",
    "clothng": "clothing",
    "groceri": "grocery",
    "groceries": "groceries",
    "electrnic": "electronic",
    "electrnics": "electronics",

    # Restaurant / Food / Retail / Cake
    "resturant": "restaurant",
    "restaraunt": "restaurant",
    "restraunt": "restaurant",
    "restarant": "restaurant",
    "restarunt": "restaurant",
    "resturent": "restaurant",
    "restaurent": "restaurant",
    "restraurant": "restaurant",
    "resturants": "restaurants",
    "restaraunts": "restaurants",
    "retaill": "retail",
    "retale": "retail",
    "bakry": "bakery",
    "bakeri": "bakery",
    "bakkery": "bakery",
    "cafee": "cafe",
    "cofee": "coffee",
    "cakee": "cake",

    # Application / Apply
    "aplication": "application",
    "aplicaton": "application",
    "applicaton": "application",
    "applicaion": "application",
    "applicatn": "application",
    "applcation": "application",
    "appliation": "application",
    "aply": "apply",
    "appli": "apply",
    "appliy": "apply",
    "aplying": "apply",
    "appling": "apply",
    "applyng": "apply",

    # Documents / Paperwork
    "documnts": "documents",
    "documets": "documents",
    "documnets": "documents",
    "dokuments": "documents",
    "dokumnts": "documents",
    "docments": "documents",
    "docmnts": "documents",
    "documnt": "document",
    "documet": "document",
    "dokument": "document",
    "paperwrk": "paperwork",
    "paperwrok": "paperwork",

    # Eligibility / Requirements
    "elgibility": "eligibility",
    "eligiblity": "eligibility",
    "elegibility": "eligibility",
    "elgible": "eligible",
    "eligibile": "eligible",
    "eligable": "eligible",
    "requirments": "requirements",
    "requirment": "requirement",
    "reqirements": "requirements",
    "requriements": "requirements",
    "requrements": "requirements",
    "requierment": "requirement",
    "requierments": "requirements",

    # Procedure / Process
    "prosedure": "procedure",
    "prosedur": "procedure",
    "procedur": "procedure",
    "procesure": "procedure",
    "proceedure": "procedure",
    "prosedures": "procedures",
    "procedurs": "procedures",
    "procces": "process",
    "prosess": "process",
    "proces": "process",

    # Fees / Cost / Price
    "feee": "fee",
    "feees": "fees",
    "chargess": "charges",
    "prizing": "pricing",
    "prce": "price",
    "costt": "cost",
    "costss": "costs",
    "paymnt": "payment",
    "paymet": "payment",

    # Renewal
    "reneval": "renewal",
    "renwal": "renewal",
    "reneew": "renew",
    "reneww": "renew",
    "experation": "expiration",
    "expiraion": "expiration",
    "expir": "expire",
    "bienial": "biennial",

    # Office / Location / Address
    "adress": "address",
    "addres": "address",
    "locashun": "location",
    "locatin": "location",
    "locaton": "location",
    "offise": "office",
    "offce": "office",
    "ofice": "office",
    "offices": "offices",
    "chechago": "chicago",
    "chigago": "chicago",
    "chicgo": "chicago",
    "chicagoo": "chicago",
    "chocago": "chicago",

    # Other Services
    "tavernn": "tavern",
    "liqr": "liquor",
    "liquir": "liquor",
    "liquer": "liquor",
    "liqour": "liquor",
    "tobacoo": "tobacco",
    "tobbaco": "tobacco",
    "cigarete": "cigarette",
    "cigarets": "cigarettes",
    "cigarrette": "cigarette",
    "daycarr": "daycare",
    "childcarr": "childcare",
    "ammusement": "amusement",
    "amusment": "amusement",
    "entertaiment": "entertainment",
    "vechicle": "vehicle",
    "vehical": "vehicle",
    "vehcle": "vehicle",
    "massaj": "massage",
    "masage": "massage",
    "comisary": "commissary",
    "commisary": "commissary",

    # Abbreviations and Short Forms
    "biz": "business",
    "lic": "license",
    "docs": "documents",
    "doc": "document",
    "reqs": "requirements",
    "req": "requirement",
    "proc": "procedure",
}

# ── Domain Lexicon for Edit-Distance Verification ────────────────────────────

_DOMAIN_LEXICON: Set[str] = {
    # Core nouns & verbs
    "business", "license", "licenses", "licensing", "permit", "permits",
    "commercial", "application", "applications", "apply", "applying",
    "requirement", "requirements", "document", "documents", "paperwork",
    "form", "forms", "eligibility", "eligible", "procedure", "procedures",
    "process", "steps", "fee", "fees", "cost", "costs", "price", "pricing",
    "charge", "charges", "payment", "renewal", "renew", "renewing", "renewals",
    "expiration", "expire", "expires", "validity", "valid", "biennial",
    "office", "offices", "location", "locations", "address", "addresses",
    "department", "contact", "phone", "hours", "chicago", "illinois", "city",
    "hall", "clerk", "zoning", "inspection", "inspections", "affidavit",
    "certificate", "occupancy",

    # Service categories & business entities
    "retail", "food", "establishment", "restaurant", "restaurants", "cafe",
    "cafes", "bakery", "bakeries", "diner", "diners", "bistro", "eatery",
    "coffee", "liquor", "tavern", "taverns", "bar", "bars", "consumption",
    "premises", "beer", "wine", "spirits", "alcohol", "tobacco", "smoke",
    "cigar", "cigars", "cigarette", "cigarettes", "vape", "daycare",
    "childcare", "preschool", "children", "services", "facility", "facilities",
    "amusement", "entertainment", "theater", "theaters", "music", "venue",
    "venues", "massage", "spa", "spas", "vehicle", "vehicles", "motor",
    "repair", "garage", "garages", "body", "mechanic", "shared", "kitchen",
    "kitchens", "commissary", "valet", "parking", "home", "occupation",
    "animal", "care", "pet", "pets", "hotel", "hotels", "bed", "breakfast",
    "peddler", "vendor", "vendors", "mobile", "tailoring", "tailor", "tailors",
    "clothing", "clothes", "apparel", "grocery", "groceries", "electronics",
    "mobile", "phone", "phones", "cake", "cakes", "baking", "bake", "cupcake",
    "shop", "shops", "store", "stores", "outlet", "outlets", "boutique",
    "market", "supermarket", "company", "setup", "firm", "agency", "dress",
    "dresses", "garment", "garments", "textile", "textiles", "hardware",
    "furniture", "stationery", "jewelry", "salon", "barber", "beauty", "hair",
    "sewing", "stitch", "stitching", "alteration", "alterations",

    # Common English functional words
    "how", "what", "where", "when", "which", "who", "why", "much", "many",
    "can", "could", "should", "would", "do", "did", "is", "are",
    "was", "were", "obtain", "get", "getting", "need", "needed", "needs",
    "require", "required", "start", "starting", "open", "opening", "register",
    "registration", "find", "tell", "give", "show", "help", "information",
    "details", "about", "for", "from", "with", "without", "online", "person",
}

# Acronyms and short preserved tokens
_PRESERVED_ACRONYMS: Set[str] = {
    "lbl", "ppa", "bacp", "cdph", "dob", "sbc", "cpd", "cfd",
    "id", "ids", "faq", "us", "usa", "il", "st", "ave", "rd",
}


def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Damerau-Levenshtein distance (insertions, deletions, substitutions, transpositions)."""
    d = {}
    len1 = len(s1)
    len2 = len(s2)
    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len1):
        for j in range(len2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,        # deletion
                d[(i, j - 1)] + 1,        # insertion
                d[(i - 1, j - 1)] + cost,  # substitution
            )
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + 1)  # transposition

    return d[(len1 - 1, len2 - 1)]


def correct_token(token: str) -> Tuple[str, bool]:
    """
    Corrects a single token against the dictionary and domain vocabulary.
    Returns: (corrected_token, was_changed)
    """
    lower = token.lower()

    # 1. Preserve numbers, codes, short tokens, and acronyms
    if re.match(r"^\d+(-\w+)?$", token):
        return token, False
    if lower in _PRESERVED_ACRONYMS or len(token) <= 2:
        return token, False

    # 2. Check direct high-frequency typo dictionary (O(1))
    if lower in _DIRECT_TYPO_MAP:
        corrected = _DIRECT_TYPO_MAP[lower]
        # Preserve capitalization style if original was capitalized
        if token.istitle():
            corrected = corrected.capitalize()
        elif token.isupper():
            corrected = corrected.upper()
        return corrected, True

    # 3. If token is already in domain lexicon or standard valid word, keep it
    if lower in _DOMAIN_LEXICON:
        return token, False

    # 4. Fuzzy distance matching against domain vocabulary
    # Only check if length >= 4 and not obviously unrelated
    if len(lower) >= 4:
        best_candidate = None
        best_dist = 999
        max_allowed_dist = 1 if len(lower) <= 5 else 2

        for word in _DOMAIN_LEXICON:
            # First character MUST match to prevent converting unrelated words (e.g. mining -> zoning)
            if word[0] != lower[0]:
                continue
            if abs(len(word) - len(lower)) > max_allowed_dist:
                continue
            dist = damerau_levenshtein_distance(lower, word)
            if dist <= max_allowed_dist and dist < best_dist:
                best_dist = dist
                best_candidate = word

        if best_candidate and best_dist <= max_allowed_dist:
            corrected = best_candidate
            if token.istitle():
                corrected = corrected.capitalize()
            elif token.isupper():
                corrected = corrected.upper()
            return corrected, True

    return token, False


def correct_spelling(text: str) -> Tuple[str, List[str]]:
    """
    Corrects spelling and typos in a natural-language query string.
    Returns: (corrected_text, list_of_applied_corrections)
    """
    if not text:
        return "", []

    tokens = re.findall(r"\b[\w\-\/]+\b|[^\w\s]", text)
    corrected_tokens = []
    corrections_applied = []

    for token in tokens:
        if re.match(r"^[\w\-]+$", token):
            corr, changed = correct_token(token)
            if changed:
                corrections_applied.append(f"'{token}' -> '{corr}'")
            corrected_tokens.append(corr)
        else:
            corrected_tokens.append(token)

    # Reconstruct text cleanly
    result = " ".join(corrected_tokens)
    # Fix punctuation spacing
    result = re.sub(r"\s+([?.!,;:])", r"\1", result)
    result = re.sub(r"\s+", " ", result).strip()

    return result, corrections_applied
