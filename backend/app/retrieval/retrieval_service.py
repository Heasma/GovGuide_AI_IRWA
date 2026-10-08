"""
GovGuide AI — Retrieval Service

Coordinates the complete information retrieval pipeline:
1. Query preprocessing and normalization
2. BM25 lexical retrieval
3. Semantic vector retrieval
4. Hybrid Reciprocal Rank Fusion (RRF)
5. Source attribution validation
6. Structured EvidenceBundle assembly
"""

import re
from typing import Any, Dict, List, Optional
import structlog

from app.config import get_settings
from app.nlp.preprocessor import preprocess, normalize_for_retrieval, expand_query
from app.nlp.intent_classifier import classify_intent
from app.retrieval.chunker import ServiceChunk
from app.retrieval.chunk_generator import generate_chunks_from_db
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.semantic_retriever import SemanticRetriever, LocalDeterministicEmbeddingProvider
from app.retrieval.hybrid_retriever import HybridRetriever, HybridResult
from app.retrieval.source_attribution import filter_attributed_results
from app.orchestrator.message_schema import (
    EvidenceBundle,
    EvidenceResult,
    SourceReference,
)

logger = structlog.get_logger(__name__)


def extract_distinguishing_terms(query: str) -> List[str]:
    """
    Extracts informative, non-stopword tokens from the user query.
    Used to verify that retrieved evidence actually contains the subject requested.
    """
    generic_stops = {
        # English grammatical and functional stop words
        "what", "is", "the", "for", "how", "to", "apply", "get", "need", "obtain", "a", "an", "and", "or",
        "in", "of", "on", "at", "by", "with", "about", "from", "do", "does", "did", "i", "can", "could",
        "should", "would", "shall", "will", "may", "might", "must", "where", "when", "why", "who", "whom",
        "which", "whose", "are", "am", "be", "been", "being", "was", "were", "have", "has", "had", "having",
        "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not",
        "only", "own", "same", "so", "than", "too", "very", "just", "now", "into", "through", "during",
        "before", "after", "above", "below", "up", "down", "out", "off", "over", "under", "again", "further",
        "then", "once", "here", "there",
        # Common domain nouns, verbs, and inflections
        "business", "license", "licence", "licenses", "licences", "licensing", "licensed",
        "city", "chicago", "permit", "permits", "permitting", "permitted",
        "services", "service", "requirement", "requirements", "require", "requires", "required", "requiring",
        "information", "details", "official", "process", "processes", "processing", "processed",
        "application", "procedure", "procedures", "step", "steps", "fee", "fees", "cost", "pricing",
        "documents", "document", "documentation", "eligibility", "eligible", "renewal", "renew", "renewing",
        "office", "department", "bacp", "type", "types",
        "you", "your", "my", "me", "we", "us", "they", "them",
        "start", "starting", "starts", "started", "open", "opening", "opens", "opened",
        "want", "wants", "wanted", "wanting", "like", "likes", "liked",
        "tell", "telling", "tells", "told", "much", "many",
        "give", "giving", "gives", "gave", "please", "help", "helping", "helps", "helped",
        "new", "suitable", "perfect", "good", "best", "right",
        "apply", "applying", "applies", "applied", "applicant", "applicants",
        "obtain", "obtaining", "obtains", "obtained", "get", "getting", "gets", "got",
        "know", "knowing", "knows", "knew", "known", "guide", "guiding", "guides", "guidance",
        "take", "taking", "takes", "took", "taken",
        # Thanglish / Tamil / Sinhala functional particles
        "ennaku", "enakku", "naan", "unga", "ungalluku", "enga", "engae", "epdi", "edukka",
        "edukurathu", "edukanum", "vanganum", "enna", "ena", "venum", "theva", "thevai",
        "panna", "pannanum", "pannum", "poren", "podanum", "onnu", "ondu", "oru", "kudunga",
        "sollunga", "kidaikkala", "kidaikkum", "illai", "enda", "ennaen", "pathina", "pathi",
        "madhiri", "sambanthapata", "theriya", "solla", "vekkara", "irukkuma", "panradhu",
        "mona", "oyata", "karanna", "ona", "wage", "kiyanna", "wisthara", "ganna", "puluwan",
    }
    tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", query.lower())
    return [t for t in tokens if t not in generic_stops and len(t) > 2]


