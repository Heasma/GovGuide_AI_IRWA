# GovGuide AI — Phase 4: Retrieval & RAG Preparation Implementation Plan

**Date**: 2026-08-20  
**Phase**: 4 — Retrieval & RAG Preparation  
**Status**: APPROVED — Implementation Ready  

---

## 1. Current Retrieval Architecture & Analysis

### Existing Components & Gaps

| Component | Current State | Phase 4 Target State |
|---|---|---|
| `backend/app/retrieval/retrieval_engine.py` | Stub returning empty `EvidenceBundle` | Replaced/Delegated to `RetrievalService` with Hybrid RRF |
| `backend/app/nlp/preprocessor.py` | Basic whitespace normalization | Enhanced query preprocessor with lowercase, punct normalization, phrase preservation |
| `backend/app/nlp/intent_classifier.py` | Rule-based heuristics for 4 intents | Preserved and leveraged for intent-aware evidence routing |
| `backend/app/models/official_source.py` | ORM models for `OfficialSource` & `DocumentChunk` | Unmodified schema (uses `metadata_` JSONB for chunk attributes) |
| `backend/app/agents/research_agent/agent.py` | Calls stub `RetrievalEngine`, computes stub confidence | Connects to `RetrievalService`, validates source attribution, handles insufficient evidence |
| `backend/app/orchestrator/message_schema.py` | `EvidenceBundle` and `EvidenceResult` defined | Extended/aligned with `service_id`, `service_code`, `section`, `score`, `source_url`, `source_title` |

---

## 2. Document Representation (`document_builder.py`)

Each of the 56 `GovernmentService` records in PostgreSQL is converted into a canonical structured text document with 9 explicit sections:

1. **Header**: Service Name, License Code, Category, Responsible Department, Official Source URL
2. **Overview**: Service overview/description, target business activities
3. **Eligibility**: Entity eligibility, prerequisites, zoning, restrictions
4. **Required Documents**: Step-by-step documentation list
5. **Application Procedure**: Online portal, in-person Small Business Center (SBC) address, step-by-step workflow, inspection requirements
6. **Fees**: License fee, fee description/structure, non-refundable terms
7. **License Validity & Renewal**: License term (years), renewal requirements, renewal period
8. **Responsible Office & Contact**: BACP office, address, phone (312-74-GOBIZ), email, hours, website
9. **Legal References & Source Confidence**: Municipal Code (MCC Title 4), official URL, source confidence (`VERIFIED` | `PARTIALLY_VERIFIED` | `REQUIRES_MANUAL_VERIFICATION`)

*Rule*: No fabricated facts. If a field is blank or missing, `NOT_AVAILABLE` is explicitly emitted.

---

## 3. Semantic Section-Based Chunking (`chunker.py` & `chunk_generator.py`)

Rather than arbitrary fixed-window chunking, we implement semantic section-based chunking matching government service querying patterns:

| Section Name | Target Query Types | Metadata Retained |
|---|---|---|
| `overview` | "What is X?", "Do I need a license for Y?" | `chunk_id`, `service_id`, `service_code`, `section`, `source_id`, `source_url`, `source_title` |
| `eligibility` | "Who is eligible for X?", "Can an LLC apply for Y?" | Same |
| `required_documents` | "What documents are required for X?" | Same |
| `application_procedure` | "How do I apply for X?", "Where to submit application?" | Same |
| `fees` | "How much is X?", "What are the fees for Y?" | Same |
| `renewal` | "How to renew X?", "When does Y expire?" | Same |
| `office_contact` | "Where is BACP?", "Who to call for license help?" | Same |
| `legal_source` | "What is the municipal code for X?" | Same |

---

## 4. Lexical Retrieval Strategy (BM25) (`bm25_retriever.py`)

- **Implementation**: Standard Okapi BM25 ($k_1 = 1.5, b = 0.75$) operating over inverted token index of all service chunks.
- **Indexed Fields**:
  - `service_name` (weighted)
  - `service_code` (exact match preservation)
  - `category`
  - `section_name`
  - `content_text`
- **Output**: Ranked chunks with BM25 score, matched text snippet, service ID, and full source metadata. Default `top_k = 10`.

---

## 5. Semantic Retrieval Strategy (`semantic_retriever.py`)

- **Architecture**: Pluggable `EmbeddingProvider` interface with:
  - `embed_text(text: str) -> List[float]`
  - `embed_documents(texts: List[str]) -> List[List[float]]`
- **Phase 4 Provider**: Deterministic local TF-IDF / N-gram dense vectorizer (or local embeddings) generating fixed-dimensional cosine embeddings with zero external API dependencies or costs.
- **Extensibility**: Drop-in replaceable with OpenAI `text-embedding-3-small`, HuggingFace `sentence-transformers`, or pgvector in future phases.

---

## 6. Hybrid Retrieval & Ranking (`hybrid_retriever.py`)

- **Algorithm**: Reciprocal Rank Fusion (RRF) combining BM25 and Semantic rank positions:
  $$\text{RRF}(d) = \sum_{m \in \{\text{BM25}, \text{Semantic}\}} \frac{1}{k + \text{rank}_m(d)}$$
  with default fusion constant $k = 60$.
- **Output**: Sorted descending by RRF score, preserving both raw component scores and fused rank.

---

## 7. EvidenceBundle & Source Attribution (`source_attribution.py` & `retrieval_service.py`)

- **Attribution Invariant**: Every retrieved chunk **must** contain `source_id`, `source_url`, and `source_title`.
- **Validation**: Any chunk lacking source attribution is automatically rejected.
- **Insufficient Evidence Handling**: When query returns low relevance score ($< 0.15$ RRF) or empty match, `sufficient_evidence=False` is set to prevent hallucination.

---

## 8. Research Agent Integration (`backend/app/agents/research_agent/agent.py`)

- Updated to call `RetrievalService.search(query, top_k)`.
- Enriches NLP analysis with intent, performs hybrid search, evaluates confidence, and produces the final `ResearchResultPayload`.

---

## 9. Evaluation Strategy (`data/evaluation/` & `evaluator.py`)

- **Evaluation Dataset**: 20+ realistic citizen queries covering all 9 categories (Food, Retail, Liquor, Tobacco, Motor Vehicle, Amusement, Childcare, Property, Health).
- **Metrics Computed**:
  - Precision@5
  - Recall@5
  - MRR@10 (Mean Reciprocal Rank)
  - Latency: Average, Median, P95
- **Comparison**: BM25 vs. Semantic vs. Hybrid RRF.
- **Output**: `data/evaluation/retrieval_evaluation_report.json` and `docs/PHASE_4_RETRIEVAL_REPORT.md`.

---

## 10. Test Strategy

- `tests/unit/test_document_builder.py` — Canonical document generation & `NOT_AVAILABLE` enforcement
- `tests/unit/test_chunker.py` — Semantic section splitting & chunk metadata
- `tests/unit/test_bm25_retriever.py` — BM25 scoring & exact license code matching
- `tests/unit/test_semantic_retriever.py` — Local embedding provider & cosine similarity
- `tests/unit/test_hybrid_retriever.py` — RRF fusion formula & score ordering
- `tests/unit/test_evidence_bundle.py` — Pydantic schema validation & serialization
- `tests/unit/test_source_attribution.py` — Source attribution invariants
- `tests/integration/test_retrieval_pipeline.py` — End-to-end integration test with live PostgreSQL database
- Existing 182 tests must continue to pass without regression.
