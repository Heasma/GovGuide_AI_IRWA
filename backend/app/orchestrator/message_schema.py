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
    QUERY_AGENT = "query_agent"
    QUERY_UNDERSTANDING_AGENT = "query_understanding_agent"
    RETRIEVAL_AGENT = "retrieval_agent"
    RESPONSE_AGENT = "response_agent"
    RESPONSE_VERIFICATION_AGENT = "response_verification_agent"
    # Legacy / alias identifiers for backward compatibility
    RESEARCH_AGENT = "research_agent"
    ADVISORY_AGENT = "advisory_agent"


class MessageType(str, Enum):
    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    STATUS = "status"


class TaskType(str, Enum):
    QUERY_UNDERSTANDING = "query_understanding"
    INFORMATION_RETRIEVAL = "information_retrieval"
    RESPONSE_GENERATION = "response_generation"
    VERIFICATION = "verification"


class Intent(str, Enum):
    SERVICE_LOOKUP = "service_lookup"
    SERVICE_INFORMATION = "service_information"
    LICENSE_IDENTIFICATION = "license_identification"
    ELIGIBILITY = "eligibility"
    GEOGRAPHIC_ELIGIBILITY = "geographic_eligibility"
    PROCEDURE = "procedure"
    APPLICATION_PROCEDURE = "application_procedure"
    REQUIRED_DOCUMENTS = "required_documents"
    FEES = "fees"
    RENEWAL = "renewal"
    OFFICE_INFORMATION = "office_information"
    COMPARISON = "comparison"
    SOURCE_EVIDENCE = "source_evidence"
    CONVERSATIONAL = "conversational"
    GREETING = "greeting"
    THANKS = "thanks"
    ACKNOWLEDGEMENT = "acknowledgement"
    GOODBYE = "goodbye"
    GENERAL = "general"
    UNKNOWN = "unknown"



class Domain(str, Enum):
    BUSINESS_LICENSE = "business_license"
    GOVERNMENT_SERVICE = "government_service"
    DRIVER_LICENSE = "driver_license"
    VEHICLE_REGISTRATION = "vehicle_registration"
    AVIATION = "aviation"
    TAX = "tax"
    HEALTH = "health"
    EDUCATION = "education"
    OTHER = "other"
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
    UNSUPPORTED_DOMAIN = "UNSUPPORTED_DOMAIN"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"


class SecurityClassification(str, Enum):
    NORMAL = "NORMAL"
    SYSTEM_PROMPT_EXTRACTION = "SYSTEM_PROMPT_EXTRACTION"
    INSTRUCTION_OVERRIDE = "INSTRUCTION_OVERRIDE"
    FAKE_SYSTEM_MESSAGE = "FAKE_SYSTEM_MESSAGE"
    ROLEPLAY_JAILBREAK = "ROLEPLAY_JAILBREAK"
    DEVELOPER_MODE = "DEVELOPER_MODE"
    AUTHORITY_BYPASS = "AUTHORITY_BYPASS"
    INTERNAL_METADATA_EXTRACTION = "INTERNAL_METADATA_EXTRACTION"
    RAG_INJECTION = "RAG_INJECTION"
    SECURITY_POLICY_EXTRACTION = "SECURITY_POLICY_EXTRACTION"


class SecurityAction(str, Enum):
    ALLOW = "ALLOW"
    BLOCK_AND_SAFE_RESPOND = "BLOCK_AND_SAFE_RESPOND"


# ── Sub-models ────────────────────────────────────────────────────────────────

class RetrievalConfig(BaseModel):
    mode: str = "hybrid"          # bm25 | vector | hybrid
    top_k: int = 10
    filters: Dict[str, Any] = Field(default_factory=dict)
    domain_filter: Optional[str] = None


class NLPConfig(BaseModel):
    run_ner: bool = True
    run_query_expansion: bool = True
    detect_domain: bool = True


class EntityExtraction(BaseModel):
    text: str
    label: str
    confidence: float = 0.0
    start_char: Optional[int] = None
    end_char: Optional[int] = None


class NLPAnalysis(BaseModel):
    intent: Intent = Intent.UNKNOWN
    intents: List[Intent] = Field(default_factory=list)
    domain: Domain = Domain.UNKNOWN
    is_domain_supported: bool = True
    entities: List[EntityExtraction] = Field(default_factory=list)
    expanded_query: str = ""
    keywords: List[str] = Field(default_factory=list)
    is_safe: bool = True
    confidence: float = 1.0