class RetrievalService:
    """
    Unified service for information retrieval across the government service corpus.
    """

    def __init__(
        self,
        chunks: Optional[List[ServiceChunk]] = None,
        rrf_k: Optional[int] = None,
        auto_load: bool = True,
    ):
        settings = get_settings()
        self.top_k = settings.RETRIEVAL_TOP_K
        self.rrf_k = rrf_k or settings.RRF_K
        self.confidence_threshold = settings.RETRIEVAL_CONFIDENCE_THRESHOLD

        self.bm25_retriever = BM25Retriever(k1=settings.BM25_K1, b=settings.BM25_B)
        self.semantic_retriever = SemanticRetriever(provider=LocalDeterministicEmbeddingProvider())
        self.hybrid_retriever = HybridRetriever(
            bm25_retriever=self.bm25_retriever,
            semantic_retriever=self.semantic_retriever,
            rrf_k=self.rrf_k,
        )

        self._chunks: List[ServiceChunk] = []
        self._indexed = False

        if chunks:
            self.index(chunks)
        elif auto_load:
            self._try_load_db()

    def _try_load_db(self) -> None:
        """Attempt to load and index chunks from PostgreSQL at startup."""
        try:
            chunks = generate_chunks_from_db()
            if chunks:
                self.index(chunks)
                logger.info(
                    "retrieval_service_db_loaded",
                    chunks_count=len(chunks),
                )
        except Exception as exc:
            logger.warning(
                "retrieval_service_db_load_deferred",
                reason=str(exc),
            )

    def index(self, chunks: List[ServiceChunk]) -> None:
        """Index a corpus of ServiceChunk items."""
        self._chunks = list(chunks)
        self.hybrid_retriever.index(self._chunks)
        self._indexed = True
        logger.info("retrieval_service_indexed", chunk_count=len(self._chunks))

    @property
    def is_indexed(self) -> bool:
        return self._indexed and len(self._chunks) > 0

    @property
    def total_chunks(self) -> int:
        return len(self._chunks)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        mode: Optional[str] = None,
        intent: Optional[Any] = None,
        target_service: Optional[str] = None,
    ) -> EvidenceBundle:
        """
        Execute full retrieval pipeline and return an EvidenceBundle.

        Args:
            query:  Raw user query.
            top_k:  Number of results to retrieve (default: settings.RETRIEVAL_TOP_K).
            mode:   Retrieval mode ("hybrid" | "bm25" | "semantic").
            intent: Detected intent enum or string for section boosting.
            target_service: Target service name or code for service boosting.

        Returns:
            EvidenceBundle with verified source attribution and confidence score.
        """
        k = top_k or self.top_k
        clean_query = preprocess(query)
        expanded = expand_query(clean_query)
        from app.nlp.intent_classifier import classify_intent, classify_intents
        classified_intents = classify_intents(clean_query)
        detected_intent = intent or classified_intents[0]
        intent_val = detected_intent.value if hasattr(detected_intent, "value") else str(detected_intent)
        intents_list = [i.value if hasattr(i, "value") else str(i) for i in classified_intents]

        if not self.is_indexed:
            self._try_load_db()

        if not clean_query or not self.is_indexed:
            return EvidenceBundle(
                query=query,
                intent=intent_val,
                intents=intents_list,
                total_retrieved=0,
                confidence=0.0,
                retrieval_method=mode or "hybrid",
                results=[],
                sources=[],
            )

        settings = get_settings()
        retrieval_mode = (mode or settings.RETRIEVAL_MODE).lower()

        # ── Canonical Service Identification & Service-Scoped Gating ──────────
        from app.nlp.service_resolver import get_service_resolver
        resolver = get_service_resolver()
        resolved_service_code = None
        resolved_service_name = None
        if target_service:
            resolved_service_code, resolved_service_name, _ = resolver.resolve(target_service)
        if not resolved_service_code:
            resolved_service_code, resolved_service_name, _ = resolver.resolve(clean_query)
        if not resolved_service_code:
            resolved_service_code, resolved_service_name, _ = resolver.resolve(query)

        is_catalog_query = (
            intent_val == "license_catalog"
            or (hasattr(detected_intent, "value") and detected_intent.value == "license_catalog")
            or "license_catalog" in intents_list
        )

        if resolved_service_code and not is_catalog_query:
            # Service identity strictly prioritizes over generic BM25/semantic score
            # Restrict candidates ONLY to chunks belonging to the identified service_code
            service_chunks = [
                c for c in self._chunks
                if str(getattr(c, "service_code", "")).strip().lower() == resolved_service_code.strip().lower()
            ]

            # Order chunks: put the requested intent section first, followed by others
            intent_section_priority = {
                "fees": ["fees", "overview"],
                "required_documents": ["required_documents", "overview"],
                "eligibility": ["eligibility", "overview"],
                "application_procedure": ["application_procedure", "overview"],
                "procedure": ["application_procedure", "overview"],
                "renewal": ["renewal", "overview"],
                "office_information": ["contact_information", "responsible_office"],
                "service_lookup": ["overview", "eligibility"],
                "service_information": ["overview", "eligibility"],
            }
            pref_sections = intent_section_priority.get(intent_val, ["overview"])

            def _service_chunk_sort_key(c) -> int:
                sec = (getattr(c, "section", "") or "").lower()
                if sec in pref_sections:
                    return pref_sections.index(sec)
                return 99

            service_chunks.sort(key=_service_chunk_sort_key)
            attributed_candidates = service_chunks
            retrieval_mode = "service_scoped"

        elif is_catalog_query:
            # Retrieve verified canonical service overview chunks across distinct services in the KB
            overview_chunks = [
                c for c in self._chunks
                if getattr(c, "section", "") == "overview" and getattr(c, "service_code", "") not in ("NOT_AVAILABLE", "")
            ]
            if not overview_chunks:
                seen_codes = set()
                for c in self._chunks:
                    sc = getattr(c, "service_code", "")
                    if sc and sc not in seen_codes:
                        seen_codes.add(sc)
                        overview_chunks.append(c)

            # Sort deterministically: prioritized core Chicago business licenses, followed by others in numeric code order
            core_priority = {
                "1010": 1, "1006": 2, "4405": 3, "1470": 4, "1781": 5,
                "1023": 6, "4404": 7, "1050": 8, "1007": 9, "1032": 10,
                "1275": 11, "1003": 12, "4406": 13, "1683": 14,
            }
            overview_chunks.sort(key=lambda c: (core_priority.get(getattr(c, "service_code", ""), 99), getattr(c, "service_code", "")))
            attributed_candidates = overview_chunks

        else:
            # Execute search based on mode
            raw_candidates = []
            if retrieval_mode == "bm25":
                norm_query = normalize_for_retrieval(expanded)
                bm25_res = self.bm25_retriever.search(norm_query, top_k=k)
                for r in bm25_res:
                    raw_candidates.append(r)
            elif retrieval_mode == "semantic":
                sem_res = self.semantic_retriever.search(expanded, top_k=k)
                for r in sem_res:
                    raw_candidates.append(r)
            else:  # hybrid (default)
                retrieval_mode = "hybrid"
                hybrid_res = self.hybrid_retriever.search(
                    expanded,
                    top_k=k,
                    intent=detected_intent,
                    target_service=target_service,
                )
                for r in hybrid_res:
                    raw_candidates.append(r)

            # ── Source Attribution Validation ─────────────────────────────────
            attributed_candidates = filter_attributed_results(raw_candidates)

            # 1. Reject everything if query contains an unrecognized token
            from app.nlp.activity_extractor import extract_business_activity, BusinessActivityType
            activity = extract_business_activity(clean_query)
            if activity.activity_type == BusinessActivityType.UNRECOGNIZED_TOKEN:
                logger.info("retrieval_service_unrecognized_token_rejected", token=activity.extracted_text)
                attributed_candidates = []

            # 2. Activity domain compatibility filtering
            if attributed_candidates:
                # If the user query is explicitly non-food (tailoring, clothing, electronics, generic retail),
                # reject Retail Food Establishment (1006) and other food licenses.
                if not activity.is_food_related and activity.activity_type not in (BusinessActivityType.NONE, BusinessActivityType.GENERIC_BUSINESS):
                    compatible_candidates = []
                    for c in attributed_candidates:
                        srv_name = (getattr(c, "service_name", "") or "").lower()
                        srv_code = (getattr(c, "service_code", "") or "").lower()
                        if srv_code in ("1006", "4405", "1005") or "retail food" in srv_name or "mobile food" in srv_name:
                            continue  # Incompatible food license for non-food activity
                        compatible_candidates.append(c)
                    attributed_candidates = compatible_candidates

            # 3. Check distinguishing terms
            expanded_q = expand_query(clean_query)
            distinguishing_terms = extract_distinguishing_terms(f"{clean_query} {expanded_q}")
            if target_service and target_service.lower() not in ("business license", "license", "city license"):
                for t in re.findall(r"\b[a-zA-Z0-9_-]+\b", target_service.lower()):
                    if t not in distinguishing_terms and len(t) > 2 and t not in (
                        "business", "license", "city", "chicago", "service", "apply", "for"
                    ):
                        distinguishing_terms.append(t)

            if distinguishing_terms and attributed_candidates:
                matched_candidates = []
                suggested_svc = (activity.suggested_candidate_service or "").lower()
                for c in attributed_candidates:
                    chunk_text = (getattr(c, "text", "") or "").lower()
                    srv_name = (getattr(c, "service_name", "") or "").lower()
                    srv_cat = (getattr(c, "category", "") or "").lower()
                    srv_code = (getattr(c, "service_code", "") or "").lower()
                    full_chunk_str = f"{chunk_text} {srv_name} {srv_cat} {srv_code}"

                    term_match = any(dt in full_chunk_str for dt in distinguishing_terms)
                    suggested_match = False
                    if suggested_svc:
                        suggested_match = (
                            suggested_svc in srv_name
                            or suggested_svc in srv_code
                            or (suggested_svc in ("limited business license", "1010") and ("retail" in srv_cat or "1010" in srv_code or "limited business" in srv_name))
                        )

                    if term_match or suggested_match:
                        matched_candidates.append(c)

                if not matched_candidates:
                    # Distinguishing entity is completely absent from knowledge base
                    logger.info(
                        "retrieval_service_distinguishing_entity_unmatched",
                        terms=distinguishing_terms,
                        rejected_count=len(attributed_candidates),
                    )
                    attributed_candidates = []
                else:
                    attributed_candidates = matched_candidates

        # ── Assemble EvidenceResult items and SourceReferences ───────────────
        evidence_results: List[EvidenceResult] = []
        seen_source_ids = set()
        source_references: List[SourceReference] = []

        for i, item in enumerate(attributed_candidates):
            # Determine score and retrieval method
            if is_catalog_query:
                score = round(max(0.50, 0.95 - (i * 0.02)), 2)
                method = "catalog"
            elif isinstance(item, HybridResult):
                score = item.rrf_score
                method = "hybrid"
            elif hasattr(item, "score"):
                score = item.score
                method = retrieval_mode
            else:
                score = 0.0
                method = retrieval_mode

            result = EvidenceResult(
                chunk_id=item.chunk_id,
                service_id=item.service_id,
                service_code=item.service_code,
                service_name=item.service_name,
                section=item.section,
                content=item.text,
                text=item.text,
                relevance_score=score,
                score=score,
                source_id=item.source_id,
                source_url=item.source_url,
                source_title=item.source_title,
                source_confidence=item.source_confidence,
                retrieval_method=method,
            )
            evidence_results.append(result)

            if item.source_id not in seen_source_ids:
                seen_source_ids.add(item.source_id)
                source_references.append(
                    SourceReference(
                        source_id=item.source_id,
                        title=item.source_title,
                        url=item.source_url,
                        excerpt=item.text[:200] + "..." if len(item.text) > 200 else item.text,
                    )
                )

        # ── Calculate Confidence ──────────────────────────────────────────────
        confidence = 0.0
        if is_catalog_query:
            confidence = 0.90 if evidence_results else 0.0
        elif retrieval_mode == "service_scoped":
            confidence = 0.95 if evidence_results else 0.0
        elif evidence_results:
            top_res = attributed_candidates[0] if attributed_candidates else None
            top_score = evidence_results[0].score or evidence_results[0].relevance_score

            if retrieval_mode == "hybrid" and isinstance(top_res, HybridResult):
                bm25_s = top_res.bm25_score
                sem_s = top_res.semantic_score
                if sem_s < 0.15 or bm25_s < 1.5:
                    # Insufficient semantic agreement or lexical overlap -> Out-of-domain / irrelevant match
                    confidence = round(min(0.12, max(0.02, sem_s * 0.2)), 2)
                elif bm25_s >= 3.0 and sem_s >= 0.20:
                    # Multi-modal agreement: calibrate based on direct entity vs inferred broad category
                    is_inferred = getattr(activity, "is_generic_or_ambiguous", False) or activity.activity_type in (
                        BusinessActivityType.RETAIL_CLOTHING,
                        BusinessActivityType.RETAIL_ELECTRONICS_MOBILE,
                        BusinessActivityType.GENERIC_RETAIL,
                    )
                    base_conf = 0.78 if is_inferred else 0.88
                    confidence = round(min(0.92, base_conf + (min(bm25_s, 8.0) / 40.0) * 0.08), 2)
                elif bm25_s >= 1.5 and sem_s >= 0.15:
                    # Moderate lexical and semantic match
                    confidence = round(min(0.75, 0.45 + (bm25_s / 10.0) * 0.25), 2)
                else:
                    confidence = round(min(0.14, max(0.05, sem_s * 0.1)), 2)
            elif retrieval_mode == "semantic":
                confidence = round(min(0.90, top_score) if top_score >= 0.40 else top_score * 0.15, 2)
            else:
                confidence = round(min(0.90, top_score / 10.0) if top_score >= 2.0 else 0.05, 2)

        return EvidenceBundle(
            query=query,
            intent=intent_val,
            intents=intents_list,
            total_retrieved=len(evidence_results),
            confidence=confidence,
            retrieval_method=retrieval_mode,
            results=evidence_results,
            sources=source_references,
        )


_global_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    """Returns the singleton RetrievalService instance."""
    global _global_retrieval_service
    if _global_retrieval_service is None:
        _global_retrieval_service = RetrievalService(auto_load=True)
    return _global_retrieval_service

