"""
GovGuide AI — Unit Tests: Domain Detector & Classifier

Tests:
1. Classification of driver license queries and natural variations
2. Classification of supported business license and government service queries
3. Classification of out-of-domain queries (aviation, tax, health, education)
4. DomainDetector component behavior and domain support validation
"""

import pytest
from app.nlp.domain_detector import (
    classify_domain,
    is_domain_supported,
    DomainDetector,
    SUPPORTED_DOMAINS,
    UNSUPPORTED_DOMAINS,
)
from app.orchestrator.message_schema import Domain


def test_driver_license_variations():
    queries = [
        "I need drive car so what type of licence?",
        "I need to drive a car, what type of licence?",
        "What driving licence do I need?",
        "Which licence is required to drive a car?",
        "What class licence do I need for a car?",
        "How can I get a driving licence?",
        "What type of driver's license do I need?",
        "How do I apply for a driver licence at the DMV?",
        "What is the procedure for a learner's permit?",
        "Where do I take the driving test for a car?",
    ]
    for q in queries:
        detected = classify_domain(q)
        assert detected == Domain.DRIVER_LICENSE, f"Failed on query: '{q}', got {detected}"
        assert not is_domain_supported(detected), f"Driver license must be unsupported in local BACP dataset: '{q}'"


def test_aviation_queries():
    queries = [
        "What licence do I need to fly a helicopter?",
        "How to get a pilot license?",
        "FAA license requirements for flying an airplane",
    ]
    for q in queries:
        detected = classify_domain(q)
        assert detected == Domain.AVIATION, f"Failed on query: '{q}', got {detected}"
        assert not is_domain_supported(detected)


def test_tax_and_health_queries():
    assert classify_domain("How do I file my personal income tax with the IRS?") == Domain.TAX
    assert not is_domain_supported(Domain.TAX)

    assert classify_domain("How can I apply for Medicaid health insurance?") == Domain.HEALTH
    assert not is_domain_supported(Domain.HEALTH)

    assert classify_domain("How to apply for FAFSA student loan?") == Domain.EDUCATION
    assert not is_domain_supported(Domain.EDUCATION)


def test_business_license_queries():
    queries = [
        "What business license do I need to open a restaurant?",
        "What license is required for a mobile food business?",
        "How do I apply for a retail food establishment license?",
        "What is the fee for a tavern liquor license in Chicago?",
        "Limited business license requirements for retail store",
        "Public place of amusement PPA license application",
    ]
    for q in queries:
        detected = classify_domain(q)
        assert detected == Domain.BUSINESS_LICENSE, f"Failed on query: '{q}', got {detected}"
        assert is_domain_supported(detected)


def test_government_service_queries():
    queries = [
        "Where is City Hall located and what are the office hours?",
        "Contact information for City of Chicago Small Business Center Room 800",
    ]
    for q in queries:
        detected = classify_domain(q)
        assert detected == Domain.GOVERNMENT_SERVICE, f"Failed on query: '{q}', got {detected}"
        assert is_domain_supported(detected)


def test_domain_detector_class():
    detector = DomainDetector()
    domain, supported = detector.detect("I need drive car so what type of licence?")
    assert domain == Domain.DRIVER_LICENSE
    assert supported is False

    domain_biz, supported_biz = detector.detect("What business license do I need to open a restaurant?")
    assert domain_biz == Domain.BUSINESS_LICENSE
    assert supported_biz is True
