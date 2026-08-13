"""
GovGuide AI — Intent Classifier (Stub)
Classifies user query intent. Phase 1: Rule-based heuristics.
Phase 2: ML classifier trained on real government queries.

IMPORTANT: Intent taxonomy (service_lookup, eligibility, procedure, general)
is preliminary. Final categories depend on the real dataset and query patterns.
"""

from app.orchestrator.message_schema import Intent


# Keyword hints for each intent — preliminary, dataset-dependent
_INTENT_HINTS = {
    Intent.ELIGIBILITY: [
        "am i eligible", "do i qualify", "can i apply", "who can apply",
        "requirements", "criteria", "qualify for",
    ],
    Intent.PROCEDURE: [
        "how to apply", "how do i", "steps to", "process for",
        "procedure", "application process", "what documents",
    ],
    Intent.SERVICE_LOOKUP: [
        "what is", "tell me about", "information about", "find service",
        "look up", "search for",
    ],
}


def classify_intent(query: str) -> Intent:
    """
    Rule-based intent classification.
    Returns the best-matching intent or GENERAL if no pattern matches.

    Phase 2: Replace with a trained classifier.
    """
    lower = query.lower()
    for intent, hints in _INTENT_HINTS.items():
        if any(hint in lower for hint in hints):
            return intent
    return Intent.GENERAL
