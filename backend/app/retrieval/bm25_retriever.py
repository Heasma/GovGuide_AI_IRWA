"""
GovGuide AI — Okapi BM25 Lexical Retriever

Implements Okapi BM25 lexical ranking for ServiceChunk documents.

Parameters:
- k1 = 1.5 (term frequency saturation)
- b = 0.75 (document length penalization)

Features:
- Field-weighted token matching (service_name, service_code, category, section, body text)
- Exact license code boost (e.g., '1006', '1010')
- Returns structured results preserving complete source attribution
"""

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from app.retrieval.chunker import ServiceChunk

# Stopwords list for standard lexical normalization
DEFAULT_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}


def tokenize(text: str, remove_stopwords: bool = False) -> List[str]:
    """
    Tokenize text into lowercase alphanumeric tokens.
    Preserves numerical strings (such as license codes like '1006', '1010').
    """
    if not text:
        return []
    tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    if remove_stopwords:
        tokens = [t for t in tokens if t not in DEFAULT_STOPWORDS]
    return tokens


@dataclass
class BM25Result:
    """A scored result from BM25 retrieval."""
    chunk_id: str
    service_id: str
    service_code: str
    service_name: str
    category: str
    section: str
    text: str
    score: float
    source_id: str
    source_url: str
    source_title: str
    source_confidence: str
    matched_terms: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "service_id": self.service_id,
            "service_code": self.service_code,
            "service_name": self.service_name,
            "category": self.category,
            "section": self.section,
            "text": self.text,
            "score": self.score,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "source_confidence": self.source_confidence,
            "matched_terms": self.matched_terms,
        }


class BM25Retriever:
    """
    Okapi BM25 Index over ServiceChunk documents.
    """

    def __init__(
        self,
        chunks: Optional[List[ServiceChunk]] = None,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        self.k1 = k1
        self.b = b
        self.chunks: List[ServiceChunk] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_term_freqs: List[Counter] = []
        self.inverted_index: Dict[str, List[int]] = defaultdict(list)
        self.idf: Dict[str, float] = {}

        if chunks:
            self.index(chunks)

    def index(self, chunks: List[ServiceChunk]) -> None:
        """Build the BM25 inverted index over the provided chunks."""
        self.chunks = list(chunks)
        self.doc_lengths = []
        self.doc_term_freqs = []
        self.inverted_index = defaultdict(list)
        self.idf = {}

        total_len = 0
        n_docs = len(self.chunks)

        if n_docs == 0:
            self.avg_doc_len = 0.0
            return

        for doc_idx, chunk in enumerate(self.chunks):
            # Combine fields with weight repetition for critical fields
            # service_code and service_name get extra term density
            boosted_text = f"{chunk.service_code} {chunk.service_code} {chunk.service_name} {chunk.service_name} {chunk.category} {chunk.section} {chunk.text}"
            tokens = tokenize(boosted_text)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)

            for term in tf.keys():
                self.inverted_index[term].append(doc_idx)

        self.avg_doc_len = total_len / n_docs

        # Calculate IDF for all indexed terms
        for term, posting_list in self.inverted_index.items():
            df = len(posting_list)
            # Standard Lucene/Okapi smoothed IDF
            self.idf[term] = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 10) -> List[BM25Result]:
        """
        Execute a BM25 search for the given query.
        Returns top_k results sorted by score descending.
        """
        if not self.chunks or not query or not query.strip():
            return []

        query_tokens = tokenize(query, remove_stopwords=True)
        if not query_tokens:
            query_tokens = tokenize(query, remove_stopwords=False)
            return []

        scores: Dict[int, float] = defaultdict(float)
        matched_terms_per_doc: Dict[int, List[str]] = defaultdict(list)

        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            token_idf = self.idf[token]
            posting_list = self.inverted_index[token]

            for doc_idx in posting_list:
                tf = self.doc_term_freqs[doc_idx][token]
                doc_len = self.doc_lengths[doc_idx]

                # BM25 term score formula
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                term_score = token_idf * (numerator / denominator)

                scores[doc_idx] += term_score
                matched_terms_per_doc[doc_idx].append(token)

        # Sort candidate documents by BM25 score descending
        sorted_indices = sorted(scores.keys(), key=lambda idx: scores[idx], reverse=True)

        results: List[BM25Result] = []
        for idx in sorted_indices[:top_k]:
            chunk = self.chunks[idx]
            score = round(scores[idx], 4)
            if score <= 0:
                continue

            results.append(
                BM25Result(
                    chunk_id=chunk.chunk_id,
                    service_id=chunk.service_id,
                    service_code=chunk.service_code,
                    service_name=chunk.service_name,
                    category=chunk.category,
                    section=chunk.section,
                    text=chunk.text,
                    score=score,
                    source_id=chunk.source_id,
                    source_url=chunk.source_url,
                    source_title=chunk.source_title,
                    source_confidence=chunk.source_confidence,
                    matched_terms=matched_terms_per_doc[idx],
                )
            )

        return results
