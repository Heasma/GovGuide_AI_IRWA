"""
GovGuide AI — Agent Communication Protocol Controller

Exposes dedicated REST endpoints demonstrating real inter-agent communication:
- POST /api/v1/agents/query-understanding : Agent 1 (NLP, NER, Intent, Safety)
- POST /api/v1/agents/retrieval           : Agent 2 (BM25, Semantic, Hybrid, RRF)
- POST /api/v1/agents/response-verification: Agent 3 (Grounded Generation, Verification, Citations)
- POST /api/v1/agents/pipeline            : End-to-end multi-agent pipeline with audit trace
- GET  /api/v1/agents/status              : Agent registry status, health, and configurations
"""

import time
import uuid
import structlog
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.orchestrator.agent_registry import AgentRegistry
from app.orchestrator.message_schema import (
    AgentMessage, AgentId, MessageType, TaskType,
    QueryUnderstandingTaskPayload, StructuredQueryPayload,
    RetrievalTaskPayload, RetrievalResultPayload,
    ResponseTaskPayload, ResponseResultPayload,
    ConfidenceLabel, ErrorCode, ErrorPayload,
)
from app.orchestrator.orchestrator import Orchestrator
from app.config import get_settings

router = APIRouter(prefix="/agents", tags=["Agent Communication Protocol"])
logger = structlog.get_logger(__name__)
registry = AgentRegistry()


@router.get(
    "/status",
    summary="Get status and configuration of all registered intelligent agents",
)
async def get_agent_status():
    """
    Returns the registry of intelligent agents and their operational status.
    """
    settings = get_settings()
    agents = registry.list_agents()
    return {
        "status": "online",
        "agent_protocol": "REST / JSON AgentMessage v1.0",
        "registered_agents": [a.value if hasattr(a, "value") else str(a) for a in agents],
        "configuration": {
            "retrieval_mode": settings.RETRIEVAL_MODE,
            "bm25_k1": settings.BM25_K1,
            "bm25_b": settings.BM25_B,
            "rrf_k": settings.RRF_K,
            "confidence_threshold": settings.RETRIEVAL_CONFIDENCE_THRESHOLD,
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.LLM_MODEL or "grounded_synthesis_fallback",
        },
    }


@router.post(
    "/query-understanding",
    response_model=AgentMessage,
    summary="Agent 1: Process natural-language query through Query Understanding Agent",
)
async def query_understanding_endpoint(
    message: AgentMessage,
    current_user: dict = Depends(get_current_user),
):
    """
    Endpoint for Agent 1 (Query Understanding Agent).
    Performs NLP preprocessing, intent classification, entity extraction, and query structure formulation.
    """
    agent = registry.get_agent(AgentId.QUERY_AGENT)
    try:
        response_msg = await agent.process(message)
        return response_msg
    except Exception as exc:
        logger.error("query_agent_endpoint_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query Understanding Agent failed: {str(exc)}",
        )


@router.post(
    "/retrieval",
    response_model=AgentMessage,
    summary="Agent 2: Retrieve ranked government evidence chunks via Retrieval Agent",
)
async def retrieval_endpoint(
    message: AgentMessage,
    current_user: dict = Depends(get_current_user),
):
    """
    Endpoint for Agent 2 (Retrieval Agent).
    Performs hybrid BM25 + Semantic search with Reciprocal Rank Fusion.
    """
    agent = registry.get_agent(AgentId.RETRIEVAL_AGENT)
    try:
        response_msg = await agent.process(message)
        return response_msg
    except Exception as exc:
        logger.error("retrieval_agent_endpoint_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval Agent failed: {str(exc)}",
        )


@router.post(
    "/response-verification",
    response_model=AgentMessage,
    summary="Agent 3: Generate grounded, verified response via Response / Verification Agent",
)
async def response_verification_endpoint(
    message: AgentMessage,
    current_user: dict = Depends(get_current_user),
):
    """
    Endpoint for Agent 3 (Response / Verification Agent).
    Performs LLM inference, evidence grounding verification, citation attachment, and hallucination checks.
    """
    agent = registry.get_agent(AgentId.RESPONSE_AGENT)
    try:
        response_msg = await agent.process(message)
        return response_msg
    except Exception as exc:
        logger.error("response_agent_endpoint_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Response Verification Agent failed: {str(exc)}",
        )


