"""
GovGuide AI — NLP Preprocessor
Cleans and normalizes user queries before retrieval.
Phase 1: Basic cleaning. Phase 2: Language detection, domain-specific normalization.
"""

import re


def preprocess(text: str) -> str:
    """
    Normalize a raw query string.
    Phase 1: Strip, lowercase, collapse whitespace.
    Phase 2: Add stopword removal, stemming, domain normalization.
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    # Note: do NOT lowercase here for NER accuracy — done at retrieval stage
    return text
