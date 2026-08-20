"""
GovGuide AI — Semantic Section Chunker

Transforms CanonicalDocument representations into structured, semantic section-based chunks.

Rules:
- Semantic section-based chunking matching government service inquiry types.
- Every chunk strictly retains chunk_id, service_id, service_code, section, text, source_id, source_url, source_title.
- Avoids arbitrary fixed-length truncation of coherent sections.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from app.retrieval.document_builder import CanonicalDocument, NOT_AVAILABLE


@dataclass
class ServiceChunk:
    """
    A single searchable text chunk derived from a GovernmentService section.
    """
    chunk_id: str
    service_id: str
    service_code: str
    service_name: str
    category: str
    section: str
    text: str
    source_id: str
    source_url: str
    source_title: str
    source_confidence: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "service_id": self.service_id,
            "service_code": self.service_code,
            "service_name": self.service_name,
            "category": self.category,
            "section": self.section,
            "text": self.text,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "source_confidence": self.source_confidence,
            "metadata": self.metadata,
        }


def chunk_document(doc: CanonicalDocument) -> List[ServiceChunk]:
    """
    Splits a CanonicalDocument into semantic section chunks.
    Each section with meaningful content becomes a ServiceChunk.
    """
    chunks: List[ServiceChunk] = []

    for section_name, section_text in doc.sections.items():
        if not section_text or section_text.strip() == NOT_AVAILABLE:
            continue

        chunk_id = f"chk-{doc.service_code}-{section_name}"
        chunk = ServiceChunk(
            chunk_id=chunk_id,
            service_id=doc.service_id,
            service_code=doc.service_code,
            service_name=doc.service_name,
            category=doc.category,
            section=section_name,
            text=section_text,
            source_id=doc.source_id,
            source_url=doc.source_url,
            source_title=doc.source_title,
            source_confidence=doc.source_confidence,
            metadata={
                "service_code": doc.service_code,
                "service_name": doc.service_name,
                "category": doc.category,
                "section": section_name,
                "source_url": doc.source_url,
                "source_title": doc.source_title,
                "source_confidence": doc.source_confidence,
            },
        )
        chunks.append(chunk)

    return chunks


def chunk_documents(docs: List[CanonicalDocument]) -> List[ServiceChunk]:
    """Split a list of CanonicalDocument objects into ServiceChunk items."""
    all_chunks: List[ServiceChunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    return all_chunks