@router.post(
    "/pipeline",
    summary="Execute full end-to-end 3-agent pipeline with execution trace",
)
async def execute_agent_pipeline(
    query_text: str,
    session_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Executes the complete 3-agent communication pipeline sequentially via the agent protocol:
    Query Understanding Agent → Retrieval Agent → Response Verification Agent.
    Returns the final grounded answer with full step-by-step communication traces.
    """
    request_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    trace = []

    # Step 1: Query Understanding Agent
    q_start = time.monotonic()
    query_agent = registry.get_agent(AgentId.QUERY_AGENT)
    q_task = AgentMessage(
        request_id=request_id,
        correlation_id=correlation_id,
        sender=AgentId.ORCHESTRATOR,
        recipient=AgentId.QUERY_AGENT,
        message_type=MessageType.TASK,
        payload=QueryUnderstandingTaskPayload(
            raw_query=query_text,
            session_id=session_id,
        ).model_dump(),
    )
    q_res = await query_agent.process(q_task)
    q_dur = int((time.monotonic() - q_start) * 1000)
    trace.append({
        "step": 1,
        "agent": "query_understanding_agent",
        "status": "completed" if q_res.message_type == MessageType.RESULT else "error",
        "duration_ms": q_dur,
        "intent": q_res.payload.get("intent") if q_res.message_type == MessageType.RESULT else None,
        "entities_found": len(q_res.payload.get("entities", [])) if q_res.message_type == MessageType.RESULT else 0,
    })

    if q_res.message_type == MessageType.ERROR:
        return {
            "request_id": request_id,
            "status": "error",
            "trace": trace,
            "error": q_res.payload,
        }

    # Step 2: Retrieval Agent
    r_start = time.monotonic()
    retrieval_agent = registry.get_agent(AgentId.RETRIEVAL_AGENT)
    r_task = AgentMessage(
        request_id=request_id,
        correlation_id=correlation_id,
        sender=AgentId.QUERY_AGENT,
        recipient=AgentId.RETRIEVAL_AGENT,
        message_type=MessageType.TASK,
        payload=RetrievalTaskPayload(
            structured_query=StructuredQueryPayload(**q_res.payload),
        ).model_dump(),
    )
    r_res = await retrieval_agent.process(r_task)
    r_dur = int((time.monotonic() - r_start) * 1000)
    trace.append({
        "step": 2,
        "agent": "retrieval_agent",
        "status": "completed" if r_res.message_type == MessageType.RESULT else "error",
        "duration_ms": r_dur,
        "evidence_retrieved": r_res.payload.get("evidence_bundle", {}).get("total_retrieved", 0) if r_res.message_type == MessageType.RESULT else 0,
        "retrieval_confidence": r_res.payload.get("retrieval_confidence", 0.0) if r_res.message_type == MessageType.RESULT else 0.0,
    })

    if r_res.message_type == MessageType.ERROR:
        return {
            "request_id": request_id,
            "status": "error",
            "trace": trace,
            "error": r_res.payload,
        }

    # Step 3: Response Verification Agent
    res_start = time.monotonic()
    response_agent = registry.get_agent(AgentId.RESPONSE_AGENT)
    res_task = AgentMessage(
        request_id=request_id,
        correlation_id=correlation_id,
        sender=AgentId.RETRIEVAL_AGENT,
        recipient=AgentId.RESPONSE_AGENT,
        message_type=MessageType.TASK,
        payload=ResponseTaskPayload(
            user_query=query_text,
            structured_query=StructuredQueryPayload(**q_res.payload),
            evidence_bundle=r_res.payload.get("evidence_bundle", {}),
            retrieval_confidence=r_res.payload.get("retrieval_confidence", 0.0),
            sufficient_evidence=r_res.payload.get("sufficient_evidence", False),
        ).model_dump(),
    )
    res_res = await response_agent.process(res_task)
    res_dur = int((time.monotonic() - res_start) * 1000)
    trace.append({
        "step": 3,
        "agent": "response_verification_agent",
        "status": "completed" if res_res.message_type == MessageType.RESULT else "error",
        "duration_ms": res_dur,
        "confidence_label": res_res.payload.get("confidence_label") if res_res.message_type == MessageType.RESULT else None,
        "sources_count": len(res_res.payload.get("sources", [])) if res_res.message_type == MessageType.RESULT else 0,
        "response_validated": res_res.payload.get("response_validated", False) if res_res.message_type == MessageType.RESULT else False,
    })

    return {
        "request_id": request_id,
        "status": "success" if res_res.message_type == MessageType.RESULT else "error",
        "total_duration_ms": q_dur + r_dur + res_dur,
        "trace": trace,
        "final_result": res_res.payload,
    }
