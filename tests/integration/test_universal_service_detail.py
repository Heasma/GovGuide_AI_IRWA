import pytest
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.message_schema import Intent


@pytest.fixture
def orchestrator():
    return Orchestrator()


@pytest.mark.asyncio
async def test_matrix_a_service_overview(orchestrator):
    """A. Service overview: 'tell me about secondary sports'"""
    result = await orchestrator.process_query("tell me about secondary sports")
    assert "Secondary Sports License" in result.answer
    assert "7035" in result.answer
    assert "Overview" in result.answer
    assert "Eligibility" in result.answer
    assert "Required Documents" in result.answer
    assert "Fees" in result.answer
    assert "Renewal" in result.answer
    assert "Responsible Office" in result.answer


@pytest.mark.asyncio
async def test_matrix_b_eligibility(orchestrator):
    """B. Eligibility: 'what is the eligibility for secondary sports'"""
    result = await orchestrator.process_query("what is the eligibility for secondary sports")
    assert "Secondary Sports License" in result.answer
    assert "7035" in result.answer
    assert "Eligibility" in result.answer


@pytest.mark.asyncio
async def test_matrix_c_documents(orchestrator):
    """C. Documents: 'what documents are needed for secondary sports'"""
    result = await orchestrator.process_query("what documents are needed for secondary sports")
    assert "Secondary Sports License" in result.answer
    assert "7035" in result.answer
    assert "Required Documents" in result.answer


@pytest.mark.asyncio
async def test_matrix_d_procedure(orchestrator):
    """D. Procedure: 'how to apply for secondary sports'"""
    result = await orchestrator.process_query("how to apply for secondary sports")
    assert "Secondary Sports License" in result.answer
    assert "7035" in result.answer
    assert "Application Procedure" in result.answer


@pytest.mark.asyncio
async def test_matrix_e_fees(orchestrator):
    """E. Fees: 'how much is secondary sports license'"""
    result = await orchestrator.process_query("how much is secondary sports license")
    assert "Secondary Sports License" in result.answer
    assert "7035" in result.answer
    assert "Fees" in result.answer


@pytest.mark.asyncio
async def test_matrix_f_renewal(orchestrator):
    """F. Renewal: 'how to renew secondary sports'"""
    result = await orchestrator.process_query("how to renew secondary sports")
    assert "Secondary Sports License" in result.answer
    assert "7035" in result.answer
    assert "Renewal" in result.answer


@pytest.mark.asyncio
async def test_matrix_g_code(orchestrator):
    """G. Code: 'what is license 7035'"""
    result = await orchestrator.process_query("what is license 7035")
    assert "Secondary Sports License" in result.answer
    assert "7035" in result.answer


@pytest.mark.asyncio
async def test_matrix_h_partial_name(orchestrator):
    """H. Partial service name: 'secondary sports'"""
    result = await orchestrator.process_query("secondary sports")
    assert "Secondary Sports License" in result.answer
    assert "7035" in result.answer


@pytest.mark.asyncio
async def test_matrix_i_typo(orchestrator):
    """I. Typo: 'secondery sports'"""
    result = await orchestrator.process_query("secondery sports")
    assert "Secondary Sports License" in result.answer
    assert "7035" in result.answer


@pytest.mark.asyncio
async def test_matrix_j_generic_service_query(orchestrator):
    """J. Generic: 'I need to know about service'"""
    result = await orchestrator.process_query("I need to know about service")
    assert "Which government service would you like to know about?" in result.answer


@pytest.mark.asyncio
async def test_matrix_k_unknown_service(orchestrator):
    """K. Unknown: 'tell me about ABCXYZ service'"""
    result = await orchestrator.process_query("tell me about ABCXYZ service")
    assert "couldn't find a matching verified government service for 'abcxyz'" in result.answer.lower()
    # Must NOT hallucinate or map to unrelated licenses like 1010
    assert "1010" not in result.answer
    assert "Limited Business" not in result.answer


@pytest.mark.asyncio
async def test_matrix_l_regression_56_catalog(orchestrator):
    """L. Existing regression: 'I need 56 government service summary'"""
    result = await orchestrator.process_query("I need 56 government service summary")
    assert "56" in result.answer or "government services" in result.answer
    # Make sure multiple services are listed
    assert "Secondary Sports License" in result.answer
    assert "Retail Food" in result.answer


@pytest.mark.asyncio
async def test_cross_service_contamination():
    """
    13. CROSS-SERVICE CONTAMINATION TEST:
    For every service-specific query, assert that all retrieved evidence.service_code
    matches the resolved canonical service_code.
    """
    from app.retrieval.retrieval_service import get_retrieval_service

    service = get_retrieval_service()

    test_cases = [
        ("tell me about secondary sports", "7035"),
        ("what is the eligibility for secondary sports", "7035"),
        ("what documents are needed for secondary sports", "7035"),
        ("how to apply for secondary sports", "7035"),
        ("tell me about tavern license", "1470"),
        ("tell me about restaurant license", "1006"),
        ("tell me about tobacco license", "1781"),
    ]

    for query, expected_code in test_cases:
        res = service.search(query, target_service=expected_code)
        assert len(res.results) > 0, f"Expected evidence for {query}"
        for chunk in res.results:
            assert chunk.service_code == expected_code, (
                f"Contamination detected! Query '{query}' (expected {expected_code}) "
                f"retrieved chunk for service_code {chunk.service_code}"
            )
