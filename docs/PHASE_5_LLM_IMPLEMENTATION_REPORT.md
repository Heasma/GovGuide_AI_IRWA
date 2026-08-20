# GovGuide AI — Phase 5: Advisory Agent & Grounded LLM Integration Report

**Date**: 2026-08-20  
**Phase**: 5 — Advisory Agent & Grounded LLM Integration  
**Status**: COMPLETE & VERIFIED  

---

## 1. Executive Summary

Phase 5 implements the Advisory Agent and Grounded LLM Integration layer of GovGuide AI. The system connects the Research Agent and the Hybrid RRF Retrieval Service to the Advisory Agent and the pluggable LLM provider layer (`OpenAIAdapter` / `StubLLMClient`). All factual statements are strictly grounded within XML-delimited `<OFFICIAL_EVIDENCE>` blocks with source citations (`[Source N]`).

All 234 executed unit and integration tests are passing (plus 1 optional live-LLM test skipped when no API key is set), with zero database migrations or modifications to raw operational data.

---

## 2. Files Created & Modified

### New Files Created (Phase 5)
- `docs/PHASE_5_LLM_IMPLEMENTATION_PLAN.md` — Technical implementation plan.
- `backend/app/llm/openai_adapter.py` — Asynchronous OpenAI SDK adapter with secure error translation.
- `backend/app/responsible_ai/grounding_checker.py` — Responsible AI grounding and citation validator.
- `backend/pytest.ini` — Pytest configuration with `llm` marker and asyncio settings.
- `tests/unit/test_prompt_builder.py` — Unit tests for grounded prompt construction and XML isolation.
- `tests/unit/test_llm_client.py` — Unit tests for LLM adapters, error codes, and stub fallback.
- `tests/unit/test_grounding_validation.py` — Unit tests for grounding verification and URL validation.
- `tests/unit/test_advisory_agent.py` — Unit tests for AdvisoryAgent message processing and insufficient evidence.
- `tests/integration/test_advisory_pipeline.py` — Integration tests for full multi-agent pipeline with real PostgreSQL data.
- `docs/PHASE_5_LLM_IMPLEMENTATION_REPORT.md` — This report.

### Files Modified
- `backend/app/llm/llm_client.py` — Implemented dynamic `get_llm_client()` factory and `StubLLMClient`.
- `backend/app/llm/__init__.py` — Exported LLM adapters.
- `backend/app/agents/advisory_agent/prompt_builder.py` — Implemented XML `<OFFICIAL_EVIDENCE>` prompt grounding and anti-injection sanitization.
- `backend/app/agents/advisory_agent/agent.py` — Integrated AdvisoryAgent with LLM client, confidence thresholding, and responsible AI validation.
- `backend/app/agents/advisory_agent/response_validator.py` — Integrated Responsible AI grounding checks.
- `backend/app/responsible_ai/__init__.py` — Exported grounding checker.
- `backend/app/orchestrator/agent_registry.py` — Added dynamic `register()` method.
- `backend/app/orchestrator/orchestrator.py` — Connected dynamic `is_demo` indicator.
- `backend/app/schemas/__init__.py` — Re-exported `ConfidenceLabel`.
- `backend/app/retrieval/retrieval_service.py` — Enhanced confidence scaling for zero-lexical match queries.

---

## 3. LLM Provider Architecture & Configuration

```
BaseLLMClient (Abstract Interface)
       ├── StubLLMClient (Safe fallback when unconfigured)
       └── OpenAIAdapter (AsyncOpenAI client)
```

### Configurable Environment Parameters
- `LLM_PROVIDER=openai`
- `LLM_API_KEY=` (Never hardcoded, never logged, never committed)
- `LLM_MODEL=` (Configurable model name, e.g. `gpt-4o-mini`)
- `LLM_MAX_TOKENS=800`
- `LLM_TEMPERATURE=0.1`
- `RETRIEVAL_CONFIDENCE_THRESHOLD=0.15`

### Error Handling
Provider errors are mapped to internal error statuses:
- `LLM_NOT_CONFIGURED`
- `LLM_PROVIDER_ERROR`
- `LLM_TIMEOUT`
- `LLM_INVALID_RESPONSE`

---

## 4. AdvisoryAgent & Grounding Flow

```
User Query
    ↓
Orchestrator (Prompt Injection Guard: assert_safe)
    ↓
ResearchAgent
    ↓
RetrievalService (BM25 + Local Semantic Vector + Hybrid RRF k=60)
    ↓
Source Attribution Validation (filter_attributed_results)
    ↓
EvidenceBundle
    ↓
AdvisoryAgent
    ↓
[Grounded Prompt Construction: <OFFICIAL_EVIDENCE> with [Source N]]
    ↓
LLM Provider (OpenAIAdapter or StubLLMClient)
    ↓
Responsible AI Validation (check_grounding_and_citations)
    ↓
QueryResponse
```

---

## 5. Security & Responsible AI Verification

1. **Anti-Injection Protection**:
   - User queries checked against regex injection patterns via `assert_safe()`.
   - Retrieved evidence placed inside `<OFFICIAL_EVIDENCE>` tags with delimiters sanitized against breakout attempts.
   - System prompt explicitly instructs the LLM that retrieved content is passive DATA, not instructions.
2. **Zero Fabrication**:
   - The Advisory Agent does not perform external web queries.
   - Missing fields are emitted as `NOT_AVAILABLE`.
   - If confidence is below `RETRIEVAL_CONFIDENCE_THRESHOLD (0.15)` or evidence is insufficient, a structured referral to BACP is returned.
3. **Credential Protection**:
   - API keys and authorization headers are never logged or returned by API endpoints.

---

## 6. Build & Test Suite Results

### Backend Test Suite
```
================ 234 passed, 1 skipped, 12 warnings in 13.11s =================
```
- **Previous Tests (Phase 4)**: 213
- **New Tests (Phase 5)**: 22
- **Total Tests**: 235
- **Passed**: 234 (100% of runnable tests)
- **Skipped**: 1 (Live LLM test skipped because `LLM_API_KEY` was not set in local environment)
- **Failed**: 0

### Build Verifications
- **Backend Import**: `from app.main import app` passed with exit code 0.
- **Frontend Build**: `npm run build` completed in 4.92s with 0 errors.

### Live LLM Status
- **Status**: `Live LLM verification skipped — API key not configured.`

---

## 7. Remaining Limitations & Phase 6 Recommendations

### Current Limitations
- **Live LLM Execution**: Requires user to populate `LLM_API_KEY` and `LLM_MODEL` in `.env` to execute live OpenAI completions.
- **Conversation State Storage**: Multi-turn sessions are managed in-memory/database schemas, but full conversational RAG context compaction belongs to future enhancement.

### Recommended Next Steps for Phase 6
1. **Frontend Experience & Chat UI Polish**: Connect live query stream and source citation chips in the frontend UI.
2. **Multi-Turn Contextual RAG**: Pass dialogue history to query expansion and orchestrator workflows.
3. **End-to-End User Acceptance Testing**: Perform live smoke testing across municipal business scenarios once live LLM credentials are provided.
