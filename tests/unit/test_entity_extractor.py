"""
GovGuide AI — Unit Tests: Entity Extractor & Named Entity Recognition
"""

import pytest
from app.nlp.entity_extractor import extract_entities, ExtractedEntity


def test_extract_service_entities():
    query = "How do I apply for a Retail Food Establishment License for my new restaurant?"
    entities = extract_entities(query)
    labels = [e.label for e in entities]
    texts = [e.text.lower() for e in entities]

    assert "SERVICE" in labels
    assert any("retail food" in t for t in texts)


def test_extract_organization_entities():
    query = "Where is the Department of Business Affairs and Consumer Protection located?"
    entities = extract_entities(query)
    org_entities = [e for e in entities if e.label == "ORGANIZATION"]

    assert len(org_entities) > 0
    assert any("department of business affairs" in e.text.lower() or "bacp" in e.text.lower() for e in org_entities)


def test_extract_license_codes():
    query = "What are the rules for license code 1006 and 1010 in Chicago?"
    entities = extract_entities(query)
    code_entities = [e for e in entities if e.label == "LICENSE_CODE"]

    codes = [e.text for e in code_entities]
    assert "1006" in codes
    assert "1010" in codes


def test_extract_fees_and_periods():
    query = "Is there a $660 fee for the 2 years biennial renewal?"
    entities = extract_entities(query)
    fee_entities = [e for e in entities if e.label == "FEE_AMOUNT"]
    period_entities = [e for e in entities if e.label == "DATE_PERIOD"]

    assert len(fee_entities) > 0
    assert any("$660" in e.text or "660" in e.text for e in fee_entities)
    assert len(period_entities) > 0
    assert any("2 years" in e.text or "biennial" in e.text for e in period_entities)


def test_extract_location_entities():
    query = "Can I apply at City Hall on 121 N LaSalle St in Chicago?"
    entities = extract_entities(query)
    loc_entities = [e for e in entities if e.label == "LOCATION"]

    assert len(loc_entities) >= 2
    loc_texts = [e.text.lower() for e in loc_entities]
    assert any("chicago" in t for t in loc_texts)
    assert any("city hall" in t or "lasalle" in t for t in loc_texts)


def test_empty_query():
    assert extract_entities("") == []
