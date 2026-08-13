"""
GovGuide AI — Audit Logger
Writes immutable structured audit events to the database.
Does NOT log raw request bodies, passwords, or PII.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


def _hash_payload(payload: dict) -> str:
    """SHA-256 hash of a payload dict. Used to record what was sent without storing PII."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


class AuditEvent:
    """
    Represents a single audit event.
    Call .to_dict() to get the log record.
    """

    def __init__(
        self,
        event_type: str,
        outcome: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.outcome = outcome
        self.user_id = user_id
        self.resource = resource
        self.ip_address = ip_address
        self.request_id = request_id
        self.payload_hash = _hash_payload(payload) if payload else None
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "outcome": self.outcome,
            "user_id": self.user_id,
            "resource": self.resource,
            "ip_address": self.ip_address,
            "request_id": self.request_id,
            "payload_hash": self.payload_hash,
            "timestamp": self.timestamp,
        }


def log_event(
    event_type: str,
    outcome: str,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> AuditEvent:
    """
    Log an audit event to structured logs.
    In Phase 2, this will also persist to the audit_logs database table.

    Outcomes: "success" | "failure" | "blocked"
    """
    event = AuditEvent(
        event_type=event_type,
        outcome=outcome,
        user_id=user_id,
        resource=resource,
        ip_address=ip_address,
        request_id=request_id,
        payload=payload,
    )
    logger.info("audit_event", **event.to_dict())
    return event


# ── Convenience helpers ───────────────────────────────────────────────────────

def log_login(user_id: str, ip: str, success: bool, request_id: str = None):
    log_event(
        event_type="auth.login",
        outcome="success" if success else "failure",
        user_id=user_id,
        resource="/api/v1/auth/login",
        ip_address=ip,
        request_id=request_id,
    )


def log_query(user_id: Optional[str], request_id: str, ip: str):
    log_event(
        event_type="query.submitted",
        outcome="success",
        user_id=user_id,
        resource="/api/v1/query",
        ip_address=ip,
        request_id=request_id,
    )


def log_blocked(reason: str, ip: str, request_id: str = None):
    log_event(
        event_type="security.blocked",
        outcome="blocked",
        resource=reason,
        ip_address=ip,
        request_id=request_id,
    )
