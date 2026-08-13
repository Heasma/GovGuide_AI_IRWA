"""
GovGuide AI — Response Validator (Advisory Agent)
Checks that the LLM-generated response is grounded in retrieved evidence.

Phase 1: Heuristic foundation. Not a complete hallucination detector.
Phase 2: Semantic entailment checking against evidence content.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    passed: bool
    attributed_sources: List[dict] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    explanation: str = ""


def validate_response(
    answer: str,
    evidence_bundle: Dict[str, Any],
) -> ValidationResult:
    """
    Validates a generated response against the supplied evidence bundle.

    Phase 1 checks:
    - Is the answer non-empty?
    - Does the evidence bundle have any content?
    - Are any source attributions possible?

    Phase 2: Add semantic entailment scoring.
    """
    results = evidence_bundle.get("results", [])

    # Empty answer
    if not answer or not answer.strip():
        return ValidationResult(
            passed=False,
            caveats=["Response was empty."],
            explanation="LLM returned an empty response.",
        )

    # No evidence was retrieved
    if not results:
        return ValidationResult(
            passed=False,
            caveats=[
                "No evidence was retrieved for this query.",
                "Government dataset integration is pending.",
                "Please consult an official government source directly.",
            ],
            explanation="No evidence in bundle — cannot validate response.",
        )

    # Build source attribution from retrieved results
    attributed_sources = [
        {
            "source_id": r.get("source_id", ""),
            "title": r.get("source_title", "Unknown"),
            "url": r.get("source_url"),
            "excerpt": r.get("content", "")[:200],  # first 200 chars as excerpt
        }
        for r in results[:5]  # top 5 sources
    ]

    caveats = [
        "Always verify important information with the official government source.",
        "This response is based on retrieved documents and may not reflect the most current information.",
    ]

    return ValidationResult(
        passed=True,
        attributed_sources=attributed_sources,
        caveats=caveats,
        explanation="Response generated from retrieved evidence. Semantic validation pending (Phase 2).",
    )
