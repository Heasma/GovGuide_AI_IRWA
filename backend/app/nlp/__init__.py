"""
GovGuide AI — NLP Pipeline Package
"""

from app.nlp.preprocessor import preprocess, normalize_for_retrieval, expand_query, tokenize_query
from app.nlp.intent_classifier import classify_intent, classify_intents, IntentClassifier
from app.nlp.entity_extractor import extract_entities, resolve_query_entity, ExtractedEntity
from app.nlp.domain_detector import classify_domain, DomainDetector, SUPPORTED_DOMAINS
from app.nlp.language_detector import detect_language, LanguageInfo, LanguageCode
from app.nlp.spelling_corrector import correct_spelling, correct_token
from app.nlp.thanglish_normalizer import normalize_thanglish_and_multilingual
from app.nlp.abbreviation_expander import expand_abbreviations
from app.nlp.query_understanding_service import QueryUnderstandingService, QueryUnderstandingResult

__all__ = [
    "preprocess",
    "normalize_for_retrieval",
    "expand_query",
    "tokenize_query",
    "classify_intent",
    "classify_intents",
    "IntentClassifier",
    "extract_entities",
    "resolve_query_entity",
    "ExtractedEntity",
    "classify_domain",
    "DomainDetector",
    "SUPPORTED_DOMAINS",
    "detect_language",
    "LanguageInfo",
    "LanguageCode",
    "correct_spelling",
    "correct_token",
    "normalize_thanglish_and_multilingual",
    "expand_abbreviations",
    "QueryUnderstandingService",
    "QueryUnderstandingResult",
]
