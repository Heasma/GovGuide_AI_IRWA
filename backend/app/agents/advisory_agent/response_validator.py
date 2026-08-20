"""
GovGuide AI — Response Validator (Advisory Agent)

Validates that LLM-generated responses are strictly grounded in retrieved evidence
and comply with Responsible AI citation and anti-hallucination principles.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.responsible_ai.grounding_checker import check_grounding_and_citations


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
    """
    results = evidence_bundle.get("results", [])

    # Empty answer check
    if not answer or not answer.strip():
        return ValidationResult(
            passed=False,
            attributed_sources=[],
            caveats=["Response was empty."],
            explanation="LLM returned an empty response.",
        )

    # Missing evidence check
    if not results:
        return ValidationResult(
            passed=False,
            attributed_sources=[],
            caveats=[
                "No evidence was retrieved for this query.",
                "Please consult the official City of Chicago BACP portal directly.",
            ],
            explanation="No evidence in bundle — cannot validate response.",
        )

    grounding = check_grounding_and_citations(answer, evidence_bundle)

    if not grounding.is_grounded:
        return ValidationResult(
            passed=False,
            attributed_sources=grounding.attributed_sources,
            caveats=grounding.caveats + grounding.reasons,
            explanation=f"Grounding validation failed: {'; '.join(grounding.reasons)}",
        )

    return ValidationResult(
        passed=True,
        attributed_sources=grounding.attributed_sources,
        caveats=grounding.caveats,
        explanation="Response verified and grounded against official evidence.",
    )
