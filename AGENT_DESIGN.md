# GovGuide AI — Intelligent Agent Design & Multi-Agent Specification

> **Module**: IT3041 – Information Retrieval and Web Analytics (SLIIT)  
> **Document**: AGENT_DESIGN.md  
> **System**: GovGuide AI Multi-Agent Platform  

---

## 1. Multi-Agent Design Philosophy

GovGuide AI uses a **decoupled multi-agent architecture** where each agent is an autonomous, intelligent component with a well-defined contract, specialized tools, and domain boundaries.

```
       ┌──────────────────────────────────────────────────────────────┐
       │                        ORCHESTRATOR                          │
       └──────┬───────────────────────┬────────────────────────▲──────┘
              │ (1. Raw Query)        │ (2. Structured Query)  │ (3. Final Answer)
              ▼                       ▼                        │
┌──────────────────────────┐   ┌──────────────────────────┐    │
│  Agent 1: Query Agent    │──►│  Agent 2: Retrieval Agent│    │
│  - Preprocessing         │   │  - BM25 Index Search     │    │
│  - Intent Classifier     │   │  - Semantic Vector Search│    │
│  - NER & Entity Extractor│   │  - Reciprocal Rank Fusion│    │
│  - Safety & Ambiguity    │   │  - Evidence Packaging    │    │
└──────────────────────────┘   └─────────────┬────────────┘    │
                                             │ (Evidence)      │
                                             ▼                 │
                               ┌──────────────────────────┐    │
                               │ Agent 3: Response Agent  │────┘
                               │ - Grounded Prompt Builder│
                               │ - LLM Generation         │
                               │ - Grounding Checker      │
                               │ - Anti-Hallucination     │
                               └──────────────────────────┘
```

---

## 2. Agent 1: Query Understanding Agent (`AgentId.QUERY_AGENT`)

### 2.1. Purpose & Responsibilities
The Query Understanding Agent is the natural-language processing entry point. It converts unstructured citizen inputs into formal, structured search requests while filtering adversarial manipulation attempts.

### 2.2. Internal Processing Pipeline
1. **Input Sanitization**: Removes disallowed control characters and normalizes whitespace (`sanitize_query`).
2. **Security & Injection Guard**: Scans the input against prompt injection patterns using heuristic and regex classifiers (`assert_safe`).
3. **Lexical Preprocessing & Tokenization**: Preserves municipal codes (e.g. `1006`, `1010`), tokenizes text, removes general stopwords, and applies domain synonym expansion (e.g., "food truck" $\rightarrow$ "mobile food vendor peddler").
4. **Intent Classification**: Evaluates multi-class intent taxonomy:
   - `service_information`: General service overview and scope
   - `eligibility`: Qualification rules, restrictions, prerequisites
   - `required_documents`: Identification, lease, forms, affidavits
   - `application_procedure`: Step-by-step guidance, where to submit
   - `fees`: Fee schedules, tiers, cost amounts
   - `renewal`: Expiration intervals, renewal procedures
   - `office_information`: City Hall locations, contact numbers, hours
   - `general`: Broad conversational queries
   - `unknown`: Ambiguous or unclassified requests
5. **Named Entity Recognition (NER)**: Extracts domain entities with confidence scores:
   - `SERVICE`: e.g. "Retail Food Establishment", "Limited Business License"
   - `LOCATION`: e.g. "Chicago", "City Hall", "121 N LaSalle St"
   - `ORGANIZATION`: e.g. "BACP", "CDPH", "Small Business Center"
   - `LICENSE_CODE`: e.g. "1006", "1010", "1011"
   - `FEE_AMOUNT`: e.g. "$660", "$250"
   - `DATE_PERIOD`: e.g. "2 years", "biennial"
6. **Ambiguity Assessment**: Flags queries that lack sufficient contextual tokens for retrieval.

### 2.3. Output Payload Contract (`StructuredQueryPayload`)
```python
class StructuredQueryPayload(BaseModel):
    task_type: TaskType = TaskType.QUERY_UNDERSTANDING
    original_query: str
    cleaned_query: str
    expanded_query: str
    intent: Intent
    entities: List[EntityExtraction]
    keywords: List[str]
    is_safe: bool
    is_ambiguous: bool
    search_parameters: Dict[str, Any]
```

---

## 3. Agent 2: Retrieval Agent (`AgentId.RETRIEVAL_AGENT`)

### 3.1. Purpose & Responsibilities
The Retrieval Agent interfaces with the knowledge repository to retrieve the most relevant canonical document chunks. It does **not** generate natural language answers, ensuring pure evidentiary separation.

### 3.2. Internal Retrieval Execution
1. **Search Query Resolution**: Consumes the `expanded_query` and domain `search_parameters` from Agent 1.
2. **Multi-Retriever Execution**:
   - Executes Okapi BM25 retrieval over inverted chunk index ($k_1=1.5, b=0.75$).
   - Executes dense semantic retrieval via cosine similarity against deterministic document embeddings.
