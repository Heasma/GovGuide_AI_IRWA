import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.nlp.thanglish_normalizer import normalize_thanglish_and_multilingual
from app.nlp.language_detector import detect_language
from app.nlp.intent_classifier import classify_intent, classify_intents
from app.nlp.activity_extractor import extract_business_activity
from app.nlp.query_understanding_service import QueryUnderstandingService

queries = [
    "enna enna business licence inga edukkalam",
    "enna enna business license inga edukkalam",
    "enna enna business license inga edulkkalam",
    "enna enna business licence inga edulkkalam",
    "enna enna license inga edukkalam",
    "enna enna licence inga edukkalam",
    "inga enna enna business license irukku",
    "inga enna enna business licence irukku",
    "what business licenses are available",
    "what business licences are available",
    "show me available business licenses",
]

qus = QueryUnderstandingService()

for q in queries:
    lang = detect_language(q)
    th_norm, mod = normalize_thanglish_and_multilingual(q)
    res = qus.understand_query(q)
    intents = classify_intents(q)
    intent = classify_intent(q)
    act = extract_business_activity(q)
    print(f"=== QUERY: \"{q}\" ===")
    print(f"  detect_language: {lang.language.value}")
    print(f"  thanglish_norm:  \"{th_norm}\" (modified={mod})")
    print(f"  classify_intent: {intent.value if hasattr(intent, 'value') else intent}")
    print(f"  classify_intents: {[it.value if hasattr(it, 'value') else it for it in intents]}")
    print(f"  activity:        {act.activity_type.value}")
    print(f"  result.intent:   {res.intent.value if hasattr(res.intent, 'value') else res.intent}")
    print(f"  result.intents:  {[it.value if hasattr(it, 'value') else it for it in res.intents]}")
    print(f"  result.norm_q:   \"{res.normalized_query}\"")
    print(f"  result.is_ambig: {res.is_ambiguous}")
    print(f"  result.is_domain_supported: {res.is_domain_supported}")
    print()
