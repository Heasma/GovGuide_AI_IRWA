"""
GovGuide AI — Security & Adversarial Query Guard

Detects, classifies, and blocks adversarial queries attempting to manipulate
the AI system, extract system prompts/metadata, override instructions, or bypass safety rules.

Categories:
- SYSTEM_PROMPT_EXTRACTION: Leaking hidden prompts, internal instructions
- INSTRUCTION_OVERRIDE: Overriding system instructions, claiming user priority
- FAKE_SYSTEM_MESSAGE: Spoofing system/admin messages or control tokens
- ROLEPLAY_JAILBREAK: Persona hijacking, DAN mode, unrestricted roleplay
- DEVELOPER_MODE: Claiming developer/unrestricted mode to disable controls
- AUTHORITY_BYPASS: Impersonating government administrators to escalate privilege
- INTERNAL_METADATA_EXTRACTION: Demanding internal retrieval info, keys, hidden metadata
- RAG_INJECTION: Instructing the model to obey retrieved content over system rules
- SECURITY_POLICY_EXTRACTION: Probing hidden security rules or exact restrictions
- NORMAL: Legitimate citizen questions about government services and licenses
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.orchestrator.message_schema import SecurityClassification, SecurityAction


@dataclass
class SecurityCheckResult:
    classification: SecurityClassification
    action: SecurityAction
    is_safe: bool
    confidence: float = 1.0
    reason: str = ""
    matched_pattern: str = ""
    safe_response: str = ""


@dataclass
class InjectionCheckResult:
    """Backward-compatible result structure for existing consumers."""
    is_safe: bool
    reason: str = ""
    matched_pattern: str = ""


# ── Controlled Safe Response Templates ────────────────────────────────────────

_SECURITY_RESPONSE_TEMPLATES: Dict[SecurityClassification, str] = {
    SecurityClassification.SYSTEM_PROMPT_EXTRACTION: (
        "I cannot provide hidden system instructions, internal prompts, or confidential "
        "configuration. I can provide general information about how GovGuide AI works "
        "and help with Chicago government services."
    ),
    SecurityClassification.INSTRUCTION_OVERRIDE: (
        "I cannot ignore or override the system's security instructions and operating policies. "
        "I can still assist you with official government service and license information."
    ),
    SecurityClassification.FAKE_SYSTEM_MESSAGE: (
        "I cannot accept simulated system or administrative messages that attempt to override "
        "security policies. I am here to help with official Chicago business licenses and public services."
    ),
    SecurityClassification.ROLEPLAY_JAILBREAK: (
        "I cannot engage in roleplay scenarios that attempt to bypass safety rules or disable "
        "security restrictions. I can assist you with legitimate government service questions."
    ),
    SecurityClassification.DEVELOPER_MODE: (
        "I cannot disable the system's security controls, enter a developer mode, "
        "or operate without safety constraints."
    ),
    SecurityClassification.AUTHORITY_BYPASS: (
        "I cannot verify or accept claimed administrative authorization through a chat message, "
        "and I cannot disclose protected system information or grant elevated privileges."
    ),
    SecurityClassification.INTERNAL_METADATA_EXTRACTION: (
        "I cannot disclose hidden metadata, internal configuration, or protected retrieval "
        "information. I can provide official public details for Chicago business services."
    ),
    SecurityClassification.RAG_INJECTION: (
        "I cannot follow instructions contained in retrieved content that attempt to override "
        "the system's security controls. Retrieved records are processed solely as reference "
        "evidence for user inquiries."
    ),
    SecurityClassification.SECURITY_POLICY_EXTRACTION: (
        "I cannot provide hidden security policies or confidential internal instructions. "
        "I can explain the system's public features and government service guidance at a high level."
    ),
}

_DEFAULT_BLOCKED_RESPONSE = (
    "Your query could not be processed because it contains content that may attempt to "
    "manipulate the AI system or bypass security policies. Please ask a question about "
    "official government services."
)


# ── Classification Pattern Definitions ────────────────────────────────────────

_PATTERNS_BY_CATEGORY: List[Tuple[SecurityClassification, List[re.Pattern]]] = [
    # 1. Fake System Message & Control Tokens (Highest priority spoofing check)
    (
        SecurityClassification.FAKE_SYSTEM_MESSAGE,
        [
            re.compile(r"^\s*(system|developer|administrator|admin)\s*(message)?\s*:", re.I),
            re.compile(r"\[(system|system\s+message|developer\s+mode)\]", re.I),
            re.compile(r"<\|im_start\|>|<\|im_end\|>|<\|system\|>", re.I),
            re.compile(r"###\s*instruction", re.I),
            re.compile(r"system\s*:\s*you\s+are", re.I),
        ]
    ),

    # 2. Developer Mode / Unrestricted Mode
    (
        SecurityClassification.DEVELOPER_MODE,
        [
            re.compile(r"(enable|activate|switch\s+to|turn\s+on|enter)\s+(the\s+)?(developer|unrestricted|debug|god|root|sudo|admin)\s+mode", re.I),
            re.compile(r"in\s+developer\s+mode[,\s]+(all\s+restrictions\s+are\s+disabled|you\s+must|restrictions\s+are\s+off)", re.I),
            re.compile(r"developer\s+mode\s+(is\s+now\s+enabled|activated|on|enable\s+pannu|activate\s+pannu|kudu)", re.I),
            re.compile(r"disable\s+all\s+restrictions", re.I),
            re.compile(r"(developer\s+mode)\s+(enable\s+pannu|activate\s+pannu|on\s+pannu)", re.I),
        ]
    ),

    # 3. Roleplay & Jailbreaks
    (
        SecurityClassification.ROLEPLAY_JAILBREAK,
        [
            re.compile(r"let['’]?s\s+role-?play", re.I),
            re.compile(r"(pretend|role-?play|act)\s+(that\s+|as\s+(if\s+)?)?(you\s+are\s+)?(an?\s+)?(unrestricted|jailbroken|evil|unfiltered|uncensored|dan\b|without\s+safety)", re.I),
            re.compile(r"you\s+are\s+(now\s+)?(an?\s+)?unrestricted\s+ai", re.I),
            re.compile(r"you\s+are\s+now\s+(a\s+)?(helpful\s+)?hacker", re.I),
            re.compile(r"do\s+anything\s+now\s*(dan)?", re.I),
            re.compile(r"\bjailbreak\b", re.I),
            re.compile(r"act\s+as\s+an\s+ai\s+without\s+safety\s+restrictions", re.I),
            re.compile(r"pretend\s+(you\s+are|to\s+be)\b", re.I),
            re.compile(r"you\s+are\s+now\s+(a\s+)?(?!govguide)[a-z]+", re.I),
            re.compile(r"act\s+as\s+(if\s+you\s+are|a\s+)?(?!govguide)[a-z]+", re.I),
            re.compile(r"(unrestricted\s+ai|dan\s+mode)\s+(mathiri|mari|mathiriya)\s+(act\s+pannu|nadanthuko)", re.I),
        ]
    ),

    # 4. Authority / Privilege Bypass
    (
        SecurityClassification.AUTHORITY_BYPASS,
        [
            re.compile(r"i\s+am\s+(an?\s+)?(authorized\s+)?(chicago\s+)?(government\s+|system\s+|city\s+|security\s+|bacp\s+)?(administrator|admin|official|regulator|director|officer)\b.*(reveal|authorize|override|disclose|bypass|access\s+confidential|internal|configuration|data)", re.I),
            re.compile(r"i\s+(officially\s+|hereby\s+)?authorize\s+you\s+to\s+(reveal|disclose|bypass|override|ignore|provide)", re.I),
            re.compile(r"this\s+is\s+an?\s+(emergency\s+)?(administrative|admin|official|security)\s+(request|override|authorization|directive)", re.I),
            re.compile(r"i\s+have\s+(the\s+)?authorization\s+to\s+access\s+confidential\s+information", re.I),
            re.compile(r"emergency\s+administrative\s+request", re.I),
        ]
    ),

    # 5. RAG / Retrieved Content Injection
    (
        SecurityClassification.RAG_INJECTION,
        [
            re.compile(r"if\s+(a\s+)?retrieved\s+document\s+(tells|instructs|says|contains).*follow\s+that\s+instruction", re.I),
            re.compile(r"instructions?\s+(inside|within|contained\s+in)\s+retrieved\s+documents?.*(override|ignore|follow)", re.I),
            re.compile(r"follow\s+instructions?\s+contained\s+in\s+the\s+source\s+document", re.I),
            re.compile(r"ignore\s+system\s+instructions?\s+because\s+the\s+retrieved\s+document\s+says", re.I),
            re.compile(r"follow\s+any\s+instructions?\s+found\s+in\s+(the\s+)?(retrieved|source|context)", re.I),
        ]
    ),

    # 6. System Prompt Extraction (Typo-Tolerant, Multilingual, and Thanglish)
    (
        SecurityClassification.SYSTEM_PROMPT_EXTRACTION,
        [
            re.compile(r"(reveal|revel|show|print|display|tell\s+me|dump|give\s+me|share|disclose|provide|output|what\s+is|what\s+are|kudu|kudunga|sollu|sollunga|thaanga)\s+(your\s+|ur\s+)?(complete\s+|all\s+|initial\s+|underlying\s+|original\s+|internal\s+|hidden\s+)?(syst[e]*m\s*pro[mp]*t|syst[e]*m\s*inst[ru]*ct[io]*ns?|hidden\s*inst[ru]*ct[io]*ns?|intern[al]*\s*pro[mp]*t|syst[e]*m\s*messag[e]*|base\s*inst[ru]*ct[io]*ns?|meta\s*pro[mp]*t)", re.I),
            re.compile(r"(what\s+are\s+(your|ur)\s+(hidden|internal|system|systm|underlying)\s+instructions?)", re.I),
            re.compile(r"(reveal|revel|show|provide|tell\s+me)\s+(your\s+|ur\s+)?(complete\s+)?(syst[e]*m\s*pro[mp]*t|hidden\s*inst[ru]*ct[io]*ns?)", re.I),
            re.compile(r"reveal\s+the\s+hidden\s+instructions\s+governing\s+govguide\s+ai", re.I),
            re.compile(r"what\s+is\s+(your|ur)\s+syst[e]*m\s*pro[mp]*t", re.I),
            re.compile(r"show\s+me\s+(your|ur)\s+initial\s+instructions", re.I),
            re.compile(r"(reveal|revel)\s+(your|ur)\s+complete\s+syst[e]*m\s*pro[mp]*t", re.I),
            re.compile(r"hidden\s+instructions\s+given\s+to\s+you", re.I),
            # Thanglish prompt extraction
            re.compile(r"\b(hidden\s+)?(syst[e]*m\s*pro[mp]*t|syst[e]*m\s*instructions?)\s+(kudu|kudunga|sollu|sollunga|reveal\s+pannu|thaanga|kaattu)\b", re.I),
            re.compile(r"\b(syst[e]*m\s*pro[mp]*t)\s+(enna|ena|kudu|sollu)\b", re.I),
            # Typo-tolerant direct extraction combos
            re.compile(r"(reveal|revel|dump|show|output)\s+(syst[e]*m\s*pro[mp]*t)", re.I),
            re.compile(r"\b(syst[e]*m\s*pro[mp]*t)\b.*(reveal|revel|dump|kudu|sollu)", re.I),
            # Tamil and Sinhala script
            re.compile(r"கணினி\s+அறிவுறுத்தல்களை\s*(வெளிப்படுத்து|சொல்லு)", re.I),
            re.compile(r"மறைக்கப்பட்ட\s+அறிவுறுத்தல்கள்", re.I),
            re.compile(r"පද්ධති\s+උපදෙස්\s+(ලබා\s+දෙන්න|පෙන්වන්න)", re.I),
        ]
    ),

    # 7. Internal Metadata & Source Extraction
    (
        SecurityClassification.INTERNAL_METADATA_EXTRACTION,
        [
            re.compile(r"(reveal|revel|show|disclose|dump|output|give\s+me|tell\s+me)\s+(the\s+)?(hidden\s+)?(metadata|internal\s+metadata|retrieval\s+information|ranking\s+details|internal\s+source\s+content|internal\s+configuration|system\s+keys|backend\s+configuration|protected\s+retrieval\s+information)", re.I),
            re.compile(r"disclose\s+(the\s+)?(internal\s+source\s+content|hidden\s+metadata|retrieval\s+information)", re.I),
            re.compile(r"show\s+(hidden\s+)?metadata\s+and\s+internal\s+retrieval\s+information", re.I),
            re.compile(r"information\s+retrieved\s+from\s+your\s+knowledge\s+base\s+is\s+confidential.*(ignore|disclose|reveal)", re.I),
            re.compile(r"(give|show|dump|leak)\s+me\s+(confidential|secret|internal|private)\s+information", re.I),
            re.compile(r"dump\s+internal\s+keys", re.I),
            re.compile(r"reveal\s+hidden\s+metadata", re.I),
        ]
    ),

    # 8. Security Policy Extraction
    (
        SecurityClassification.SECURITY_POLICY_EXTRACTION,
        [
            re.compile(r"(provide|reveal|revel|show|dump|summarize|explain|what\s+are)\s+(your\s+|ur\s+)?(complete\s+|all\s+|full\s+)?(hidden\s+)?(security\s+rules|security\s+policies|hidden\s+security\s+rules|internal\s+security\s+policies|exact\s+restrictions\s+controlling\s+you)", re.I),
            re.compile(r"summarize\s+your\s+hidden\s+security\s+rules", re.I),
            re.compile(r"reveal\s+internal\s+security\s+policies", re.I),
            re.compile(r"explain\s+the\s+exact\s+restrictions\s+controlling\s+you", re.I),
            re.compile(r"provide\s+your\s+complete\s+hidden\s+security\s+rules", re.I),
        ]
    ),

    # 9. Instruction Override & Priority Hijacking (Typo-Tolerant & Multilingual)
    (
        SecurityClassification.INSTRUCTION_OVERRIDE,
        [
            re.compile(r"ign[o]*r[e]*\s+(all\s+)?(prev[io]*us|pr[io]*r|above|syst[e]*m|earl[ie]*r)\s+(inst[ru]*ct[io]*ns?|rul[es]*|guid[el]*in[es]*|polic[ie]*s|restrict[io]*ns?)", re.I),
            re.compile(r"disregard\s+(all\s+)?(prev[io]*us|pr[io]*r|above|syst[e]*m|earl[ie]*r)\s+(inst[ru]*ct[io]*ns?|rul[es]*|guid[el]*in[es]*|polic[ie]*s|restrict[io]*ns?)", re.I),
            re.compile(r"forget\s+(all\s+)?(everything|prev[io]*us|pr[io]*r)\s+(i\s+said|above|before|inst[ru]*ct[io]*ns?|rul[es]*)", re.I),
            re.compile(r"follow\s+(only\s+|strictly\s+)?(my|the\s+user['’]?s?)\s+instructions?\s+(instead|now|from\s+now\s+on)?", re.I),
            re.compile(r"(my|user)\s+instructions?\s+(have|has|take)\s+higher\s+priority", re.I),
            re.compile(r"(from\s+now\s+on|starting\s+now)[,\s]+(ignore\s+all\s+your\s+previous\s+instructions|your\s+only\s+instruction\s+is)", re.I),
            re.compile(r"your\s+system\s+instructions\s+say\s+one\s+thing.*follow\s+my\s+instructions\s+instead", re.I),
            re.compile(r"override\s+(syst[e]*m|security|safety)\s+(rul[es]*|inst[ru]*ct[io]*ns?|policy|policies|restrict[io]*ns?)", re.I),
            re.compile(r"disable\s+(your|all|syst[e]*m)\s+(restrict[io]*ns?|rul[es]*|inst[ru]*ct[io]*ns?|safeguards?|filters?)", re.I),
            re.compile(r"confirm\s+that\s+the\s+previous\s+instructions\s+have\s+been\s+disabled", re.I),
            re.compile(r"ignore\s+(the\s+)?(retrieved\s+)?(documents?|evidence|sources?|context)", re.I),
            # Thanglish and Code-Mixed Instruction Override
            re.compile(r"\b(prev[io]*us\s+inst[ru]*ct[io]*ns?|instruction)\s+(ignore|ignre)\s+(panni|pannu|panradhu|seythu)\b", re.I),
            re.compile(r"\b(syst[e]*m\s*inst[ru]*ct[io]*ns?|insturctions?|instrctions?|instructions?|rules?)\s+(override|ignore|disable|disregard)", re.I),
            re.compile(r"\b(syst[e]*m\s*inst[ru]*ct[io]*ns?|rules?)\s+(override\s+pannu|ignore\s+pannu|disable\s+pannu)\b", re.I),
            re.compile(r"\b(sytem|systm|system)\s+(insturctions?|instrctions?|instructions?)\b", re.I),
            re.compile(r"\b(override|ignore|disable)\s+(panni|pannu)\b", re.I),
            # Tamil and Sinhala script
            re.compile(r"முந்தைய\s+வழிமுறைகளை\s*(புறக்கணி|விட்டுவிட்டு)", re.I),
            re.compile(r"(පෙර\s+උපදෙස්|ආරක්ෂක\s+නීති)\s*නොසලකා\s+හරින්න", re.I),
        ]
    ),
]


def classify_security_query(text: str) -> SecurityCheckResult:
    """
    Evaluates a user query for security threats, prompt injection, and adversarial patterns.
    Operates strictly on the original user query as first line of defense, with typo tolerance
    and multilingual attack pattern matching.

    Returns:
        SecurityCheckResult with classification, action, safe response template, and audit reason.
    """
    if not text or not text.strip():
        return SecurityCheckResult(
            classification=SecurityClassification.NORMAL,
            action=SecurityAction.ALLOW,
            is_safe=True,
            confidence=1.0,
        )

    clean_text = text.strip()

    # Check for direct regex category patterns
    for classification, patterns in _PATTERNS_BY_CATEGORY:
        for pattern in patterns:
            match = pattern.search(clean_text)
            if match:
                template = _SECURITY_RESPONSE_TEMPLATES.get(
                    classification, _DEFAULT_BLOCKED_RESPONSE
                )
                return SecurityCheckResult(
                    classification=classification,
                    action=SecurityAction.BLOCK_AND_SAFE_RESPOND,
                    is_safe=False,
                    confidence=1.0,
                    reason=f"Matched security category {classification.value} with pattern: {pattern.pattern}",
                    matched_pattern=pattern.pattern,
                    safe_response=template,
                )

    # Secondary fuzzy check for adversarial token co-occurrences with typos
    # (e.g., 'ignre' + 'prevous' + 'instrctions', 'reveal' + 'systm' + 'promt')
    lower = clean_text.lower()
    has_ignore = bool(re.search(r"\b(ign[o]*r[e]*|disregard|forget|override|disable)\b", lower))
    has_previous = bool(re.search(r"\b(prev[io]*us|pr[io]*r|above|earl[ie]*r)\b", lower))
    has_instructions = bool(re.search(r"\b(inst[ru]*ct[io]*ns?|rul[es]*|policies|safeguards?)\b", lower))
    has_system_prompt = bool(re.search(r"\b(syst[e]*m\s*pro[mp]*t|hidden\s*promt|system\s*promt)\b", lower))
    has_reveal = bool(re.search(r"\b(rev[ea]*l|revel|dump|leak|disclose|show|kudu|sollu)\b", lower))

    if has_ignore and has_previous and (has_instructions or has_system_prompt):
        return SecurityCheckResult(
            classification=SecurityClassification.INSTRUCTION_OVERRIDE,
            action=SecurityAction.BLOCK_AND_SAFE_RESPOND,
            is_safe=False,
            confidence=1.0,
            reason="Fuzzy co-occurrence match: instruction override with typos/variations.",
            matched_pattern="fuzzy_instruction_override",
            safe_response=_SECURITY_RESPONSE_TEMPLATES[SecurityClassification.INSTRUCTION_OVERRIDE],
        )

    if has_reveal and has_system_prompt:
        return SecurityCheckResult(
            classification=SecurityClassification.SYSTEM_PROMPT_EXTRACTION,
            action=SecurityAction.BLOCK_AND_SAFE_RESPOND,
            is_safe=False,
            confidence=1.0,
            reason="Fuzzy co-occurrence match: system prompt extraction with typos/variations.",
            matched_pattern="fuzzy_system_prompt_extraction",
            safe_response=_SECURITY_RESPONSE_TEMPLATES[SecurityClassification.SYSTEM_PROMPT_EXTRACTION],
        )

    return SecurityCheckResult(
        classification=SecurityClassification.NORMAL,
        action=SecurityAction.ALLOW,
        is_safe=True,
        confidence=1.0,
    )


def get_security_response_template(classification: SecurityClassification) -> str:
    """Returns the dedicated safe response template for a given security classification."""
    return _SECURITY_RESPONSE_TEMPLATES.get(classification, _DEFAULT_BLOCKED_RESPONSE)


def check_for_injection(text: str) -> InjectionCheckResult:
    """
    Backward-compatible check_for_injection used across existing components and tests.
    """
    sec_result = classify_security_query(text)
    if not sec_result.is_safe:
        return InjectionCheckResult(
            is_safe=False,
            reason=sec_result.reason or "Query contains content that may attempt to manipulate the AI system.",
            matched_pattern=sec_result.matched_pattern,
        )
    return InjectionCheckResult(is_safe=True)


def assert_safe(text: str) -> str:
    """
    Raises ValueError if the text contains adversarial patterns.
    Returns the original text if safe.
    """
    result = check_for_injection(text)
    if not result.is_safe:
        raise ValueError(result.reason)
    return text
