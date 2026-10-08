"""
GovGuide AI — Thanglish, Tamil & Sinhala Multilingual Normalizer

Converts queries written in:
- Thanglish (Tamil written in English/Latin letters)
- Tamil script (தமிழ்)
- Sinhala script (සිංහල)
- Singlish (Sinhala written in English/Latin letters)
- Tamil-English / Sinhala-English code-mixed queries

Into standard English representations while strictly preserving:
- Original citizen intent (fees, documents, procedures, office info, renewal, eligibility)
- Specific license types and service entities
- Conservative semantics (never hallucinating or switching intent).
"""

import re
from typing import Dict, List, Tuple


# ── Canonical High-Level Sentence/Idiom Rewrites ─────────────────────────────

_EXACT_OR_IDIOMATIC_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # ── Tamil Script Specific Phrases ─────────────────────────────────────────
    (re.compile(r"வணிக\s+உரிமம்\s+பெறுவது\s+எப்படி\??", re.I), "how can i obtain a business license?"),
    (re.compile(r"உணவக\s+உரிமத்திற்கு\s+என்ன\s+ஆவணங்கள்\s+தேவை\??", re.I), "what documents are required for restaurant license?"),
    (re.compile(r"வணிக\s+உரிம\s+கட்டணம்\s+எவ்வளவு\??", re.I), "what is the business license fee?"),
    (re.compile(r"வணிக\s+உரிமம்\s+பெற\s+எங்கு\s+செல்ல\s+வேண்டும்\??", re.I), "where should i go to get a business license?"),
    (re.compile(r"உரிமத்தை\s+எவ்வாறு\s+புதுப்பிப்பது\??", re.I), "how to renew license?"),
    (re.compile(r"வணிக\s+உரிம\s+விண்ணப்ப\s+முறை\s+என்ன\??", re.I), "what is the application procedure for business license?"),

    # ── Sinhala Script Specific Phrases ───────────────────────────────────────
    (re.compile(r"ව්‍යාපාර\s+බලපත්‍රයක්\s+ලබා\s+ගන්නේ\s+කෙසේද\??", re.I), "how can i obtain a business license?"),
    (re.compile(r"ආපනශාලා\s+බලපත්‍ර\s+ගාස්තුව\s+කීයද\??", re.I), "how much is the restaurant license fee?"),
    (re.compile(r"ව්‍යාපාර\s+බලපත්‍රයක්\s+සඳහා\s+අවශ්‍ය\s+ලියකියවිලි\s+මොනවාද\??", re.I), "what documents are required for a business license?"),
    (re.compile(r"බලපත්‍ර\s+කාර්යාලය\s+කොහෙද\s+තියෙන්නේ\??", re.I), "where is the license office?"),
    (re.compile(r"බලපත්‍රය\s+අලුත්\s+කරන්නේ\s+කෙසේද\??", re.I), "how to renew license?"),
    (re.compile(r"ව්‍යාපාර\s+බලපත්‍ර\s+ක්‍රියාවලිය\s+මොකක්ද\??", re.I), "what is the procedure for a business license?"),

    # "enna enna business license inga edulkkalam / edukalam / irukku" -> "what business licenses are available here"
    (
        re.compile(r"^\s*(?:(?:inga|ingey|inge|ingga)\s+)?(?:enna+\s*[-]?\s*enna+|enna+enna+|yena+\s*[-]?\s*yena+|yena+yena+|enna+|yena+)\s+(?:business\s+|government\s+)?(?:licen[cs]e|services?)(?:s)?(?:\s+(?:inga|ingey|inge|ingga))?\s*(?:edulkkalam|edukkalam|edukalam|edulkkalaam|edukkalaam|edukalaam|edukka\s+mudiyum|vanga\s+mudiyum|vangalam|vangikalam|irukku|kidaikkum|available)?\??\s*$", re.I),
        "what business licenses are available here"
    ),
    (
        re.compile(r"\b(?:(?:inga|ingey|inge|ingga)\s+)?(?:enna+\s*[-]?\s*enna+|enna+enna+|yena+\s*[-]?\s*yena+|yena+yena+)\s+(?:business\s+|government\s+)?(?:licen[cs]e|services?)(?:s)?(?:\s+(?:inga|ingey|inge|ingga))?\s*(?:edulkkalam|edukkalam|edukalam|edulkkalaam|edukkalaam|edukalaam|edukka\s+mudiyum|vanga\s+mudiyum|vangalam|vangikalam|irukku|kidaikkum|available)\??", re.I),
        "what business licenses are available here"
    ),
    (
        re.compile(r"\b(?:inga|ingey|inge|ingga)\s+(?:enna+\s*[-]?\s*enna+|enna+enna+|enna+)\s+(?:business\s+|government\s+)?(?:licen[cs]e|services?)(?:s)?\s*(?:edulkkalam|edukkalam|edukalam|edulkkalaam|edukkalaam|edukalaam|irukku|kidaikkum|available)\??", re.I),
        "what business licenses are available here"
    ),
    (
        re.compile(r"\b(?:enna+\s*[-]?\s*enna+|yena+\s*[-]?\s*yena+|enna+enna+)\s+(?:business\s+|government\s+)?(?:licen[cs]e|services?)(?:s)?\s*(?:irukku|kidaikkum|available|options)\??", re.I),
        "what business licenses are available"
    ),
    (
        re.compile(r"^\s*(?:56\s+)?(?:government\s+)?services?\s*(?:oda\s+)?summary\s*(?:venum|vendum|kudunga|theva|thevai)\??\s*$", re.I),
        "i need 56 government services summary"
    ),
    (
        re.compile(r"\b(?:56\s+)?(?:government\s+)?services?\s*(?:oda\s+)?summary\s*(?:venum|vendum|kudunga|theva|thevai)\??", re.I),
        "i need 56 government services summary"
    ),
    (
        re.compile(r"\b(?:available|all)\s+(?:56\s+)?(?:business\s+|government\s+)?(?:licen[cs]e|services?)(?:s)?\s+(?:list|options|summary)\s*(?:sollunga|kudunga|kaatunga)\??", re.I),
        "show all available business licenses"
    ),
    (
        re.compile(r"இங்கு\s+என்னென்ன\s+வணிக\s+உரிமங்கள்\s+கிடைக்கும்\??", re.I),
        "what business licenses are available here"
    ),

    # "licence venum but enna business nu sollala" -> "i need a license but have not specified business type"
    (
        re.compile(r"\blicen[cs]e\s+(?:venum|vendum|edukanum|edukkanum|vanganum)\s+but\s+enna\s+business\s+(?:nu|endru)?\s*sollala\??", re.I),
        "i need a license but have not specified business type"
    ),

    # "ennaku licence edukanum" / "ennaku licence venum" / "ennaku licence edukkan" -> "i need to obtain a license"
    (
        re.compile(r"^\s*(?:ennaku|enakku|enaku)\s+licen[cs]e(?:s)?\s+(?:edukanum|edukkanum|edukkanam|edukkan|edukan|vanganum|venum|theva|thevai)\??\s*$", re.I),
        "i need to obtain a license"
    ),
    (
        re.compile(r"^\s*licen[cs]e(?:s)?\s+(?:edukanum|edukkanum|edukkanam|edukkan|edukan|vanganum|venum|theva|thevai)\??\s*$", re.I),
        "i need to obtain a license"
    ),

    # "naan dress shop start panna poren" -> "what license is required to start a dress shop"
    (
        re.compile(r"^\s*(?:naan\s+)?([a-z0-9_\-\s]+?)\s+(?:start\s+panna|open\s+panna|aarambikka)\s+(?:poren|poran|mudivupanniruken)\??\s*$", re.I),
        r"what license is required to start \1"
    ),

    # "food licence epdi apply pannanum" -> "how can i apply for food license"
    (
        re.compile(r"([a-z\s]+?)\s+(?:epdi|eppadi|ebdi)\s+(?:apply\s+pannanum|apply\s+panradhu|vinnapikka)\??", re.I),
        r"how can i apply for \1"
    ),

    # "food business start panna enna license venum" / "naan restaurant open panna poren enna licence venum?" -> "what license is required to start a food business"
    (
        re.compile(r"(?:naan\s+)?([a-z0-9_\-\s]+?)\s+(?:start\s+panna|open\s+panna|aarambikka)(?:\s+(?:poren|poran))?\s+(?:enna|ena|yena)\s+(?:license|licenses|licenss|lisense|licnse|licence|licences|urimam)\s+(?:venum|vendum|theva|thevai)\??", re.I),
        r"what license is required to start \1"
    ),
    # "XYZABC123 business-ku enna licence venum?" -> "what license is required for XYZABC123 business"
    (
        re.compile(r"([a-z0-9_\-\s]+?)(?:-?ku|-uku)\s+(?:enna|ena|yena)\s+(?:licen[cs]e|licenses|licenss|lisense|licnse|urimam)\s+(?:venum|vendum|theva|thevai)\??", re.I),
        r"what license is required for \1"
    ),
    # "i like to start a new food bsness which licenss perfect for me" -> "i want to start a new food business which license is suitable for me"
    (
        re.compile(r"\bi\s+(?:like|want|wish)\s+to\s+start\s+(?:a\s+)?(?:new\s+)?([a-z\s]+?)\s+which\s+(?:license|licenses|licenss|lisense|licnse)\s+(?:is\s+)?(?:perfect|suitable|best|good)\s+for\s+me\??", re.I),
        r"i want to start a new \1 which license is suitable for me"
    ),
    # "business licnse epdi edukurathu" -> "How can I obtain/apply for a business license?"
    (
        re.compile(r"(?:how\s+to\s+)?([a-z\s]+?)\s+(?:epdi|eppadi|ebdi|yapadi)\s+(?:edukurathu|edukkaradhu|edukkuradhu|eduka|edukka|vaanguradhu|vaanga|edukanum)\??", re.I),
        r"how to get \1"
    ),
    # "business lisense edukka ena documents venum" -> "What documents are required to obtain a business license?"
    (
        re.compile(r"([a-z\s]+?)\s+(?:edukka|vaanga|apply\s+panna)\s+(?:ena|enna|yena)\s+(?:documents|document|aavanangal|papers)\s+(?:venum|vendum|theva|thevai)\??", re.I),
        r"what documents are required to obtain \1"
    ),
    # "business license edukka enga poganum?" -> "Where should I go to apply for a business license?"
    (
        re.compile(r"([a-z\s]+?)\s+(?:edukka|vaanga|apply\s+panna)\s+(?:enga|engae|enge|yenga)\s+(?:poganum|ponum|sella\s+vendum)\??", re.I),
        r"where should i go to apply for \1"
    ),
    # "business license apply panna procedure enna?" -> "What is the procedure for applying for a business license?"
    (
        re.compile(r"([a-z\s]+?)\s+(?:apply\s+panna|apply\s+panradhu|vinnapikka)\s+(?:procedure|steps|process)\s+(?:enna|ena|yennadhu)\??", re.I),
        r"what is the procedure for applying for \1"
    ),
    # "busines licnse aplicaton epdi?" -> "How do I apply for a business license?"
    (
        re.compile(r"([a-z\s]+?)\s+(?:application|aplicaton|applicaton)\s+(?:epdi|eppadi|ebdi|yapadi)\??", re.I),
        r"how do i apply for \1"
    ),
    # Fee queries in Thanglish (Conservative: keeps fee intent!)
    (
        re.compile(r"([a-z\s]+?)\s+(?:ku\s+)?(?:evvalavu|evlo|evalavu|evvalavu)\s+(?:fee|fees|cost|kattanam|katnam|panam)\??", re.I),
        r"what is the fee for \1"
    ),
    (
        re.compile(r"([a-z\s]+?)\s+(?:fee|fees|cost|kattanam|katnam)\s+(?:evvalavu|evlo|evalavu|enna|ena)\??", re.I),
        r"what is the fee for \1"
    ),
    # Renewal queries in Thanglish
    (
        re.compile(r"([a-z\s]+?)\s+(?:renew\s+panna|puthupikka|renew\s+panradhu)\s+(?:epdi|eppadi|procedure\s+enna)\??", re.I),
        r"how to renew \1"
    ),
    # Eligibility queries in Thanglish
    (
        re.compile(r"([a-z\s]+?)\s+(?:edukka\s+)?(?:yarukku|yaaru|yaar)\s+(?:eligibility|qualification|eligible|mudiyum)\??", re.I),
        r"who is eligible for \1"
    ),
    (
        re.compile(r"([a-z\s]+?)\s+(?:eligibility|thiguthi|qualification)\s+(?:enna|ena)\??", re.I),
        r"what is the eligibility for \1"
    ),

    # ── Singlish (Sinhala in Latin) Canonical Patterns ────────────────────────
    (
        re.compile(r"([a-z\s]+?)\s+(?:ganna|labaganna)\s+(?:kohomada|komada)\??", re.I),
        r"how to get \1"
    ),
    (
        re.compile(r"([a-z\s]+?)\s+(?:ganna\s+)?(?:awashya|ona|one)\s+(?:liyakiyawili|documents)\s+(?:monawada|mokakda)\??", re.I),
        r"what documents are required for \1"
    ),
    (
        re.compile(r"([a-z\s]+?)\s+(?:ekata\s+)?(?:gaasthuwa|fee|fees|mudal)\s+(?:kiyada|monawada)\??", re.I),
        r"what is the fee for \1"
    ),
    (
        re.compile(r"([a-z\s]+?)\s+(?:ganna\s+)?(?:koheda|kohetada)\s+(?:yanna\s+one|yanna\s+ona|thiyenne)\??", re.I),
        r"where should i go to apply for \1"
    ),
    (
        re.compile(r"([a-z\s]+?)\s+(?:aluth\s+karanne|renew\s+karanne)\s+(?:kohomada|komada)\??", re.I),
        r"how to renew \1"
    ),
]