class EvidenceResult(BaseModel):
    chunk_id: str
    source_id: str
    source_title: str
    source_url: Optional[str] = None
    content: str = ""
    text: Optional[str] = None
    relevance_score: float = 0.0
    score: Optional[float] = None
    service_id: Optional[str] = None
    service_code: Optional[str] = None
    service_name: Optional[str] = None
    section: Optional[str] = None
    domain: str = "business_license"
    retrieval_method: str = "hybrid"  # bm25 | vector | hybrid | stub
    source_confidence: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.content and self.text:
            self.content = self.text
        elif not self.text and self.content:
            self.text = self.content
        if self.score is None:
            self.score = self.relevance_score
        elif self.relevance_score == 0.0 and self.score is not None:
            self.relevance_score = self.score


class SourceReference(BaseModel):
    source_id: str
    title: str
    url: Optional[str] = None
    excerpt: Optional[str] = None


class EvidenceBundle(BaseModel):
    query: str = ""
    intent: Optional[str] = None
    intents: List[str] = Field(default_factory=list)
    domain: Optional[str] = None
    domain_supported: bool = True
    total_retrieved: int = 0
    confidence: float = 0.0
    retrieval_method: str = "hybrid"
    results: List[EvidenceResult] = Field(default_factory=list)
    sources: List[SourceReference] = Field(default_factory=list)


class GenerationConfig(BaseModel):
    max_tokens: int = 800
    temperature: float = 0.1
    require_source_attribution: bool = True
    enable_hallucination_check: bool = True


# ── Task Payloads ─────────────────────────────────────────────────────────────

# Agent 1: Query Understanding Agent Payloads
class QueryUnderstandingTaskPayload(BaseModel):
    """Payload sent to Query Understanding Agent."""
    task_type: TaskType = TaskType.QUERY_UNDERSTANDING
    raw_query: str
    session_id: Optional[str] = None
    context_entity: Optional[str] = None
    nlp_config: NLPConfig = Field(default_factory=NLPConfig)



class StructuredQueryPayload(BaseModel):
    """Payload produced by Query Understanding Agent."""
    task_type: TaskType = TaskType.QUERY_UNDERSTANDING
    original_query: str
    cleaned_query: str
    expanded_query: str
    intent: Intent = Intent.UNKNOWN
    intents: List[Intent] = Field(default_factory=list)
    domain: Domain = Domain.UNKNOWN
    is_domain_supported: bool = True
    entities: List[EntityExtraction] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    is_safe: bool = True
    is_ambiguous: bool = False
    search_parameters: Dict[str, Any] = Field(default_factory=dict)


# Agent 2: Retrieval Agent Payloads
class RetrievalTaskPayload(BaseModel):
    """Payload sent to Retrieval Agent."""
    task_type: TaskType = TaskType.INFORMATION_RETRIEVAL
    structured_query: StructuredQueryPayload
    retrieval_config: RetrievalConfig = Field(default_factory=RetrievalConfig)


class RetrievalResultPayload(BaseModel):
    """Payload returned by Retrieval Agent."""
    task_type: TaskType = TaskType.INFORMATION_RETRIEVAL
    evidence_bundle: EvidenceBundle = Field(default_factory=EvidenceBundle)
    retrieval_confidence: float = 0.0
    sufficient_evidence: bool = False
    domain: Optional[Domain] = None
    is_domain_supported: bool = True


# Agent 3: Response / Verification Agent Payloads
class ResponseTaskPayload(BaseModel):
    """Payload sent to Response / Verification Agent."""
    task_type: TaskType = TaskType.RESPONSE_GENERATION
    user_query: str
    structured_query: Optional[StructuredQueryPayload] = None
    domain: Optional[Domain] = None
    is_domain_supported: bool = True
    evidence_bundle: EvidenceBundle
    retrieval_confidence: float
    sufficient_evidence: bool
    generation_config: GenerationConfig = Field(default_factory=GenerationConfig)


class ResponseResultPayload(BaseModel):
    """Payload returned by Response / Verification Agent."""
    task_type: TaskType = TaskType.RESPONSE_GENERATION
    answer: str
    confidence_score: float = 0.0
    confidence_label: ConfidenceLabel = ConfidenceLabel.INSUFFICIENT
    domain: Optional[Domain] = None
    is_domain_supported: bool = True
    sources: List[SourceReference] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None
    response_validated: bool = False
    fabrication_detected: bool = False


# Legacy payloads for backward compatibility with existing tests
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
    domain: Optional[Domain] = None
    is_domain_supported: bool = True
    generation_config: GenerationConfig = Field(default_factory=GenerationConfig)


class AdvisoryResultPayload(BaseModel):
    """Payload returned by Advisory Agent → Orchestrator."""
    task_type: TaskType = TaskType.RESPONSE_GENERATION
    answer: str
    confidence_score: float = 0.0
    confidence_label: ConfidenceLabel = ConfidenceLabel.INSUFFICIENT
    domain: Optional[Domain] = None
    is_domain_supported: bool = True
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
