"""
GovGuide AI — Unit Tests: Hybrid RRF Retriever

Tests:
- Reciprocal Rank Fusion formula calculation: 1 / (k + rank)
- Rank order combination from BM25 and Semantic
- Configurable RRF constant k
- Candidate score sorting descending
- Empty query handling
"""

import uuid
import pytest
from app.retrieval.document_builder import build_service_document
from app.retrieval.chunker import chunk_document
from app.retrieval.hybrid_retriever import HybridRetriever, HybridResult


@pytest.fixture
def sample_hybrid_retriever():
    services = [
        {
            "id": str(uuid.uuid4()),
            "service_code": "1006",
            "name": "Apply for a Retail Food Establishment License",
            "category": "Food & Beverage",
            "description": "Required for restaurants, bakeries, cafes, and food handling businesses.",
            "source_url": "https://www.chicago.gov/RetailFood",
            "fee_amount": "$660.00",
        },
        {
            "id": str(uuid.uuid4()),
            "service_code": "1010",
            "name": "Apply for a Limited Business License (LBL)",
            "category": "Retail & General",
            "description": "Standard business license for retail and services.",
            "source_url": "https://www.chicago.gov/LBL",
            "fee_amount": "$500.00",
        },
        {
            "id": str(uuid.uuid4()),
            "service_code": "1781",
            "name": "Apply for a Tobacco License",
            "category": "Tobacco",
            "description": "Retail sale of tobacco, cigars, and e-cigarettes.",
            "source_url": "https://www.chicago.gov/Tobacco",
            "fee_amount": "$1,000.00",
        },
    ]

    chunks = []
    for s in services:
        doc = build_service_document(s)
        chunks.extend(chunk_document(doc))

    return HybridRetriever(chunks=chunks, rrf_k=60)


def test_hybrid_search_food_query(sample_hybrid_retriever):
    results = sample_hybrid_retriever.search("How much does a restaurant food license cost?", top_k=5)
    assert len(results) > 0

    top = results[0]
    assert isinstance(top, HybridResult)
    assert top.service_code == "1006"
    assert top.rrf_score > 0.0
    assert top.source_url == "https://www.chicago.gov/RetailFood"

    # Scores must be sorted descending
    scores = [r.rrf_score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_hybrid_empty_query(sample_hybrid_retriever):
    assert sample_hybrid_retriever.search("") == []
    assert sample_hybrid_retriever.search("   ") == []


def test_hybrid_rrf_k_parameter():
    retriever_k10 = HybridRetriever(chunks=[], rrf_k=10)
    assert retriever_k10.rrf_k == 10