# ── Vocabulary & Token Mappings ──────────────────────────────────────────────

_TAMIL_WORD_MAP: Dict[str, str] = {
    # Pronouns & Subjects
    "ennaku": "for me",
    "enakku": "for me",
    "enaku": "for me",
    "ungalluku": "for you",
    "ungalukku": "for you",
    "ungalku": "for you",
    "namma": "our",
    "namakku": "for us",
    "unaku": "for you",
    "naan": "i",
    "neenga": "you",
    "eppadi": "how",
    "yapadi": "how",
    "ebdi": "how",
    "yeppidi": "how",
    "enna": "what",
    "ena": "what",
    "yennadhu": "what",
    "ennathu": "what",
    "yena": "what",
    "enga": "where",
    "engae": "where",
    "enge": "where",
    "yenga": "where",
    "engey": "where",
    "evvalavu": "how much",
    "evlo": "how much",
    "evalavu": "how much",
    "ethana": "how many",
    "ethanai": "how many",
    "eppo": "when",
    "yeppo": "when",
    "eppodhu": "when",
    "yaaru": "who",
    "yaar": "who",
    "yaru": "who",
    "yarukku": "for whom",
    "edhuku": "why",
    "ethuku": "why",
    "yen": "why",

    # Verbs & Actions
    "edukka": "to get",
    "edukkaradhu": "getting",
    "edukkuradhu": "getting",
    "eduka": "to get",
    "edukurathu": "how to get",
    "edukanum": "need to get",
    "edukkanum": "need to get",
    "edukkanam": "need to get",
    "edukanam": "need to get",
    "edukkan": "need to get",
    "edukan": "need to get",
    "edulkkalam": "can get",
    "edukkalam": "can get",
    "edukalam": "can get",
    "edulkkalaam": "can get",
    "edukkalaam": "can get",
    "edukalaam": "can get",
    "inga": "here",
    "ingga": "here",
    "ingey": "here",
    "inge": "here",
    "licence": "license",
    "licences": "licenses",
    "kidaikkum": "available",
    "vaanga": "to obtain",
    "vaanguradhu": "obtaining",
    "vanga": "to obtain",
    "vanganum": "need to obtain",
    "peruvathu": "to obtain",
    "venum": "required",
    "vendum": "required",
    "theva": "required",
    "thevai": "required",
    "thevapadum": "is required",
    "poganum": "should go",
    "ponum": "should go",
    "poga": "to go",
    "sella": "to go",
    "panna": "to do",
    "panradhu": "doing",
    "panrathu": "doing",
    "pannuradhu": "doing",
    "pannu": "do",
    "kudunga": "give me",
    "kudu": "give",
    "sollunga": "tell me",
    "sollu": "tell",
    "sollala": "not told",
    "sollalaam": "can tell",
    "theriyala": "do not know",
    "kidaikkala": "not available",
    "pannanum": "need to do",
    "pananum": "need to do",
    "thaanga": "give",
    "thanga": "give",
    "puthupikka": "to renew",
    "puthusa": "new",
    "thirumba": "again",
    "marupadiyum": "again",
    "mudiyuma": "can i",
    "mudiyum": "can",
    "panlam": "can do",
    "madhiri": "like",
    "mari": "like",
    "mathiri": "like",

    # Nouns
    "thozhil": "business",
    "thozil": "business",
    "vyaparam": "business",
    "viyabaram": "business",
    "urimam": "license",
    "urimangal": "licenses",
    "aavanam": "document",
    "aavanangal": "documents",
    "kattanam": "fee",
    "katnam": "fee",
    "panam": "cost",
    "kaasu": "cost",
    "mugavari": "address",
    "neram": "hours",
    "thodarpu": "contact",
    "paththi": "about",
    "patri": "about",
    "patthi": "about",
}

