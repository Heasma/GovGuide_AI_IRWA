"""
GovGuide AI — Universal Canonical Service Resolver

Dynamically resolves any user query reference to the canonical GovernmentService
service_code across ALL 56 canonical records stored in the knowledge base / database.

Features:
- Auto-initializes from canonical database records (zero hardcoded code->service mappings).
- Multi-stage deterministic & fuzzy matching (code, full name, clean name, token overlap, edit distance).
- Supports typos (e.g., 'secondery sports', 'tavrn', 'restarant', 'mobil food', 'tobaco').
- Supports multilingual / Thanglish queries ('secondary sports pathi sollunga', 'secondary sports service details venum').
- Detects unknown / non-existent services ('tell me about ABCXYZ service').
- Detects generic service queries ('I need to know about service', 'service details venum').
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

import structlog

logger = structlog.get_logger(__name__)

# Minimum confidence thresholds
_EXACT_CODE_SCORE = 1.00
_FULL_NAME_SCORE = 0.98
_PARTIAL_OVERLAP_MIN = 0.60
_FUZZY_MIN_RATIO = 0.75
_MIN_RESOLUTION_SCORE = 0.60

_GENERIC_TOKENS = {
    "a", "an", "the", "for", "of", "in", "and", "or", "to", "by", "on", "at", "with",
    "business", "license", "licence", "licenses", "licences", "licensing",
    "service", "services", "city", "chicago", "municipal", "government",
    "what", "how", "is", "are", "do", "does", "get", "apply", "applying", "obtain",
    "i", "me", "my", "we", "our", "you", "your", "need", "want", "can", "could",
    "fees", "fee", "cost", "price", "pricing",
    "documents", "document", "paperwork", "form", "forms",
    "eligibility", "eligible", "qualify", "requirements", "criteria",
    "renewal", "renew", "validity", "expire", "expiration",
    "procedure", "procedures", "steps", "process",
    "office", "location", "address", "contact", "phone", "hours",
    "info", "information", "details", "about", "tell", "give", "show", "help",
    "please", "know", "which", "where", "when", "why", "who",
    # Thanglish particles
    "pathi", "pathina", "sollunga", "venum", "vendum", "kudunga", "theva", "thevai",
    "irukku", "inga", "edukka", "edukanum", "edukkanum", "vanganum", "panren", "panna",
    "enna", "mona", "oyata", "karanna", "ona", "wage", "kiyanna", "ganna", "puluwan",
}


def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation/accents, collapse whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def clean_service_display_name(name: str) -> str:
    """Strips operational prefixes like 'Apply for a ' or parenthetical acronyms for clean matching."""
    if not name:
        return ""
    c = re.sub(r"^Apply for (?:an? )?", "", name, flags=re.IGNORECASE).strip()
    return c


def levenshtein_ratio(a: str, b: str) -> float:
    """Returns edit-similarity ratio in [0, 1]."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if abs(la - lb) > max(la, lb) * 0.5:
        return 0.0
    prev = list(range(lb + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(
                curr[j] + 1,
                prev[j + 1] + 1,
                prev[j] + (0 if ca == cb else 1),
            ))
        prev = curr
    distance = prev[lb]
    return 1.0 - distance / max(la, lb)


@dataclass
class CanonicalServiceEntry:
    service_code: str
    raw_name: str
    clean_name: str
    normalized_name: str
    normalized_clean_name: str
    category: str
    name_tokens: List[str] = field(default_factory=list)
    meaningful_tokens: List[str] = field(default_factory=list)
    aliases: Set[str] = field(default_factory=set)

    def __post_init__(self):
        self.name_tokens = self.normalized_name.split()
        clean_tokens = self.normalized_clean_name.split()
        self.meaningful_tokens = [
            t for t in clean_tokens
            if t not in _GENERIC_TOKENS and len(t) > 2
        ]
        if not self.meaningful_tokens:
            self.meaningful_tokens = [t for t in clean_tokens if len(t) > 2]

        # Populate aliases
        self.aliases.add(self.normalized_name)
        self.aliases.add(self.normalized_clean_name)
        self.aliases.add(self.service_code.lower())

        # Strip "license" or "registration" or category markers for shorthand matching
        shorter = re.sub(r"\b(licenses?|licences?|registration|permit|operator|establishment|facility|services?)\b", "", self.normalized_clean_name).strip()
        shorter = re.sub(r"\s+", " ", shorter)
        if shorter and len(shorter) > 2:
            self.aliases.add(shorter)

        # Singular/plural variants
        if "sports" in self.normalized_clean_name:
            self.aliases.add(self.normalized_clean_name.replace("sports", "sport"))
            if shorter:
                self.aliases.add(shorter.replace("sports", "sport"))


class ServiceResolver:
    """
    Universal Canonical Service Resolver operating dynamically across all 56 GovernmentService records.
    """

    def __init__(self):
        self._entries: List[CanonicalServiceEntry] = []
        self._code_index: Dict[str, CanonicalServiceEntry] = {}
        self._alias_index: Dict[str, CanonicalServiceEntry] = {}
        self._ready: bool = False

    def build_index_from_services(self, services: List[Dict[str, Any]]) -> None:
        """Builds resolution index from raw database service records or dicts."""
        seen = set()
        entries: List[CanonicalServiceEntry] = []
        self._code_index.clear()
        self._alias_index.clear()

        for s in services:
            code = str(s.get("service_code") or "").strip()
            if not code or code in seen or code == "NOT_AVAILABLE":
                continue
            seen.add(code)

            raw_name = str(s.get("name") or f"Service {code}").strip()
            clean_name = clean_service_display_name(raw_name)
            norm_raw = normalize_text(raw_name)
            norm_clean = normalize_text(clean_name)
            cat = str(s.get("category") or "Business Licensing").strip()

            entry = CanonicalServiceEntry(
                service_code=code,
                raw_name=raw_name,
                clean_name=clean_name,
                normalized_name=norm_raw,
                normalized_clean_name=norm_clean,
                category=cat,
            )
            entries.append(entry)
            self._code_index[code.lower()] = entry
            for alias in entry.aliases:
                if alias and alias not in self._alias_index:
                    self._alias_index[alias] = entry

        self._entries = entries
        self._ready = len(entries) > 0
        logger.info("universal_service_resolver_indexed", service_count=len(self._entries))

    def build_index(self, chunks) -> None:
        """Builds resolution index from ServiceChunk objects."""
        services_dict = {}
        for c in chunks:
            code = getattr(c, "service_code", None)
            if code and code not in services_dict:
                services_dict[code] = {
                    "service_code": code,
                    "name": getattr(c, "service_name", None) or f"Service {code}",
                    "category": getattr(c, "category", None) or "Business Licensing",
                }
        self.build_index_from_services(list(services_dict.values()))

    def _ensure_initialized(self) -> None:
        """Auto-loads canonical records from database if not already initialized."""
        if not self._ready:
            try:
                from app.retrieval.chunk_generator import fetch_services_from_db
                db_services = fetch_services_from_db()
                if db_services:
                    self.build_index_from_services(db_services)
            except Exception as exc:
                logger.warning("service_resolver_db_autoload_failed", error=str(exc))

    @property
    def is_ready(self) -> bool:
        self._ensure_initialized()
        return self._ready and len(self._entries) > 0

    def resolve(self, query: str) -> Tuple[Optional[str], Optional[str], float]:
        """
        Dynamically resolves user query to (service_code, service_display_name, confidence).
        Returns: (service_code, service_name, score) or (None, None, 0.0)
        """
        if not query or not query.strip():
            return None, None, 0.0

        self._ensure_initialized()
        if not self._ready:
            return None, None, 0.0

        norm_query = normalize_text(query)
        query_words = norm_query.split()
        query_tokens = set(query_words)

        # ── Stage 1: Exact Service Code Matching ──────────────────────────────
        # Look for explicit code tokens like '7035', '1006', 'code 7035', 'license 7035'
        for token in query_tokens:
            if token in self._code_index:
                entry = self._code_index[token]
                return entry.service_code, entry.clean_name, _EXACT_CODE_SCORE

        code_match = re.search(r"\b(?:code|license|service|number|#)?\s*([0-9]{4})\b", norm_query)
        if code_match:
            candidate_code = code_match.group(1)
            if candidate_code in self._code_index:
                entry = self._code_index[candidate_code]
                return entry.service_code, entry.clean_name, _EXACT_CODE_SCORE

        # ── Stage 2: Exact Phrase / Alias Substring Matching ──────────────────
        # Check longest aliases first for maximum specificity (e.g. 'Secondary Sports License' before 'Sports')
        sorted_aliases = sorted(self._alias_index.items(), key=lambda x: len(x[0]), reverse=True)
        for alias, entry in sorted_aliases:
            if alias and len(alias) > 3:
                # Use word-boundary match for alias
                pattern = r"\b" + re.escape(alias) + r"\b"
                if re.search(pattern, norm_query):
                    return entry.service_code, entry.clean_name, _FULL_NAME_SCORE

        # ── Stage 3: Business Activity Compatibility Integration ──────────────
        try:
            from app.nlp.activity_extractor import extract_business_activity, BusinessActivityType
            act = extract_business_activity(norm_query)
            if act and act.suggested_candidate_service and not act.is_generic_or_ambiguous:
                # Match suggested service name against canonical entries
                target_norm = normalize_text(clean_service_display_name(act.suggested_candidate_service))
                for entry in self._entries:
                    if entry.normalized_clean_name == target_norm or target_norm in entry.normalized_clean_name:
                        return entry.service_code, entry.clean_name, 0.95
        except Exception:
            pass

        # ── Stage 4: Meaningful Token Overlap (Greedy / Specificity Weighted) ──
        best_code: Optional[str] = None
        best_name: Optional[str] = None
        best_score: float = 0.0
        best_matched_count: int = 0

        for entry in self._entries:
            meaningful = entry.meaningful_tokens
            if not meaningful:
                continue

            matched = [t for t in meaningful if t in query_tokens]
            matched_count = len(matched)
            if matched_count == 0:
                continue

            overlap = matched_count / len(meaningful)
            if overlap >= _PARTIAL_OVERLAP_MIN:
                # Prioritize entries where MORE distinct meaningful tokens matched
                score = 0.80 + (overlap * 0.15) + (min(3, matched_count) * 0.01)
                if score > best_score or (score == best_score and matched_count > best_matched_count):
                    best_score = score
                    best_code = entry.service_code
                    best_name = entry.clean_name
                    best_matched_count = matched_count

        if best_score >= _MIN_RESOLUTION_SCORE:
            return best_code, best_name, best_score

        # ── Stage 5: Token-Level Fuzzy Typo Matching ──────────────────────────
        # Check if individual query tokens match entry meaningful tokens with typo tolerance
        for entry in self._entries:
            meaningful = entry.meaningful_tokens
            if not meaningful:
                continue
            fuzzy_matched_count = 0
            for mt in meaningful:
                for qt in query_tokens:
                    if qt in _GENERIC_TOKENS or len(qt) <= 2:
                        continue
                    if abs(len(qt) - len(mt)) <= 2 and mt[0] == qt[0]:
                        ratio = levenshtein_ratio(qt, mt)
                        if ratio >= 0.80:
                            fuzzy_matched_count += 1
                            break
            if fuzzy_matched_count > 0:
                overlap = fuzzy_matched_count / len(meaningful)
                if overlap >= _PARTIAL_OVERLAP_MIN:
                    score = 0.75 + (overlap * 0.15)
                    if score > best_score:
                        best_score = score
                        best_code = entry.service_code
                        best_name = entry.clean_name

        if best_score >= _MIN_RESOLUTION_SCORE:
            return best_code, best_name, best_score

        # ── Stage 6: Sliding-Window Levenshtein Matching ───────────────────────
        for entry in self._entries:
            for alias in (entry.normalized_clean_name, entry.normalized_name):
                alias_words = alias.split()
                alias_len = len(alias_words)
                if alias_len == 0 or len(alias) <= 3:
                    continue

                for start in range(len(query_words)):
                    window_end = min(start + alias_len + 1, len(query_words))
                    for end in range(start + max(1, alias_len - 1), window_end + 1):
                        window = " ".join(query_words[start:end])
                        ratio = levenshtein_ratio(window, alias)
                        if ratio >= _FUZZY_MIN_RATIO and ratio > best_score:
                            best_score = ratio
                            best_code = entry.service_code
                            best_name = entry.clean_name

        if best_score >= _MIN_RESOLUTION_SCORE:
            return best_code, best_name, best_score

        return None, None, 0.0

    def detect_unknown_service(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Detects if the query asks about a specific named service that is NOT in the 56 canonical records.
        Example: 'tell me about ABCXYZ service' -> (True, 'ABCXYZ')
        """
        if not query:
            return False, None

        self._ensure_initialized()
        norm_q = normalize_text(query)

        # First check if query resolved to a known service
        resolved_code, _, _ = self.resolve(query)
        if resolved_code:
            return False, None

        # Ensure query is in-domain before classifying as unknown government service
        from app.nlp.domain_detector import classify_domain, is_domain_supported
        domain = classify_domain(query)
        if not is_domain_supported(domain):
            return False, None

        # Check for inquiry about a named entity: "tell me about <entity> (service|license)"
        patterns = [
            r"(?:tell\s+me\s+about|information\s+about|details\s+for|what\s+is|what\s+about|how\s+about)\s+(?:the\s+)?([a-z0-9_\-\s]{2,30}?)(?:\s+services|\s+service|\s+licenses|\s+license|\s+licence|\s+permit|\s+department)?$",
            r"(?:tell\s+me\s+about|information\s+about|details\s+for|what\s+is|what\s+about)\s+(?:the\s+)?([a-z0-9_\-\s]{2,30})",
        ]

        for p in patterns:
            m = re.search(p, norm_q)
            if m:
                extracted = m.group(1).strip()
                # Clean any trailing service/license keywords
                extracted = re.sub(r"\b(services|service|licenses|license|licence|permit|department)\b", "", extracted, flags=re.IGNORECASE).strip()
                # Check if extracted is a generic word or stopword
                if extracted and extracted not in _GENERIC_TOKENS and len(extracted) >= 3:
                    # Verify it's not a generic query
                    if not self.is_generic_service_query(query):
                        return True, extracted.title()

        return False, None

    def is_generic_service_query(self, query: str) -> bool:
        """
        Detects if query is a generic request for service information without specifying a service.
        Example: 'I need to know about service', 'service details venum', 'I need service information'
        """
        if not query:
            return False

        norm_q = normalize_text(query)
        
        # Check if already resolves to a specific service
        code, _, _ = self.resolve(query)
        if code:
            return False

        generic_patterns = [
            r"^(?:i\s+need\s+to\s+know\s+about\s+(?:a\s+)?service|i\s+need\s+service\s+information|service\s+details\s+(?:venum|vendum|theva|thevai|kudunga)|i\s+need\s+information\s+about\s+(?:a\s+)?service|tell\s+me\s+about\s+(?:the\s+)?service|service\s+details|government\s+service\s+details)$",
            r"^(?:service|government\s+service)\s+(?:details|information|info|summary)\s*(?:venum|vendum|theva|thevai|kudunga)?\??$",
            r"^i\s+(?:need|want)\s+(?:to\s+know\s+about\s+)?(?:a\s+)?(?:government\s+)?service\??$",
        ]

        for p in generic_patterns:
            if re.search(p, norm_q):
                return True

        return False

    def get_all_entries(self) -> List[CanonicalServiceEntry]:
        self._ensure_initialized()
        return list(self._entries)

    def get_by_code(self, code: str) -> Optional[CanonicalServiceEntry]:
        self._ensure_initialized()
        return self._code_index.get((code or "").lower())


# Global singleton instance
_global_resolver = ServiceResolver()


def get_service_resolver() -> ServiceResolver:
    """Returns the application-global ServiceResolver instance."""
    return _global_resolver
