"""
GovGuide AI — Language Detector & Multilingual Classifier

Detects natural language, script, and code-mixed patterns:
- English (en)
- Tamil (ta) [Unicode script: \u0B80-\u0BFF]
- Sinhala (si) [Unicode script: \u0D80-\u0DFF]
- Thanglish (ta-Latn / Thanglish) [Tamil transcribed in Latin script]
- Singlish (si-Latn / Singlish) [Sinhala transcribed in Latin script]
- Mixed / Code-Switched (e.g. Tamil-English, Sinhala-English)
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class LanguageCode(str, Enum):
    ENGLISH = "en"
    TAMIL = "ta"
    SINHALA = "si"
    THANGLISH = "thanglish"
    SINGLISH = "singlish"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class LanguageInfo(BaseModel):
    """Detailed metadata for detected language, script, and code-mixing."""
    language: LanguageCode = LanguageCode.ENGLISH
    script: str = "latin"  # latin | tamil | sinhala | mixed
    confidence: float = 1.0
    is_multilingual: bool = False
    detected_markers: List[str] = Field(default_factory=list)
    details: Dict[str, str] = Field(default_factory=dict)


# Unicode Script Range Matchers
_TAMIL_SCRIPT_REGEX = re.compile(r"[\u0B80-\u0BFF]")
_SINHALA_SCRIPT_REGEX = re.compile(r"[\u0D80-\u0DFF]")

# Common Thanglish vocabulary & morphological markers (Latin script Tamil)
_THANGLISH_MARKERS: Set[str] = {
    # Pronouns & People
    "ennaku", "enakku", "enaku", "ungalluku", "ungalukku", "ungalku",
    "namma", "namakku", "unaku", "enakum", "ungallukum", "naan", "neenga",
    # Question words
    "epdi", "eppadi", "yapadi", "ebdi", "yeppidi",
    "enna", "ena", "yennadhu", "ennathu", "yena",
    "enga", "engae", "enge", "yenga", "engey",
    "evvalavu", "evlo", "evalavu", "ethana", "ethanai",
    "eppo", "yeppo", "eppodhu", "yeppodhu",
    "yaaru", "yaar", "yaru", "yarukku",
    "edhuku", "ethuku", "yen", "yethukku",
    # Verbs & Verbal Participles
    "edukka", "edukkaradhu", "edukkuradhu", "eduka", "edukurathu", "edukanum",
    "vaanga", "vaanguradhu", "vanga", "peruvathu", "vanganum",
    "venum", "vendum", "theva", "thevai", "thevapadum",
    "poganum", "ponum", "sella", "poga",
    "panna", "pannuradhu", "panradhu", "panrathu", "pannungalen", "pannanum", "pananum", "pannalaam",
    "mudiyuma", "mudiyum", "panlam", "mudiyadhu",
    "kudunga", "kudu", "sollunga", "sollu", "sollala", "sollalaam", "thaanga", "thanga",
    "kattanam", "katnam", "panam", "kaasu",
    "paththi", "patri", "patthi", "thodarpa",
    "thirumba", "marupadiyum", "puthupikka", "puthusa",
    "thozhil", "thozil", "vyaparam", "viyabaram",
    "urimam", "urimangal",
    "aavanam", "aavanangal",
    "mugavari", "neram", "thodarpu",
    "illai", "illa", "irukku", "iruka", "irukkiradhu", "theriyuma", "theriyala",
    "kedaikkuma", "kedaikum", "kidaikkala", "kidaikuma", "valangapadum",
    "madhiri", "mari", "mathiri", "sonna",
}

# Common Singlish vocabulary & morphological markers (Latin script Sinhala)
_SINGLISH_MARKERS: Set[str] = {
    "kohomada", "komada", "monawada", "mokakda", "mokadda",
    "koheda", "kohetada", "kiyada", "gaasthuwa", "mudal",
    "ganna", "labaganna", "gannata", "ganna puluwanda",
    "liyakiyawili", "lekanam", "awashya", "ona", "one",
    "aluth", "karanne", "kireema", "balapathraya", "balapathra",
    "wiyapara", "vyapara", "piyawara", "karanna",
    "puluwanda", "puluwan", "danna", "kiyanna", "thena",
    "oyata", "mata", "wage",
}


def detect_language(text: str) -> LanguageInfo:
    """
    Analyzes a natural language string and identifies the language, script,
    and code-mixing properties.
    """
    if not text or not text.strip():
        return LanguageInfo(
            language=LanguageCode.UNKNOWN,
            script="unknown",
            confidence=0.0,
            is_multilingual=False,
        )

    clean_text = text.strip()
    lower = clean_text.lower()

    # 1. Check for Tamil Script
    tamil_chars = _TAMIL_SCRIPT_REGEX.findall(clean_text)
    if tamil_chars:
        ratio = len(tamil_chars) / max(len(clean_text), 1)
        return LanguageInfo(
            language=LanguageCode.TAMIL,
            script="tamil",
            confidence=min(1.0, 0.7 + ratio * 0.3),
            is_multilingual=True,
            detected_markers=tamil_chars[:10],
            details={"char_count": str(len(tamil_chars)), "script": "Tamil (Unicode)"},
        )

    # 2. Check for Sinhala Script
    sinhala_chars = _SINHALA_SCRIPT_REGEX.findall(clean_text)
    if sinhala_chars:
        ratio = len(sinhala_chars) / max(len(clean_text), 1)
        return LanguageInfo(
            language=LanguageCode.SINHALA,
            script="sinhala",
            confidence=min(1.0, 0.7 + ratio * 0.3),
            is_multilingual=True,
            detected_markers=sinhala_chars[:10],
            details={"char_count": str(len(sinhala_chars)), "script": "Sinhala (Unicode)"},
        )

    # 3. Check for Thanglish / Singlish in Latin Script
    tokens = re.findall(r"\b[a-zA-Z]+\b", lower)
    thanglish_found = [t for t in tokens if t in _THANGLISH_MARKERS]
    singlish_found = [t for t in tokens if t in _SINGLISH_MARKERS]

    # Special phrase checks (e.g., 'apply panna', 'documents venum', 'fee evlo', 'ganna one', 'licence venum', 'enna business')
    has_thanglish_phrase = bool(re.search(
        r"\b(apply\s+panna|apply\s+panradhu|epdi\s+edukurathu|edukka\s+ena|edukka\s+enna|enga\s+poganum|procedure\s+enna|documents\s+venum|evlo\s+fee|fee\s+evvalavu|fee\s+evlo|ku\s+evlo|edukka\s+mudiyuma|licen[cs]e\s+edukanum|licen[cs]e\s+venum|enna\s+business|enna\s+licen[cs]e|start\s+panna)\b",
        lower
    ))
    has_singlish_phrase = bool(re.search(
        r"\b(ganna\s+kohomada|awashya\s+liyakiyawili|gaasthuwa\s+kiyada|koheda\s+yanna|aluth\s+karanne|ganna\s+ona|ganna\s+one|business\s+ekak)\b",
        lower
    ))

    if thanglish_found or has_thanglish_phrase:
        return LanguageInfo(
            language=LanguageCode.THANGLISH,
            script="latin",
            confidence=0.95 if has_thanglish_phrase else min(1.0, 0.7 + len(thanglish_found) * 0.15),
            is_multilingual=True,
            detected_markers=thanglish_found,
            details={"type": "Thanglish / Tamil-English Code-Mixed", "markers": ", ".join(thanglish_found)},
        )

    if singlish_found or has_singlish_phrase:
        return LanguageInfo(
            language=LanguageCode.SINGLISH,
            script="latin",
            confidence=0.95 if has_singlish_phrase else min(1.0, 0.7 + len(singlish_found) * 0.15),
            is_multilingual=True,
            detected_markers=singlish_found,
            details={"type": "Singlish / Sinhala-English Code-Mixed", "markers": ", ".join(singlish_found)},
        )

    # 4. Default: Standard English
    return LanguageInfo(
        language=LanguageCode.ENGLISH,
        script="latin",
        confidence=0.99,
        is_multilingual=False,
        detected_markers=[],
        details={"type": "English"},
    )


def resolve_query_language(text: str) -> LanguageCode:
    """
    Convenience resolver that returns the canonical LanguageCode for a query text.
    """
    info = detect_language(text)
    return info.language

