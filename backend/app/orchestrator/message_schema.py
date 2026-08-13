"""
GovGuide AI — Agent Communication Message Schema
All inter-agent messages are Pydantic models.
This is the single source of truth for the agent communication contract.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enumerations ──────────────────────────────────────────────────────────────

class AgentId(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCH_AGENT = "research_agent"
    ADVISORY_AGENT = "advisory_agent"


class MessageType(str, Enum):
    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    STATUS = "status"


class TaskType(str, Enum):
    INFORMATION_RETRIEVAL = "information_retrieval"
    RESPONSE_GENERATION = "response_generation"


class Intent(str, Enum):
    SERVICE_LOOKUP = "service_lookup"
    ELIGIBILITY = "eligibility"
    PROCEDURE = "procedure"
    GENERAL = "general"
    UNKNOWN = "unknown"


class ConfidenceLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


class ErrorCode(str, Enum):
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INJECTION_DETECTED = "INJECTION_DETECTED"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"


# ── Sub-models ────────────────────────────────────────────────────────────────

class RetrievalConfig(BaseModel):
    mode: str = "hybrid"          # bm25 | vector | hybrid
    top_k: int = 10
    filters: Dict[str, Any] = Field(default_factory=dict)


class NLPConfig(BaseModel):
    run_ner: bool = True
    run_query_expansion: bool = True


class EntityExtraction(BaseModel):
    text: str
    label: str
    confidence: float = 0.0


class NLPAnalysis(BaseModel):
    intent: Intent = Intent.UNKNOWN
    entities: List[EntityExtraction] = Field(default_factory=list)
    expanded_query: str = ""
    keywords: List[str] = Field(default_factory=list)


class EvidenceResult(BaseModel):
    chunk_id: str
    source_id: str
    source_title: str
    source_url: Optional[str] = None
    content: str
    relevance_score: float = 0.0
    retrieval_method: str = "stub"  # bm25 | vector | hybrid | stub


class EvidenceBundle(BaseModel):
    total_retrieved: int = 0
    results: List[EvidenceResult] = Field(default_factory=list)


class SourceReference(BaseModel):
    source_id: str
    title: str
    url: Optional[str] = None
    excerpt: Optional[str] = None


class GenerationConfig(BaseModel):
    max_tokens: int = 800
    temperature: float = 0.1
    require_source_attribution: bool = True
    enable_hallucination_check: bool = True


# ── Task Payloads ─────────────────────────────────────────────────────────────

class ResearchTaskPayload(BaseModel):
    """Payload sent by Orchestrator → Research Agent."""
    task_type: TaskType = TaskType.INFORMATION_RETRIEVAL
    user_query: str
    session_id: Optional[str] = None
    retrieval_config: RetrievalConfig = Field(default_factory=RetrievalConfig)
    nlp_config: NLPConfig = Field(default_factory=NLPConfig)


class ResearchResultPayload(BaseModel):
    """Payload returned by Research Agent → Orchestrator."""
    task_type: TaskType = TaskType.INFORMATION_RETRIEVAL
    nlp_analysis: NLPAnalysis = Field(default_factory=NLPAnalysis)
    evidence_bundle: EvidenceBundle = Field(default_factory=EvidenceBundle)
    retrieval_confidence: float = 0.0
    sufficient_evidence: bool = False


class AdvisoryTaskPayload(BaseModel):
    """Payload sent by Orchestrator → Advisory Agent."""
    task_type: TaskType = TaskType.RESPONSE_GENERATION
    user_query: str
    nlp_analysis: NLPAnalysis
    evidence_bundle: EvidenceBundle
    retrieval_confidence: float
    sufficient_evidence: bool
    generation_config: GenerationConfig = Field(default_factory=GenerationConfig)


class AdvisoryResultPayload(BaseModel):
    """Payload returned by Advisory Agent → Orchestrator."""
    task_type: TaskType = TaskType.RESPONSE_GENERATION
    answer: str
    confidence_score: float = 0.0
    confidence_label: ConfidenceLabel = ConfidenceLabel.INSUFFICIENT
    sources: List[SourceReference] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None
    response_validated: bool = False
    fabrication_detected: bool = False


class ErrorPayload(BaseModel):
    """Error payload returned by any agent."""
    error_code: ErrorCode
    error_message: str
    recoverable: bool = True
    fallback_response: str = (
        "I could not find sufficient official evidence to provide a reliable answer. "
        "Please consult the relevant government authority directly."
    )


# ── Common Envelope ───────────────────────────────────────────────────────────

class AgentMessage(BaseModel):
    """
    The common envelope for all inter-agent messages.
    Every message sent between the orchestrator and agents uses this schema.
    """
    schema_version: str = "1.0"
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sender: AgentId
    recipient: AgentId
    message_type: MessageType
    payload: Any  # typed by the specific payload models above

    model_config = {"use_enum_values": True}
