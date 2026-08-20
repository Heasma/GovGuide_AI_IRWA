"""
GovGuide AI — Unit Tests: BM25 Retriever

Tests:
- Okapi BM25 index creation
- Keyword and phrase matching
- Exact license code boost (e.g. '1006', '1010')
- Empty query handling
- Top-K result limiting and score sorting
- Source attribution retention
"""

import uuid
import pytest
from app.retrieval.document_builder import build_service_document
from app.retrieval.chunker import chunk_document
from app.retrieval.bm25_retriever import BM25Retriever, tokenize


@pytest.fixture
def sample_retriever():
    services = [
        {
            "id": str(uuid.uuid4()),
            "service_code": "1006",
            "name": "Apply for a Retail Food Establishment License",
            "category": "Food & Beverage",
            "description": "Required for restaurants, bakeries, cafes, and food vendors in Chicago.",
            "source_url": "https://www.chicago.gov/RetailFood",
            "fee_amount": "$660.00",
            "required_documents": "Health certificate, food sanitation manager certification",
            "application_steps": "Apply online, pass health inspection, pay fee",
        },
        {
            "id": str(uuid.uuid4()),
            "service_code": "1010",
            "name": "Apply for a Limited Business License (LBL)",
            "category": "Retail & General",
            "description": "General retail store and professional service license.",
            "source_url": "https://www.chicago.gov/LBL",
            "fee_amount": "$500.00",
            "required_documents": "Lease agreement, business registration",
            "application_steps": "Apply via Chicago Business Direct, zoning approval",
        },
        {
            "id": str(uuid.uuid4()),
            "service_code": "1781",
            "name": "Apply for a Tobacco License",
            "category": "Tobacco",
            "description": "Retail sale of cigarettes, cigars, electronic cigarettes, and tobacco products.",
            "source_url": "https://www.chicago.gov/Tobacco",
            "fee_amount": "$1,000.00",
            "required_documents": "State tobacco license, zoning verification",
            "application_steps": "Undergo background check, submit application",
        },
    ]

    chunks = []
    for s in services:
        doc = build_service_document(s)
        chunks.extend(chunk_document(doc))

    return BM25Retriever(chunks=chunks)


def test_bm25_tokenization():
    tokens = tokenize("How do I apply for a Retail Food License (Code 1006)?", remove_stopwords=True)
    assert "retail" in tokens
    assert "food" in tokens
    assert "license" in tokens
    assert "1006" in tokens
    assert "how" not in tokens  # stopword


def test_bm25_search_food_query(sample_retriever):
    results = sample_retriever.search("How do I open a restaurant food establishment?", top_k=5)
    assert len(results) > 0
    top_result = results[0]
    assert top_result.service_code == "1006"
    assert "Retail Food" in top_result.service_name
    assert top_result.score > 0.0
    assert top_result.source_url == "https://www.chicago.gov/RetailFood"


def test_bm25_search_exact_code(sample_retriever):
    results = sample_retriever.search("1781", top_k=3)
    assert len(results) > 0
    assert results[0].service_code == "1781"
    assert "Tobacco" in results[0].service_name


def test_bm25_search_empty_query(sample_retriever):
    assert sample_retriever.search("", top_k=5) == []
    assert sample_retriever.search("   ", top_k=5) == []


def test_bm25_top_k_limiting(sample_retriever):
    results = sample_retriever.search("license", top_k=2)
    assert len(results) <= 2
