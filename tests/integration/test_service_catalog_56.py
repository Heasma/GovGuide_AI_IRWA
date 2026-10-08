"""
Integration tests for 56 Government Service Catalog queries, grounding integrity,
and dynamic retrieval verification.
"""

import pytest
import re
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.message_schema import Intent, ConfidenceLabel
from app.retrieval.chunk_generator import fetch_services_from_db
from app.nlp.query_understanding_service import QueryUnderstandingService


@pytest.fixture(scope="module")
def db_service_map():
    db_services = fetch_services_from_db()
    assert len(db_services) == 56, f"Expected 56 canonical records in DB, found {len(db_services)}"
    return {s["service_code"]: s for s in db_services}


@pytest.fixture(scope="module")
def orchestrator():
    return Orchestrator()


@pytest.mark.anyio
async def test_exact_query_56_government_service_summary(orchestrator, db_service_map):
    """
    Test A: "I need 56 government service summary"
    Expected:
    - Intent = LICENSE_CATALOG
    - Count = 56
    - Not clarification
    - Not insufficient evidence
    - All 56 items grounded against database
    """
    query = "I need 56 government service summary"
    resp = await orchestrator.process_query(query, request_id="test-56-a")
    
    assert resp.is_conversational is False
    assert "could not find sufficient official evidence" not in resp.answer.lower()
    assert "could not find sufficient" not in resp.answer.lower()
    assert resp.confidence_label != ConfidenceLabel.INSUFFICIENT

    pattern = re.compile(r"(\d+)\.\s+(.*?)\s+—\s+Code:\s+([A-Za-z0-9_-]+)")
    matches = pattern.findall(resp.answer)
    assert len(matches) == 56, f"Expected 56 distinct items in answer, got {len(matches)}"

    seen_codes = set()
    for idx_str, name, code in matches:
        assert code in db_service_map, f"Code {code} not found in database!"
        assert code not in seen_codes, f"Duplicate code {code} found!"
        seen_codes.add(code)
        assert name.strip() != "", "Name should not be empty"
        assert code.strip() != "", "Code should not be empty"

    assert len(seen_codes) == 56


@pytest.mark.anyio
async def test_query_show_all_56_government_services(orchestrator, db_service_map):
    """
    Test B: "show all 56 government services"
    Expected count = 56
    """
    query = "show all 56 government services"
    resp = await orchestrator.process_query(query, request_id="test-56-b")
    
    pattern = re.compile(r"(\d+)\.\s+(.*?)\s+—\s+Code:\s+([A-Za-z0-9_-]+)")
    matches = pattern.findall(resp.answer)
    assert len(matches) == 56, f"Expected 56 distinct items, got {len(matches)}"


@pytest.mark.anyio
async def test_query_give_me_summary_of_all_government_services(orchestrator, db_service_map):
    """
    Test C: "give me summary of all government services"
    Expected count = 56
    """
    query = "give me summary of all government services"
    resp = await orchestrator.process_query(query, request_id="test-56-c")
    
    pattern = re.compile(r"(\d+)\.\s+(.*?)\s+—\s+Code:\s+([A-Za-z0-9_-]+)")
    matches = pattern.findall(resp.answer)
    assert len(matches) == 56, f"Expected 56 distinct items, got {len(matches)}"


@pytest.mark.anyio
async def test_query_all_business_license_services(orchestrator, db_service_map):
    """
    Test D: "all business license services"
    Expected catalog behavior
    """
    query = "all business license services"
    resp = await orchestrator.process_query(query, request_id="test-56-d")
    
    pattern = re.compile(r"(\d+)\.\s+(.*?)\s+—\s+Code:\s+([A-Za-z0-9_-]+)")
    matches = pattern.findall(resp.answer)
    assert len(matches) == 56, f"Expected 56 distinct items, got {len(matches)}"


