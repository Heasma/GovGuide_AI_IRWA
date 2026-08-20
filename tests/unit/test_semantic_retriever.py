"""
GovGuide AI — Unit Tests: Semantic Vector Retriever

Tests:
- Pluggable EmbeddingProvider abstract interface
- LocalDeterministicEmbeddingProvider reproducibility & dimension
- Cosine similarity computation
- Semantic retrieval ranking
- Empty query handling
"""

import uuid
import pytest
from app.retrieval.document_builder import build_service_document
from app.retrieval.chunker import chunk_document
from app.retrieval.semantic_retriever import (
    EmbeddingProvider,
    LocalDeterministicEmbeddingProvider,
    SemanticRetriever,
    cosine_similarity,
)


def test_embedding_provider_deterministic():
    provider = LocalDeterministicEmbeddingProvider(dimension=128)
    assert provider.dimension == 128

    vec1 = provider.embed_text("Retail Food Establishment License")
    vec2 = provider.embed_text("Retail Food Establishment License")

    assert len(vec1) == 128
    assert vec1 == vec2  # 100% deterministic

    # Related texts should have positive similarity
    vec_related = provider.embed_text("Restaurant and cafe food licensing")
    sim = cosine_similarity(vec1, vec_related)
    assert sim > 0.1


def test_semantic_retriever_search():
    services = [
        {
            "id": str(uuid.uuid4()),
            "service_code": "1006",
            "name": "Apply for a Retail Food Establishment License",
            "category": "Food & Beverage",
            "description": "Required for restaurants, bakeries, cafes, and food vendors in Chicago.",
            "source_url": "https://www.chicago.gov/RetailFood",
        },
        {
            "id": str(uuid.uuid4()),
            "service_code": "1781",
            "name": "Apply for a Tobacco License",
            "category": "Tobacco",
            "description": "Retail sale of cigarettes, cigars, electronic cigarettes, and tobacco products.",
            "source_url": "https://www.chicago.gov/Tobacco",
        },
    ]

    chunks = []
    for s in services:
        doc = build_service_document(s)
        chunks.extend(chunk_document(doc))

    retriever = SemanticRetriever(chunks=chunks)
    results = retriever.search("I want to sell cigars and cigarettes", top_k=3)

    assert len(results) > 0
    top = results[0]
    assert top.service_code == "1781"
    assert top.score > 0.0
    assert top.source_url == "https://www.chicago.gov/Tobacco"


def test_semantic_empty_query():
    retriever = SemanticRetriever(chunks=[])
    assert retriever.search("") == []
    assert retriever.search("test") == []
