"""
Unit tests — QueryService
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.query_service import QueryService
from app.schemas import QueryResponse, SourceReference


@pytest.mark.anyio
async def test_process_query_success():
    db = AsyncMock()
    query = "What citizen services are available?"
    session_id = "sess-123"
    user_id = "user-456"
    ip_address = "192.168.1.1"

    mock_orchestrator_response = QueryResponse(
        request_id="req-123",
        answer="These are the available services.",
        confidence_score=0.95,
        confidence_label="high",
        sources=[SourceReference(source_id="src-1", title="Official Portal", url="http://gov.info", excerpt="services...")],
        caveats=["Always double check."],
        explanation="Validated against official source.",
        is_demo=True,
    )

    with patch("app.services.query_service.log_query") as mock_log_query, \
         patch("app.orchestrator.orchestrator.Orchestrator.process_query", new_callable=AsyncMock) as mock_process_query:
        
        mock_process_query.return_value = mock_orchestrator_response

        response = await QueryService.process_query(
            db=db,
            query=query,
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
        )

        assert response.request_id == "req-123"
        assert response.answer == "These are the available services."
        assert response.confidence_score == 0.95
        assert response.confidence_label == "high"
        assert len(response.sources) == 1
        assert response.is_demo is True

        mock_log_query.assert_called_once()
        mock_process_query.assert_called_once()
        
        # Verify call arguments
        call_args = mock_process_query.call_args[1]
        assert call_args["query"] == query
        assert call_args["session_id"] == session_id
        assert call_args["user_id"] == user_id
