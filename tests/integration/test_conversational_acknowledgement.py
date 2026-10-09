import pytest
from app.orchestrator.orchestrator import Orchestrator
from app.nlp.query_understanding_service import QueryUnderstandingService
from app.nlp.intent_classifier import is_conversational_query, classify_intents, classify_conversation_type
from app.orchestrator.message_schema import Intent


@pytest.mark.asyncio
async def test_conversational_acknowledgements_intent():
    qu_service = QueryUnderstandingService()

    ack_queries = [
        "ok",
        "okay",
        "ok thanks",
        "okay thank you",
        "thank you",
        "thanks",
        "thanks a lot",
        "thank you so much",
        "got it",
        "alright",
        "great",
        "understood",
        "seri",
        "sari",
        "nandri",
        "thanks bro",
        "seri thanks",
        "ok thank you",
    ]

    for q in ack_queries:
        res = qu_service.understand_query(q, context_entity="Retail Food Establishment License")
        assert res.is_conversational is True, f"Failed is_conversational for '{q}'"
        assert res.search_parameters.get("retrieval_required") is False, f"Failed retrieval_required=False for '{q}'"
        # Context entity must be preserved in search_parameters for the session
        assert res.search_parameters.get("active_entity_preserved") is True or res.search_parameters.get("resolved_context_entity") is not None


@pytest.mark.asyncio
async def test_substantive_followups_not_conversational():
    qu_service = QueryUnderstandingService()

    substantive_queries = [
        "what documents for this?",
        "how much is it?",
        "what is the eligibility?",
        "how do I apply?",
        "ithukku documents enna?",
        "ithoda fee evvalavu?",
    ]

    for q in substantive_queries:
        res = qu_service.understand_query(q, context_entity="1006")
        assert res.is_conversational is False, f"Expected non-conversational for '{q}'"
        assert res.search_parameters.get("retrieval_required") is True, f"Expected retrieval_required=True for '{q}'"
        assert res.search_parameters.get("resolved_service_code") == "1006", f"Expected resolved_service_code=1006 for '{q}', got {res.search_parameters.get('resolved_service_code')}"


@pytest.mark.asyncio
async def test_orchestrator_conversational_and_context_flow():
    orchestrator = Orchestrator()

    # 1. User says cake business
    resp1 = await orchestrator.process_query("naan oru cake business start pannaum")
    assert resp1.is_conversational is False
    assert "1006" in resp1.answer or "Retail Food" in resp1.answer

    # 2. User says ok thank you
    resp2 = await orchestrator.process_query("ok thank you", context_entity="1006")
    assert resp2.is_conversational is True
    assert "You're welcome!" in resp2.answer
    assert "1006" not in resp2.answer  # Must NOT retrieve service again

    # 3. User asks follow-up for documents
    resp3 = await orchestrator.process_query("ithukku enna documents venum apply pannurathukku", context_entity="1006")
    assert resp3.is_conversational is False
    assert "1006" in resp3.answer or "Retail Food" in resp3.answer
    assert "Document" in resp3.answer or "document" in resp3.answer or "Plan" in resp3.answer

    # 4. User asks follow-up for fees
    resp4 = await orchestrator.process_query("ithukku fees evvalavu?", context_entity="1006")
    assert resp4.is_conversational is False
    assert "1006" in resp4.answer or "Retail Food" in resp4.answer
    assert "Fee" in resp4.answer or "fee" in resp4.answer or "$" in resp4.answer

    # 5. Secondary sports license (7035) grounding
    resp5 = await orchestrator.process_query("what is the eligibility for secondary sports?")
    assert resp5.is_conversational is False
    assert "7035" in resp5.answer
    assert "1010" not in resp5.answer  # Strict grounding

    # 6. 56 services catalog
    resp6 = await orchestrator.process_query("I need 56 government service summary")
    assert resp6.is_conversational is False
    assert "56" in resp6.answer or len(resp6.sources) >= 50 or "Catalog" in resp6.answer


@pytest.mark.asyncio
async def test_vague_license_inquiries_clarification():
    orchestrator = Orchestrator()
    qu_service = QueryUnderstandingService()

    # Case A: "i need some help to regarding to thre licence" -> clarification, NOT 1006
    q_a = "i need some help to regarding to thre licence"
    res_a = qu_service.understand_query(q_a)
    assert res_a.search_parameters.get("needs_clarification") is True
    assert res_a.search_parameters.get("resolved_service_code") is None
    resp_a = await orchestrator.process_query(q_a)
    assert "Which license are you asking about?" in resp_a.answer or "business type" in resp_a.answer.lower()
    assert "1006" not in resp_a.answer
    assert "Retail Food" not in resp_a.answer

    # Case B: "i need help with the license" -> clarification
    q_b = "i need help with the license"
    res_b = qu_service.understand_query(q_b)
    assert res_b.search_parameters.get("needs_clarification") is True
    assert res_b.search_parameters.get("resolved_service_code") is None
    resp_b = await orchestrator.process_query(q_b)
    assert "Which license are you asking about?" in resp_b.answer or "business type" in resp_b.answer.lower()
    assert "1006" not in resp_b.answer

    # Case C: "ennaku licence pathi help venum" -> clarification
    q_c = "ennaku licence pathi help venum"
    res_c = qu_service.understand_query(q_c)
    assert res_c.search_parameters.get("needs_clarification") is True
    assert res_c.search_parameters.get("resolved_service_code") is None
    resp_c = await orchestrator.process_query(q_c)
    assert "endha licence" in resp_c.answer or "business type" in resp_c.answer.lower() or "Which license" in resp_c.answer
    assert "Retail Food" not in resp_c.answer

    # Case D: "I want to start a cake business" -> 1006
    q_d = "I want to start a cake business"
    resp_d = await orchestrator.process_query(q_d)
    assert "1006" in resp_d.answer or "Retail Food" in resp_d.answer

    # Case E: "ithukku enna documents venum?" after cake business context -> 1006 documents
    q_e = "ithukku enna documents venum?"
    resp_e = await orchestrator.process_query(q_e, context_entity="1006")
    assert "1006" in resp_e.answer or "Retail Food" in resp_e.answer
    assert any(term in resp_e.answer.lower() for term in ["document", "lease", "entity", "sanitation"])

    # Case F: "thank you" -> conversational acknowledgement
    q_f = "thank you"
    resp_f = await orchestrator.process_query(q_f, context_entity="1006")
    assert resp_f.is_conversational is True
    assert "You're welcome!" in resp_f.answer
    assert "1006" not in resp_f.answer

    # Case G: "ok" -> conversational acknowledgement
    q_g = "ok"
    resp_g = await orchestrator.process_query(q_g, context_entity="1006")
    assert resp_g.is_conversational is True
    assert "You're welcome!" in resp_g.answer
    assert "1006" not in resp_g.answer