_SINHALA_WORD_MAP: Dict[str, str] = {
    "kohomada": "how",
    "komada": "how",
    "monawada": "what",
    "mokakda": "what",
    "mokadda": "what",
    "koheda": "where",
    "kohetada": "where to",
    "kiyada": "how much",
    "gaasthuwa": "fee",
    "mudal": "cost",
    "ganna": "to get",
    "labaganna": "to obtain",
    "liyakiyawili": "documents",
    "awashya": "required",
    "ona": "need",
    "one": "need",
    "aluth": "renew",
    "karanne": "to do",
    "balapathraya": "license",
    "balapathra": "licenses",
    "wiyapara": "business",
    "vyapara": "business",
    "piyawara": "steps",
    "puluwanda": "can i",
    "kiyanna": "tell me",
}

# Direct Tamil Script Word Replacements
_TAMIL_SCRIPT_MAP: Dict[str, str] = {
    "வணிக": "business",
    "வியாபார": "business",
    "உரிமம்": "license",
    "உரிமங்கள்": "licenses",
    "உணவக": "restaurant",
    "மதுபான": "liquor",
    "ஆவணங்கள்": "documents",
    "ஆவணம்": "document",
    "கட்டணம்": "fee",
    "கட்டணங்கள்": "fees",
    "எவ்வளவு": "how much",
    "எப்படி": "how",
    "எங்கு": "where",
    "எப்போது": "when",
    "தேவை": "required",
    "தேவையான": "required",
    "விண்ணப்பிக்க": "apply",
    "விண்ணப்பம்": "application",
    "புதுப்பிக்க": "renew",
    "புதுப்பித்தல்": "renewal",
    "அலுவலகம்": "office",
    "முகவரி": "address",
    "தகுதி": "eligibility",
    "நிபந்தனைகள்": "requirements",
    "பெறுவது": "to get",
}