3. **Rank Fusion**: Applies Reciprocal Rank Fusion ($k=60$) to merge ranked lists.
4. **Confidence Computation**: Evaluates top relevance scores and document density to produce a normalized retrieval confidence score $\in [0.0, 1.0]$.
5. **Sufficiency Check**: Compares confidence against `RETRIEVAL_CONFIDENCE_THRESHOLD` ($0.15$).

### 3.3. Output Payload Contract (`RetrievalResultPayload`)
```python
class RetrievalResultPayload(BaseModel):
    task_type: TaskType = TaskType.INFORMATION_RETRIEVAL
    evidence_bundle: EvidenceBundle
    retrieval_confidence: float
    sufficient_evidence: bool
```

---

## 4. Agent 3: Response / Verification Agent (`AgentId.RESPONSE_AGENT`)

### 4.1. Purpose & Responsibilities
The Response / Verification Agent synthesizes the final citizen answer. It is bound by strict Responsible AI rules: it must never fabricate government requirements and must cite verified sources for all factual statements.

### 4.2. Internal Generation & Verification Pipeline
1. **Evidence Sufficiency Gate**: If `sufficient_evidence` is `False`, immediately returns a standard insufficient evidence advisory without triggering external LLM inference.
2. **Grounded Prompt Construction**: Builds a prompt containing:
   - System boundary directives
   - Evidence enclosed in XML `<OFFICIAL_EVIDENCE>` containers
   - Citizen query and citation formatting instructions (`[Source N]`)
3. **LLM Inference & Fallback**:
   - Calls the configured LLM client (e.g. OpenAI `gpt-4o-mini`, Groq, Anthropic, or Ollama).
   - If the LLM provider is unconfigured, rate-limited, or unavailable, executes the **Grounded Evidence Synthesizer** to compile a structured answer directly from top retrieved chunks.
4. **Post-Generation Grounding Validation**:
   - Validates that all URLs in the answer match official Chicago government portals (`chicago.gov`).
   - Checks that all factual statements reference retrieved document chunks.
   - Attaches mandatory citizen caveats (e.g. recommendation to verify with BACP).
5. **Confidence Labeling**:
   - `HIGH`: $\text{Confidence} \ge 0.75$ and validated.
   - `MEDIUM`: $0.45 \le \text{Confidence} < 0.75$ and validated.
   - `LOW`: $0.15 \le \text{Confidence} < 0.45$ and validated.
   - `INSUFFICIENT`: $\text{Confidence} < 0.15$ or unvalidated.

### 4.3. Output Payload Contract (`ResponseResultPayload`)
```python
class ResponseResultPayload(BaseModel):
    task_type: TaskType = TaskType.RESPONSE_GENERATION
    answer: str
    confidence_score: float
    confidence_label: ConfidenceLabel
    sources: List[SourceReference]
    caveats: List[str]
    explanation: Optional[str]
    response_validated: bool
    fabrication_detected: bool
```

---

## 5. Agent Communication Protocols & Message Envelope

All inter-agent messages use the `AgentMessage` standard envelope:

```python
class AgentMessage(BaseModel):
    schema_version: str = "1.0"
    request_id: str
    correlation_id: str
    timestamp: str
    sender: AgentId
    recipient: AgentId
    message_type: MessageType  # TASK | RESULT | ERROR | STATUS
    payload: Any
```

### Sequence Flow Diagram:
```text
Client -> Orchestrator : POST /query
Orchestrator -> Agent 1 (Query Agent) : AgentMessage(TASK, raw_query)
Agent 1 -> Orchestrator : AgentMessage(RESULT, StructuredQueryPayload)
Orchestrator -> Agent 2 (Retrieval Agent) : AgentMessage(TASK, StructuredQueryPayload)
Agent 2 -> Orchestrator : AgentMessage(RESULT, RetrievalResultPayload)
Orchestrator -> Agent 3 (Response Agent) : AgentMessage(TASK, AdvisoryTaskPayload)
Agent 3 -> Orchestrator : AgentMessage(RESULT, ResponseResultPayload)
Orchestrator -> Client : QueryResponse
```

---

## 6. Failure Recovery & Fallback Matrix

| Failure Scenario | Detecting Component | Recovery Strategy |
| :--- | :--- | :--- |
| **Prompt Injection Detected** | Agent 1 / PromptInjectionGuard | Intercept at gateway; return safe standard security refusal. |
| **No Matching Knowledge in Database** | Agent 2 (Retrieval Agent) | Return `sufficient_evidence=False`; Agent 3 renders official BACP office referral without calling LLM. |
| **LLM Provider API Outage / Rate Limit** | Agent 3 (Response Agent) | Fallback directly to deterministic Grounded Evidence Synthesis using verified DB chunks. |
| **Database Connection Failure** | FailureHandler | Catch exception; return structured `ErrorCode.RETRIEVAL_FAILED` with safe guidance message. |
| **Agent Timeout** | Orchestrator | FailureHandler catches timeout; returns safe advisory error envelope. |
