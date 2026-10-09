"""
GovGuide AI — Unit Tests: Strict Domain Restriction & Out-of-Domain Detection

Verifies that GovGuide AI strictly gates and refuses out-of-domain / unrelated queries
in English, Thanglish, Tamil, and Sinhala, while preserving valid licensing functionality.
"""

import pytest
from app.nlp.domain_detector import (
    classify_domain,
    is_domain_supported,
    get_out_of_domain_response,
    OUT_OF_DOMAIN_EN,
    OUT_OF_DOMAIN_THANGLISH,
    OUT_OF_DOMAIN_TAMIL,
    OUT_OF_DOMAIN_SINHALA,
    SUPPORTED_DOMAINS,
    UNSUPPORTED_DOMAINS,
)
from app.nlp.query_understanding_service import QueryUnderstandingService
from app.orchestrator.message_schema import Domain, Intent


@pytest.fixture
def qu_service():
    return QueryUnderstandingService()


# ── 1. Unrelated English Questions ───────────────────────────────────────────
def test_unrelated_english_domain_classification(qu_service):
    unrelated_queries = [
        "Who will win the cricket match?",
        "How do I cook biryani?",
        "Tell me a joke.",
        "Which mobile phone is best?",
        "Explain a mathematics problem.",
        "What is the capital of Australia?",
        "How to lose weight fast in 2 weeks?",
        "Write a poem about the sunrise.",
        "What is the score of the football game?",
        "How do I solve quadratic equations?",
    ]

    for q in unrelated_queries:
        domain = classify_domain(q)
        assert domain in UNSUPPORTED_DOMAINS, f"Query '{q}' classified as supported domain {domain}"
        assert not is_domain_supported(domain), f"Query '{q}' domain must not be supported"

        res = qu_service.understand_query(q)
        assert res.is_domain_supported is False, f"QueryUnderstandingService failed is_domain_supported=False for '{q}'"
        assert res.search_parameters.get("retrieval_required") is False, f"Retrieval must not be required for '{q}'"
        assert res.search_parameters.get("needs_clarification") is False, f"Must not ask clarification for unrelated '{q}'"


# ── 2. Unrelated Thanglish Questions ─────────────────────────────────────────
def test_unrelated_thanglish_domain_classification(qu_service):
    thanglish_unrelated = [
        "Cricket eppidi villadurathu?",
        "Cricket eppidi vilayaduvathu?",
        "Biryani eppidi samaikiradhu?",
        "Biryani eppadi samayal seivathu?",
        "Mobile phone edhu nalladhu?",
        "Oru joke sollu",
        "Kadhai onnu sollu bro",
        "IPL match la yaar win pannuva?",
    ]

    for q in thanglish_unrelated:
        domain = classify_domain(q)
        assert domain in UNSUPPORTED_DOMAINS, f"Thanglish query '{q}' classified as supported domain {domain}"
        assert not is_domain_supported(domain), f"Thanglish query '{q}' domain must not be supported"

        res = qu_service.understand_query(q)
        assert res.is_domain_supported is False, f"QueryUnderstandingService failed is_domain_supported=False for '{q}'"
        assert res.search_parameters.get("retrieval_required") is False, f"Retrieval must not be required for '{q}'"
        assert res.search_parameters.get("needs_clarification") is False, f"Must not ask clarification for unrelated '{q}'"


# ── 3. Unrelated Tamil & Sinhala Script Questions ────────────────────────────
def test_unrelated_tamil_and_sinhala_script(qu_service):
    tamil_queries = [
        "கிரிக்கெட் போட்டி யார் வெல்வார்கள்?",
        "பிரியாணி செய்வது எப்படி?",
        "ஒரு நகைச்சுவை சொல்லுங்கள்",
    ]
    for q in tamil_queries:
        domain = classify_domain(q)
        assert domain in UNSUPPORTED_DOMAINS, f"Tamil query '{q}' must be unsupported"
        assert not is_domain_supported(domain)

    sinhala_queries = [
        "ක්‍රිකට් තරගය දිනන්නේ කවුද?",
        "බිරියානි උයන්නේ කෙසේද?",
        "විහිළුවක් කියන්න",
    ]
    for q in sinhala_queries:
        domain = classify_domain(q)
        assert domain in UNSUPPORTED_DOMAINS, f"Sinhala query '{q}' must be unsupported"
        assert not is_domain_supported(domain)


