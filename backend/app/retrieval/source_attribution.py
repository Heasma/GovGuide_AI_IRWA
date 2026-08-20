"""
GovGuide AI — Source Attribution Validator

Enforces the core institutional invariant that every retrieved piece of evidence
must remain strictly traceable to its verified government source.

Rules:
- Every result must contain non-empty source_id, source_url, and source_title.
- Unattributed or missing-source results are rejected from the EvidenceBundle.
"""

from typing import Any, Dict, List, Tuple
import structlog

logger = structlog.get_logger(__name__)


def validate_source_attribution(item: Any) -> Tuple[bool, str]:
    """
    Validate that an evidence item has complete and non-empty source attribution.

    Returns:
        (is_valid: bool, reason: str)
    """
    def _extract(obj: Any, key: str) -> str:
        if isinstance(obj, dict):
            val = obj.get(key)
        else:
            val = getattr(obj, key, None)
        return str(val).strip() if val is not None else ""

    source_id = _extract(item, "source_id")
    source_url = _extract(item, "source_url")
    source_title = _extract(item, "source_title")

    if not source_id or source_id.upper() in ("NONE", "NULL", "NOT_AVAILABLE"):
        return False, "Missing or invalid source_id"

    if not source_url or source_url.upper() in ("NONE", "NULL", "NOT_AVAILABLE"):
        return False, "Missing or invalid source_url"

    if not source_title or source_title.upper() in ("NONE", "NULL", "NOT_AVAILABLE"):
        return False, "Missing or invalid source_title"

    return True, "Valid source attribution"


def filter_attributed_results(results: List[Any]) -> List[Any]:
    """
    Filter a list of retrieved candidate items, discarding any that fail
    the source attribution invariant.
    """
    valid_results: List[Any] = []

    for item in results:
        is_valid, reason = validate_source_attribution(item)
        if is_valid:
            valid_results.append(item)
        else:
            cid = getattr(item, "chunk_id", None) or (item.get("chunk_id") if isinstance(item, dict) else "unknown")
            logger.warning(
                "evidence_rejected_missing_source",
                chunk_id=cid,
                reason=reason,
            )

    return valid_results
