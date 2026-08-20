# GovGuide AI — Phase 4: Retrieval & RAG Preparation Report

**Date**: 2026-08-20  
**Phase**: 4 — Retrieval & RAG Preparation  
**Status**: COMPLETE & VERIFIED  

---

## 1. Executive Summary

Phase 4 of GovGuide AI implements the Information Retrieval (IR) and RAG preparation layer using deterministic, local, and fully attributable components. The architecture transforms the 56 canonical `GovernmentService` records into 504 semantic section chunks, indexes them across lexical (BM25) and semantic vector spaces, and ranks them using Reciprocal Rank Fusion ($RRF$, $k=60$) to construct structured `EvidenceBundle` objects.

All 213 unit and integration tests are passing (182 existing + 31 new), with zero database migrations or modifications to raw CSV operational data.

---

## 2. Files Created & Modified

### New Files Created (Phase 4)
- `docs/PHASE_4_RETRIEVAL_IMPLEMENTATION_PLAN.md` — Technical design document.
- `backend/app/retrieval/document_builder.py` — Canonical document builder (9 sections, `NOT_AVAILABLE` policy).
- `backend/app/retrieval/chunker.py` — Semantic section chunker preserving full source attribution.
- `backend/app/retrieval/chunk_generator.py` — Database knowledge loader and chunk generator.
- `backend/app/retrieval/bm25_retriever.py` — Okapi BM25 indexer ($k_1=1.5, b=0.75$).
- `backend/app/retrieval/semantic_retriever.py` — Pluggable `EmbeddingProvider` and local deterministic provider.
- `backend/app/retrieval/hybrid_retriever.py` — Reciprocal Rank Fusion ($k=60$) rank combiner.
- `backend/app/retrieval/source_attribution.py` — Source validation and rejection filters.
- `backend/app/retrieval/retrieval_service.py` — Unified retrieval orchestrator pipeline.
- `data/evaluation/retrieval_queries.json` — 22 ground-truth benchmark queries.
- `backend/app/retrieval/evaluator.py` — Precision@5, Recall@5, MRR@10, and latency benchmark harness.
- `data/evaluation/retrieval_evaluation_report.json` — Evaluator benchmark report.
- `tests/unit/test_document_builder.py` — Unit tests for document construction.
- `tests/unit/test_chunker.py` — Unit tests for section chunking.
- `tests/unit/test_bm25_retriever.py` — Unit tests for BM25 lexical retrieval.
- `tests/unit/test_semantic_retriever.py` — Unit tests for local vector embeddings.
- `tests/unit/test_hybrid_retriever.py` — Unit tests for RRF fusion.
- `tests/unit/test_evidence_bundle.py` — Unit tests for schema validation and backward compatibility.
- `tests/unit/test_source_attribution.py` — Unit tests for source attribution invariant.
- `tests/integration/test_retrieval_pipeline.py` — End-to-end integration tests with PostgreSQL data.
- `docs/PHASE_4_RETRIEVAL_REPORT.md` — This report.

### Files Modified
- `backend/app/config.py` — Added retrieval configuration parameters (`RETRIEVAL_TOP_K`, `RRF_K`, `BM25_K1`, `BM25_B`, `RETRIEVAL_CONFIDENCE_THRESHOLD`).
- `backend/app/nlp/preprocessor.py` — Added domain query expansion, punctuation cleaning, and tokenization.
- `backend/app/orchestrator/message_schema.py` — Extended `EvidenceResult` and `EvidenceBundle` while maintaining backward compatibility.
- `backend/app/retrieval/retrieval_engine.py` — Connected facade to `RetrievalService`.
- `backend/app/retrieval/__init__.py` — Exported retrieval components.
- `backend/app/agents/research_agent/agent.py` — Connected ResearchAgent to live retrieval service and confidence thresholding.

---

## 3. Knowledge Base & Chunking Statistics

| Metric | Count | Details |
|---|---|---|
| **GovernmentService Documents** | **56** | 100% of municipal business license types in Chicago |
| **Operational BusinessLicense Records** | **53,091** | Preserved for structured queries, NOT chunked into RAG |
| **Semantic Sections per Service** | **9** | Overview, Eligibility, Required Documents, Application Procedure, Fees, Renewal, Responsible Office, Contact Information, Legal/Source |
| **Total Searchable Chunks** | **504** | 56 services $\times$ 9 sections |
| **Missing Fields Handled** | **100%** | Mapped strictly to `NOT_AVAILABLE` with zero fabricated facts |
| **Source Attribution Compliance** | **100%** | Every chunk contains `source_id`, `source_url`, `source_title`, `service_code`, and `section` |

---

## 4. Benchmark Evaluation Results

Evaluated across **22 ground-truth citizen queries** covering all 9 municipal categories:

| Retrieval Mode | Precision@5 | Recall@5 | MRR@10 | Mean Latency | Median Latency | P95 Latency |
|---|---|---|---|---|---|---|
| **BM25 Lexical** | 0.7273 | 0.7273 | 0.7500 | 1.07 ms | 0.81 ms | 4.06 ms |
| **Semantic (Local Vector)** | 0.5000 | 0.5909 | 0.5773 | 5.59 ms | 5.48 ms | 7.77 ms |
| **Hybrid RRF ($k=60$)** | **0.5909** | **0.6591** | **0.7388** | **7.38 ms** | **7.12 ms** | **13.81 ms** |

*Note: All latency measurements were performed on local hardware with zero external network overhead.*

---

## 5. Source Attribution & Confidence Invariants

1. **Mandatory Attribution**:
   - Every candidate evidence result passes through `filter_attributed_results()`.
   - Results missing `source_id`, `source_url`, or `source_title` are rejected immediately with structured warning logs.
2. **Confidence Thresholding**:
   - `RETRIEVAL_CONFIDENCE_THRESHOLD = 0.15` (configurable in `.env` / `config.py`).
   - If retrieval confidence falls below threshold (e.g. out-of-domain or nonsense queries), `ResearchAgent` sets `sufficient_evidence = False`, preventing downstream hallucination.

---

## 6. Test Suite Results

```
====================== 213 passed, 11 warnings in 8.28s =======================
```

- **Previous Passing Tests (Phase 3)**: 182
- **New Tests (Phase 4)**: 31
- **Total Tests**: 213
- **Passed**: 213 (100%)
- **Failed**: 0 (0%)
- **Regressions**: 0

---

## 7. Limitations & Recommendations for Phase 5

### Current Limitations (By Design in Phase 4)
- **Local Embedding Provider**: Uses a deterministic character/word n-gram vectorizer for zero-cost, offline development. While fast and deterministic, deep semantic generalization will improve with neural embeddings.
- **In-Memory Chunk Index**: 504 chunks are indexed in-memory at application startup. For larger future corpora (e.g., zoning ordinances, municipal codes), pgvector indexing should be leveraged.
- **LLM Synthesis**: Phase 4 focuses solely on retrieval preparation. Generating final citizen advisory responses requires Phase 5 AdvisoryAgent / LLM integration.

### Recommended Next Steps for Phase 5
1. **Connect AdvisoryAgent**: Feed structured `EvidenceBundle` outputs into prompt templates with strict citation constraints.
2. **Production Embedding Model**: Integrate `sentence-transformers` or OpenAI embeddings using the pluggable `EmbeddingProvider` interface.
3. **Conversational Memory Integration**: Pass multi-turn context into query expansion and research workflows.