# ── 4. Standardized Response String Templates ────────────────────────────────
def test_out_of_domain_response_templates():
    assert get_out_of_domain_response("en") == OUT_OF_DOMAIN_EN
    assert "Sorry, GovGuide AI does not provide information on this topic." in OUT_OF_DOMAIN_EN
    assert "business licences" in OUT_OF_DOMAIN_EN

    assert get_out_of_domain_response("thanglish") == OUT_OF_DOMAIN_THANGLISH
    assert "Mannikkavum, indha topic pathina information GovGuide AI system-la available illa." in OUT_OF_DOMAIN_THANGLISH
    assert "business licences" in OUT_OF_DOMAIN_THANGLISH

    assert get_out_of_domain_response("tamil") == OUT_OF_DOMAIN_TAMIL
    assert "மன்னிக்கவும், இந்த தலைப்பு குறித்த தகவல்கள் GovGuide AI அமைப்பில் கிடைக்கவில்லை." in OUT_OF_DOMAIN_TAMIL

    assert get_out_of_domain_response("sinhala") == OUT_OF_DOMAIN_SINHALA
    assert "සමාවන්න, මෙම මාතෘකාව පිළිබඳ තොරතුරු GovGuide AI පද්ධතියේ නොමැත." in OUT_OF_DOMAIN_SINHALA


# ── 5. Preserving Valid Business License Queries ──────────────────────────────
def test_valid_business_license_queries(qu_service):
    valid_queries = [
        "What business license do I need to open a restaurant?",
        "How do I apply for a retail food establishment license?",
        "What is the fee for a tavern liquor license in Chicago?",
        "Required documents for a limited business license",
        "How often do I need to renew my mobile food vendor license?",
        "Where is the Small Business Center City Hall office?",
        "Public place of amusement PPA license application procedure",
        "Massage establishment license eligibility requirements",
        "Auto repair garage business license fee",
    ]

    for q in valid_queries:
        domain = classify_domain(q)
        assert domain in SUPPORTED_DOMAINS, f"Valid query '{q}' was classified as {domain}"
        assert is_domain_supported(domain) is True

        res = qu_service.understand_query(q)
        assert res.is_domain_supported is True
        assert res.search_parameters.get("retrieval_required") is True


# ── 6. Context Entity Gating: Unrelated query must drop context entity ─────────
def test_unrelated_query_drops_context_entity(qu_service):
    # If user was talking about Retail Food (Code 1006) and suddenly asks an unrelated question
    unrelated_with_context = [
        ("Who will win the cricket match?", "Retail Food Establishment License"),
        ("Cricket eppidi villadurathu?", "Retail Food Establishment License"),
        ("How do I cook biryani?", "1006"),
        ("Tell me a joke.", "Tavern License"),
        ("Which mobile phone is best?", "Limited Business License"),
    ]

    for q, ctx in unrelated_with_context:
        res = qu_service.understand_query(q, context_entity=ctx)
        assert res.is_domain_supported is False, f"Unrelated query '{q}' with context '{ctx}' must remain unsupported"
        assert res.search_parameters.get("retrieval_required") is False
        assert res.search_parameters.get("resolved_service_code") is None, f"Must not attach resolved_service_code for '{q}'"
        assert len(res.entities) == 0, f"Must not attach entity for unrelated '{q}'"


# ── 7. Context Entity Preservation for Genuine Follow-ups ─────────────────────
def test_genuine_followup_preserves_context_entity(qu_service):
    valid_followups = [
        ("What about the fees?", "Retail Food Establishment License"),
        ("How much is it?", "Retail Food Establishment License"),
        ("What documents are required?", "Tavern License"),
        ("How do I apply for it?", "Limited Business License"),
        ("Where is the office to submit?", "Retail Food Establishment License"),
        ("How often to renew?", "Children's Services Facility License"),
        ("ithukku documents enna?", "1006"),
        ("ithoda fee evvalavu?", "1006"),
    ]

    for q, ctx in valid_followups:
        res = qu_service.understand_query(q, context_entity=ctx)
        assert res.is_domain_supported is True, f"Genuine follow-up '{q}' with context '{ctx}' must be supported"
        assert res.search_parameters.get("retrieval_required") is True


# ── 8. Ambiguous Licensing Queries Trigger Clarification ─────────────────────
def test_ambiguous_licensing_queries(qu_service):
    ambiguous_queries = [
        "I want to start a business",
        "What license do I need?",
        "Do I need a permit?",
        "How do I get a license?",
        "Business start panna enna pannanum?",
        "Shop open panna enna license venum?",
    ]

    for q in ambiguous_queries:
        res = qu_service.understand_query(q)
        assert res.is_domain_supported is True
        assert res.search_parameters.get("needs_clarification") is True
        assert res.search_parameters.get("retrieval_required") is False