# Direct Sinhala Script Word Replacements
_SINHALA_SCRIPT_MAP: Dict[str, str] = {
    "ව්‍යාපාර": "business",
    "බලපත්‍රය": "license",
    "බලපත්‍ර": "license",
    "බලපත්‍රයක්": "license",
    "ආපනශාලා": "restaurant",
    "මද්‍යසාර": "liquor",
    "ලියකියවිලි": "documents",
    "ගාස්තුව": "fee",
    "ගාස්තු": "fees",
    "කීයද": "how much",
    "කෙසේද": "how",
    "කොහෙද": "where",
    "කවදාද": "when",
    "අවශ්‍ය": "required",
    "අයදුම්": "apply",
    "ක්‍රියාවලිය": "procedure",
    "අලුත්": "renew",
    "කාර්යාලය": "office",
    "ලිපිනය": "address",
    "සුදුසුකම්": "eligibility",
    "ලබා": "get",
}


def normalize_thanglish_and_multilingual(text: str) -> Tuple[str, bool]:
    """
    Normalizes a Thanglish, Tamil, Sinhala, or code-mixed string into standard English.
    Returns: (normalized_text, was_transformed)
    """
    if not text or not text.strip():
        return "", False

    original = text.strip()
    working = original

    # 1. First test exact idiomatic sentence-level rewrite patterns
    for pattern, replacement in _EXACT_OR_IDIOMATIC_PATTERNS:
        if pattern.search(working):
            rewritten = pattern.sub(replacement, working)
            rewritten = re.sub(r"\s+", " ", rewritten).strip()
            # Clean up double punctuation or grammar
            rewritten = re.sub(r"\s+([?.!,])", r"\1", rewritten)
            return rewritten, True

    was_changed = False

    # 2. Check Tamil Script words
    tamil_words_found = []
    for tamil_term, eng_term in _TAMIL_SCRIPT_MAP.items():
        if tamil_term in working:
            working = working.replace(tamil_term, f" {eng_term} ")
            tamil_words_found.append(tamil_term)
            was_changed = True

    # 3. Check Sinhala Script words
    sinhala_words_found = []
    for sinhala_term, eng_term in _SINHALA_SCRIPT_MAP.items():
        if sinhala_term in working:
            working = working.replace(sinhala_term, f" {eng_term} ")
            sinhala_words_found.append(sinhala_term)
            was_changed = True

    # 4. Check Thanglish / Latin Word-Level Map
    tokens = re.findall(r"\b[a-zA-Z]+\b|[^\w\s]", working)
    normalized_tokens = []

    for token in tokens:
        lower = token.lower()
        if lower in _TAMIL_WORD_MAP:
            normalized_tokens.append(_TAMIL_WORD_MAP[lower])
            was_changed = True
        elif lower in _SINHALA_WORD_MAP:
            normalized_tokens.append(_SINHALA_WORD_MAP[lower])
            was_changed = True
        else:
            normalized_tokens.append(token)

    working = " ".join(normalized_tokens)
    working = re.sub(r"\s+([?.!,;:])", r"\1", working)
    working = re.sub(r"\s+", " ", working).strip()

    # 5. Clean up code-mixed functional particles (e.g., "business license ku fee" -> "business license fee")
    working = re.compile(r"\bku\b", re.I).sub("for", working)
    working = re.compile(r"\bekata\b", re.I).sub("for", working)
    working = re.compile(r"\boda\b", re.I).sub("with", working)
    working = re.compile(r"\bmathiri\b", re.I).sub("like", working)

    working = re.sub(r"\s+", " ", working).strip()

    return working, was_changed or (working != original)
