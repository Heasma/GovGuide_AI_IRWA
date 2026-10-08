"""
GovGuide AI — Abbreviation & Informal Expression Expander

Expands informal abbreviations, colloquialisms, and common short-forms:
- Domain acronyms: LBL, PPA, BACP, CDPH, DOB, SBC
- General abbreviations: biz, lic, docs, reqs, proc, app, loc, info
- Informal speech: wanna, gimme, plz, pls, u, gotta
"""

import re
from typing import Dict, List, Tuple

_EXACT_ABBREVIATION_MAP: Dict[str, str] = {
    "lbl": "limited business license",
    "ppa": "public place of amusement",
    "bacp": "department of business affairs and consumer protection",
    "cdph": "chicago department of public health",
    "dob": "department of buildings",
    "sbc": "small business center",
    "cpd": "chicago police department",
    "cfd": "chicago fire department",
    "docs": "documents",
    "doc": "document",
    "reqs": "requirements",
    "req": "requirement",
    "proc": "procedure",
    "loc": "location",
    "info": "information",
    "addr": "address",
    "ph": "phone",
    "tel": "telephone",
    "faq": "frequently asked questions",
}

_INFORMAL_PHRASE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # Compound phrases
    (re.compile(r"\bbiz\s+lic(?:en[sc]e)?\b", re.I), "business license"),
    (re.compile(r"\bbiz\b", re.I), "business"),
    (re.compile(r"\bb&b\b", re.I), "bed and breakfast"),
    (re.compile(r"\bb\s*\/\s*w\b", re.I), "between"),
    (re.compile(r"\bwanna\b", re.I), "want to"),
    (re.compile(r"\bgimme\b", re.I), "give me"),
    (re.compile(r"\bgotta\b", re.I), "have to"),
    (re.compile(r"\b(plz|pls)\b", re.I), "please"),
    (re.compile(r"\b(u)\b", re.I), "you"),
    (re.compile(r"\b(ur)\b", re.I), "your"),
    (re.compile(r"\bhow\s+to\s+grab\b", re.I), "how to get"),
    (re.compile(r"\bhow\s+can\s+i\s+grab\b", re.I), "how can i get"),
    (re.compile(r"\bhow\s+do\s+i\s+grab\b", re.I), "how do i get"),
    (re.compile(r"\bwhere\s+can\s+i\s+grab\b", re.I), "where can i get"),
    (re.compile(r"\bwhere\s+do\s+i\s+grab\b", re.I), "where do i get"),
]


def expand_abbreviations(text: str) -> Tuple[str, List[str]]:
    """
    Expands abbreviations and informal phrases into standard terms.
    Returns: (expanded_text, list_of_expansions)
    """
    if not text:
        return "", []

    working = text
    expansions_applied = []

    # 1. Apply phrase-level patterns
    for pattern, replacement in _INFORMAL_PHRASE_PATTERNS:
        if pattern.search(working):
            match_str = pattern.search(working).group(0)
            working = pattern.sub(replacement, working)
            expansions_applied.append(f"'{match_str}' -> '{replacement}'")

    # 2. Apply token-level abbreviations
    tokens = re.findall(r"\b[\w\-]+\b|[^\w\s]", working)
    new_tokens = []
    for token in tokens:
        lower = token.lower()
        if lower in _EXACT_ABBREVIATION_MAP:
            replacement = _EXACT_ABBREVIATION_MAP[lower]
            new_tokens.append(replacement)
            expansions_applied.append(f"'{token}' -> '{replacement}'")
        else:
            new_tokens.append(token)

    result = " ".join(new_tokens)
    result = re.sub(r"\s+([?.!,;:])", r"\1", result)
    result = re.sub(r"\s+", " ", result).strip()

    return result, expansions_applied
