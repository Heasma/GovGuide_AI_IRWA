"""
GovGuide AI — Information Retrieval & RAG Preparation Module
"""

from app.retrieval.document_builder import (
    CanonicalDocument,
    build_service_document,
    build_documents_from_services,
    NOT_AVAILABLE,
)
from app.retrieval.chunker import (
    ServiceChunk,
    chunk_document,
    chunk_documents,
)
from app.retrieval.chunk_generator import (
    generate_chunks_from_db,
    generate_chunks_from_services,
)
from app.retrieval.bm25_retriever import (
    BM25Retriever,
    BM25Result,
)
from app.retrieval.semantic_retriever import (
    EmbeddingProvider,
    LocalDeterministicEmbeddingProvider,
    SemanticRetriever,
    SemanticResult,
)
from app.retrieval.hybrid_retriever import (
    HybridRetriever,
    HybridResult,
)
from app.retrieval.source_attribution import (
    validate_source_attribution,
    filter_attributed_results,
)
from app.retrieval.retrieval_service import (
    RetrievalService,
)
from app.retrieval.retrieval_engine import (
    RetrievalEngine,
)

__all__ = [
    "CanonicalDocument",
    "build_service_document",
    "build_documents_from_services",
    "NOT_AVAILABLE",
    "ServiceChunk",
    "chunk_document",
    "chunk_documents",
    "generate_chunks_from_db",
    "generate_chunks_from_services",
    "BM25Retriever",
    "BM25Result",
    "EmbeddingProvider",
    "LocalDeterministicEmbeddingProvider",
    "SemanticRetriever",
    "SemanticResult",
    "HybridRetriever",
    "HybridResult",
    "validate_source_attribution",
    "filter_attributed_results",
    "RetrievalService",
    "RetrievalEngine",
]
