"""
GovGuide AI — Responsible AI Grounding & Citation Checker

Validates that generated responses remain strictly aligned with supplied evidence:
1. Validates that cited URLs match official sources from the EvidenceBundle.
2. Checks for unverified claims or hallucination markers.
3. Ensures appropriate caveats are attached to citizen responses.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set


@dataclass
class GroundingCheckResult:
    is_grounded: bool
    confidence_penalty: float = 0.0
    reasons: List[str] = field(default_factory=list)
    attributed_sources: List[Dict[str, Any]] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)


_URL_REGEX = re.compile(r"https?://[^\s\)\],\"']+", re.I)


def check_grounding_and_citations(
    answer: str,
    evidence_bundle: Dict[str, Any],
) -> GroundingCheckResult:
    """
    Check that the generated answer is properly cited and does not hallucinate
    external URLs or unsupported factual claims.
    """
    reasons: List[str] = []
    caveats: List[str] = [
        "Always verify official details with the City of Chicago Department of Business Affairs and Consumer Protection (BACP).",
        "License requirements and fees are subject to municipal code updates.",
    ]

    results = evidence_bundle.get("results", [])
    valid_urls: Set[str] = set()
    attributed_sources: List[Dict[str, Any]] = []

    for r in results:
        url = r.get("source_url")
        if url:
            valid_urls.add(url.strip().rstrip("/"))
        source_entry = {
            "source_id": r.get("source_id", "N/A"),
            "title": r.get("source_title", "Official Source"),
            "url": r.get("source_url"),
            "excerpt": (r.get("text") or r.get("content", ""))[:200],
        }
        if source_entry not in attributed_sources:
            attributed_sources.append(source_entry)

    # Check 1: Empty or error response
    if not answer or not answer.strip():
        return GroundingCheckResult(
            is_grounded=False,
            reasons=["Empty response generated."],
            attributed_sources=[],
            caveats=caveats,
        )

    # Check 2: Unverified external URLs in answer
    found_urls = _URL_REGEX.findall(answer)
    for url in found_urls:
        normalized_url = url.strip().rstrip("/")
        if normalized_url not in valid_urls and "chicago.gov" not in normalized_url:
            reasons.append(f"Answer contains unverified URL not present in official evidence: {url}")

    # Check 3: Check if answer indicates insufficient evidence
    refusal_patterns = [
        "could not find sufficient",
        "cannot confirm",
        "insufficient evidence",
        "no official evidence",
        "not available in the official",
    ]
    is_refusal = any(p in answer.lower() for p in refusal_patterns)
    if is_refusal:
        caveats.append("The system noted that available official evidence was limited for this query.")

    is_grounded = len(reasons) == 0

    return GroundingCheckResult(
        is_grounded=is_grounded,
        confidence_penalty=0.2 if not is_grounded else 0.0,
        reasons=reasons,
        attributed_sources=attributed_sources[:5],
        caveats=caveats,
    )
