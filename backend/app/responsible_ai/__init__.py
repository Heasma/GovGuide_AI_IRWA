"""
GovGuide AI — Responsible AI Module
"""

from app.responsible_ai.grounding_checker import (
    GroundingCheckResult,
    check_grounding_and_citations,
)

__all__ = [
    "GroundingCheckResult",
    "check_grounding_and_citations",
]