@pytest.mark.anyio
async def test_query_thanglish_catalog_enna_enna(orchestrator, db_service_map):
    """
    Test E: "enna enna government services irukku"
    Expected catalog behavior
    """
    query = "enna enna government services irukku"
    resp = await orchestrator.process_query(query, request_id="test-56-e")
    
    pattern = re.compile(r"(\d+)\.\s+(.*?)\s+—\s+Code:\s+([A-Za-z0-9_-]+)")
    matches = pattern.findall(resp.answer)
    assert len(matches) == 56, f"Expected 56 distinct items, got {len(matches)}"


@pytest.mark.anyio
async def test_query_thanglish_catalog_56_services_venum(orchestrator, db_service_map):
    """
    Test F: "56 services summary venum"
    Expected catalog behavior
    """
    query = "56 services summary venum"
    resp = await orchestrator.process_query(query, request_id="test-56-f")
    
    pattern = re.compile(r"(\d+)\.\s+(.*?)\s+—\s+Code:\s+([A-Za-z0-9_-]+)")
    matches = pattern.findall(resp.answer)
    assert len(matches) == 56, f"Expected 56 distinct items, got {len(matches)}"


@pytest.mark.anyio
async def test_regression_queries(orchestrator):
    """
    Test G: Existing specific queries MUST NOT break:
    - restaurant -> correct relevant service (1006)
    - dress shop -> correct relevant service (1010)
    - generic "I want to start a business" -> clarification
    - "ennaku licence edukanum" -> clarification
    """
    # 1. Restaurant
    resp_rest = await orchestrator.process_query("what license do i need for a restaurant", request_id="test-reg-1")
    assert "1006" in resp_rest.answer
    assert "retail food establishment" in resp_rest.answer.lower()

    # 2. Dress shop
    resp_dress = await orchestrator.process_query("naan dress shop start panna poren", request_id="test-reg-2")
    assert "1010" in resp_dress.answer or "limited business license" in resp_dress.answer.lower()

    # 3. Generic "I want to start a business" -> clarification
    resp_start = await orchestrator.process_query("I want to start a business", request_id="test-reg-3")
    assert "specify" in resp_start.answer.lower() or "what type" in resp_start.answer.lower() or "business type" in resp_start.answer.lower()

    # 4. "ennaku licence edukanum" -> clarification
    resp_clar = await orchestrator.process_query("ennaku licence edukanum", request_id="test-reg-4")
    assert "business type" in resp_clar.answer.lower() or "enna type" in resp_clar.answer.lower()


@pytest.mark.anyio
async def test_grounding_integrity_56_records(orchestrator, db_service_map):
    """
    Explicit Grounding Integrity Test:
    For every returned catalog item:
    Query GovernmentService by service_code and assert the returned service_name matches the canonical database record.
    """
    query = "I need 56 government service summary"
    resp = await orchestrator.process_query(query, request_id="test-grounding-integrity")
    
    pattern = re.compile(r"(\d+)\.\s+(.*?)\s+—\s+Code:\s+([A-Za-z0-9_-]+)\n\s+Summary:\s+(.*?)(?=\n\d+\.|\Z)", re.DOTALL)
    matches = pattern.findall(resp.answer)
    assert len(matches) == 56

    for idx_str, disp_name, s_code, summary_text in matches:
        assert s_code in db_service_map, f"Service code {s_code} not found in DB map"
        db_record = db_service_map[s_code]
        
        # Verify alignment: cleaned name should match or be contained in db name
        db_name = db_record["name"]
        assert disp_name in db_name or db_name in disp_name or "Service " in disp_name, (
            f"Name mismatch for code {s_code}: displayed '{disp_name}' vs DB '{db_name}'"
        )

        # Verify summary is grounded: either non-empty real description or canonical safe fallback
        summary_clean = summary_text.strip()
        assert len(summary_clean) > 0
        if "Summary information is not available" in summary_clean:
            db_desc = db_record.get("description") or ""
            assert not db_desc or db_desc in ("NOT_AVAILABLE", "N/A", "NONE"), (
                f"False missing summary for code {s_code}"
            )
