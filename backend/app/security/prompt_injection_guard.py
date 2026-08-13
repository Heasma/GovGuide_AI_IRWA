"""
GovGuide AI — Prompt Injection Guard
Detects and rejects queries that attempt to manipulate LLM behavior.

IMPORTANT: This is a Phase 1 heuristic foundation, not a complete solution.
Advanced semantic injection detection will be added in Phase 2.
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class InjectionCheckResult:
    is_safe: bool
    reason: str = ""
    matched_pattern: str = ""


# Patterns commonly used in prompt injection attacks
_INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I),
    re.compile(r"forget\s+everything\s+(i\s+said|above|before)", re.I),
    re.compile(r"you\s+are\s+now\s+(a\s+)?(?!govguide)", re.I),  # persona override
    re.compile(r"act\s+as\s+(if\s+you\s+are|a\s+)?(?!govguide)", re.I),
    re.compile(r"pretend\s+(you\s+are|to\s+be)", re.I),
    re.compile(r"system\s*:\s*you\s+are", re.I),
    re.compile(r"\[system\]", re.I),
    re.compile(r"<\|im_start\|>|<\|im_end\|>", re.I),  # common LLM control tokens
    re.compile(r"###\s*instruction", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"do\s+anything\s+now\s*(dan)?", re.I),
]


def check_for_injection(text: str) -> InjectionCheckResult:
    """
    Check a query string for prompt injection patterns.

    Args:
        text: The sanitized user query.

    Returns:
        InjectionCheckResult with is_safe=True if no patterns matched.
    """
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return InjectionCheckResult(
                is_safe=False,
                reason="Query contains content that may attempt to manipulate the AI system.",
                matched_pattern=pattern.pattern,
            )
    return InjectionCheckResult(is_safe=True)


def assert_safe(text: str) -> str:
    """
    Raises ValueError if the text contains injection patterns.
    Returns the original text if safe.
    Used in the orchestrator before passing queries to agents.
    """
    result = check_for_injection(text)
    if not result.is_safe:
        raise ValueError(result.reason)
    return text
