"""
GovGuide AI — NLP Preprocessor

Cleans and normalizes user queries before retrieval.

Rules:
- Preserves key government service phrases and numerical codes (e.g., '1006', '1010').
- Whitespace and punctuation normalization.
- Tokenization with optional stopword filtering.
- Domain query expansion for common citizen business terms.
"""

import re
from typing import List, Set

_PUNCTUATION_REGEX = re.compile(r"[^\w\s\-\/]")

STOPWORDS: Set[str] = {
    "a", "about", "all", "am", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "being", "both", "but", "by",
    "can", "could", "did", "do", "does", "doing", "down", "during",
    "each", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself",
}

_EXPANSION_RULES = [
    (r"\b(restaurant|restaurants|cafe|cafes|diner|bistro|eatery|coffee shop|bakery)\b", "retail food establishment food"),
    (r"\b(food truck|food cart|mobile vendor)\b", "mobile food vendor peddler"),
    (r"\b(bar|pub|tavern|brewery|alcohol|beer|wine|spirits|cocktails)\b", "consumption on premises liquor alcohol"),
    (r"\b(smoke shop|vape|cigar|cigars|cigarettes|tobacco)\b", "retail tobacco license"),
    (r"\b(daycare|childcare|preschool|nursery)\b", "children services facility childcare"),
    (r"\b(mechanic|auto repair|car repair|garage|body shop)\b", "motor vehicle repair"),
    (r"\b(music venue|concert hall|theater|arcade|bowling|nightclub|amusement)\b", "public place of amusement"),
    (r"\b(shared kitchen|commissary)\b", "shared kitchen user supplemental"),
    (r"\b(massage|spa|masseuse)\b", "massage establishment"),
    (r"\b(general business|store|shop|boutique|consulting|office)\b", "limited business license lbl"),
]


def preprocess(text: str, lowercase: bool = False) -> str:
    """
    Normalize a raw query string.
    - Strips leading/trailing whitespace.
    - Collapses multiple whitespace characters.
    - Preserves case by default for downstream entity recognition, or lowercases if requested.
    """
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    if lowercase:
        text = text.lower()
    return text


def normalize_for_retrieval(text: str) -> str:
    """
    Normalizes a query string for lexical / BM25 search.
    - Strips non-standard punctuation while keeping hyphens and slashes (common in codes like '42-5').
    - Lowercases text.
    - Collapses whitespace.
    """
    if not text:
        return ""
    cleaned = _PUNCTUATION_REGEX.sub(" ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def expand_query(text: str) -> str:
    """
    Applies domain keyword expansions for citizen queries without modifying raw intent.
    """
    if not text:
        return ""
    lower = text.lower()
    added_terms = []
    for pattern, expansion in _EXPANSION_RULES:
        if re.search(pattern, lower):
            added_terms.append(expansion)
    if added_terms:
        return f"{text} {' '.join(added_terms)}"
    return text


def tokenize_query(text: str, remove_stopwords: bool = False) -> List[str]:
    """
    Tokenizes a query string into clean words/tokens.
    """
    if not text:
        return []
    normalized = normalize_for_retrieval(text)
    tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", normalized)
    if remove_stopwords:
        filtered = [t for t in tokens if t not in STOPWORDS]
        return filtered if filtered else tokens
    return tokens
