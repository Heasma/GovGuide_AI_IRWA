"""
GovGuide AI — Grounded Prompt Builder (Advisory Agent)

Constructs strictly grounded prompts from the EvidenceBundle.
Enforces Responsible AI invariants, XML data containment, and anti-injection rules.
"""

from typing import Any, Dict, List, Optional
import xml.sax.saxutils as saxutils
from app.config import get_settings

SYSTEM_PROMPT = """You are GovGuide AI, a helpful, conversational government service assistant for City of Chicago business licensing.

Your goal is to answer the citizen's specific question directly, naturally, and concisely using ONLY the retrieved official government records in the <OFFICIAL_EVIDENCE> block.

CONVERSATIONAL GUIDELINES:
1. Speak directly to the citizen as a polite, professional government service advisor.
2. Answer WHAT the user is asking directly. Do NOT start every response with generic boilerplate like "Based on official City of Chicago business licensing records, here is the guidance for your inquiry:".
3. Keep the response length tailored to the question:
   - Short/specific question (e.g. "What is the fee?") -> Concise, direct answer with only the requested information.
   - Comprehensive question (e.g. "Explain everything I need to open a restaurant") -> Structured guide covering overview, eligibility, documents, fees, and steps.
4. Merge multiple evidence records for the same license into ONE unified answer. Never repeat identical license headings.
5. If the requested information (fee, renewal deadline, eligibility, documents) is missing, unverified, or marked NOT_AVAILABLE in the official evidence:
   - Explicitly state that the information is unavailable in current official records.
   - Direct the citizen to BACP or Chicago Business Direct.
   - NEVER invent, assume, or estimate missing government facts.
6. CITE sources cleanly using bracket notation, e.g. [Source 1], [Source 2].
"""

EVIDENCE_HEADER = "<OFFICIAL_EVIDENCE>\n"
EVIDENCE_FOOTER = "\n</OFFICIAL_EVIDENCE>"


def sanitize_text_for_evidence(text: str) -> str:
    """
    Sanitizes evidence text to prevent tag injection or malformed XML delimiters.
    """
    if not text:
        return ""
    neutralized = text.replace("</OFFICIAL_EVIDENCE>", "[ESCAPED_DELIMITER]")
    neutralized = neutralized.replace("<OFFICIAL_EVIDENCE>", "[ESCAPED_DELIMITER]")
    safe = saxutils.escape(neutralized)
    return safe


INTENT_SECTION_MAP = {
    "fees": ["fees", "overview"],
    "required_documents": ["required_documents", "overview"],
    "eligibility": ["eligibility", "overview"],
    "application_procedure": ["application_procedure", "overview"],
    "procedure": ["application_procedure", "overview"],
    "comparison": ["overview", "fees", "eligibility", "application_procedure"],
    "source_evidence": ["legal_framework", "overview"],
    "source_verification": ["legal_framework", "overview"],
    "office_information": ["contact_information", "responsible_office"],
    "renewal": ["renewal", "overview"],
    "license_catalog": ["overview", "eligibility"],
    "service_lookup": ["overview", "eligibility"],
    "service_information": ["overview", "eligibility"],
    "license_identification": ["overview", "eligibility"],
}


def _get_intent_instruction(intent_name: str) -> str:
    """Returns explicit intent-specific conversational guidelines for the LLM."""
    if intent_name == "fees":
        return (
            "INTENT: FEES / COSTS\n"
            "- Answer the fee question directly: state the license name, code, fee amount, term, and payment terms.\n"
            "- Do NOT include unrelated sections like eligibility, required documents, or application steps unless asked.\n"
            "- If the fee is missing or NOT_AVAILABLE, state: 'The available records do not currently provide a verified fee amount for this license. Please verify the current fee with the City of Chicago BACP or Chicago Business Direct.'\n"
            "- NEVER invent or estimate a fee."
        )
    elif intent_name == "required_documents":
        return (
            "INTENT: REQUIRED DOCUMENTS\n"
            "- Answer directly with a clean bulleted list of required documents for the license.\n"
            "- Do NOT include unrelated fee schedules or application steps unless asked.\n"
            "- If documents are missing in records, state that documentation must be verified with BACP."
        )
    elif intent_name == "eligibility":
        return (
            "INTENT: ELIGIBILITY / QUALIFICATIONS\n"
            "- Answer directly: state who is eligible and any qualification criteria or location rules.\n"
            "- Do NOT append the full application procedure."
        )
    elif intent_name in ("application_procedure", "procedure"):
        return (
            "INTENT: APPLICATION PROCEDURE / STEPS\n"
            "- Provide a clear, numbered step-by-step application procedure (1. ..., 2. ..., etc.).\n"
            "- Mention online application via Chicago Business Direct and any inspection requirement."
        )
    elif intent_name == "comparison":
        return (
            "INTENT: COMPARISON\n"
            "- Provide a clear comparison between the licenses (markdown table comparing codes, categories, fees, inspections, terms).\n"
            "- Highlight key distinctions concisely."
        )
    elif intent_name in ("source_evidence", "source_verification"):
        return (
            "INTENT: SOURCE VERIFICATION & LEGAL BASIS\n"
            "- State the governing authority (BACP) and legal reference (Municipal Code of Chicago).\n"
            "- Cite official document title and verification status."
        )
    elif intent_name == "renewal":
        return (
            "INTENT: LICENSE RENEWAL & VALIDITY\n"
            "- If renewal details exist, state the validity term and renewal procedure.\n"
            "- If renewal information is missing or unverified, state: 'I found information about the license, but the available official records do not provide enough verified information about the renewal process or renewal deadline. I don't want to guess. Please verify current renewal requirements with BACP.'"
        )
    elif intent_name == "office_information":
        return (
            "INTENT: OFFICE & CONTACT INFORMATION\n"
            "- Provide Department name (BACP), Small Business Center address (121 N. LaSalle St., Room 800), hours, and phone."
        )
    elif intent_name in ("license_catalog", "available_business_licenses"):
        return (
            "INTENT: LICENSE CATALOG / AVAILABLE BUSINESS LICENSES\n"
            "- The user is asking for a list/catalog of available business licenses or government services.\n"
            "- Present a structured list of distinct business licenses available in the Knowledge Base evidence.\n"
            "- For each license, include its name, code, and a brief summary.\n"
            "- Conclude by inviting the user to specify their business type so you can help identify the most relevant option.\n"
            "- Do NOT invent licenses not present in the retrieved evidence."
        )
    elif intent_name in ("service_lookup", "service_information", "license_identification"):
        return (
            "INTENT: LICENSE IDENTIFICATION / LOOKUP\n"
            "- Identify the relevant license name and code, and explain briefly why it applies to the user's business activity."
        )
    return (
        "INTENT: GENERAL ADVISORY\n"
        "- Answer the citizen's inquiry directly, politely, and concisely."
    )



def build_prompt(
    query: str,
    evidence_bundle: Dict[str, Any],
    nlp_analysis: Optional[Dict[str, Any]] = None,
    max_evidence_chunks: int = 6,
) -> str:
    """
    Builds an intent-aware, grounded, injection-resistant prompt for the LLM.

    Args:
        query: Sanitized citizen query.
        evidence_bundle: Evidence bundle dict containing results and sources.
        nlp_analysis: Optional NLP analysis metadata containing intent.
        max_evidence_chunks: Maximum number of top evidence chunks to include.

    Returns:
        Complete prompt string containing system instructions, delimited evidence, and citizen query.
    """
    raw_results = evidence_bundle.get("results", [])

    # Extract intent(s) from NLP analysis or fall back to classification
    intents_list: List[str] = []
    if nlp_analysis and isinstance(nlp_analysis, dict):
        raw_intents = nlp_analysis.get("intents", [])
        if raw_intents:
            for it in raw_intents:
                val = it.value if hasattr(it, "value") else str(it)
                if val.lower() not in intents_list:
                    intents_list.append(val.lower())
        if not intents_list:
            raw_intent = nlp_analysis.get("intent")
            if hasattr(raw_intent, "value"):
                intents_list = [str(raw_intent.value).lower()]
            elif raw_intent:
                intents_list = [str(raw_intent).lower()]
    else:
        from app.nlp.intent_classifier import classify_intents
        classified_list = classify_intents(query)
        intents_list = [
            (c.value if hasattr(c, "value") else str(c)).lower()
            for c in classified_list
        ]

    if not intents_list:
        intents_list = ["general"]

    intent_val = intents_list[0]
    if len(intents_list) > 1:
        instructions_parts = [
            "MULTIPLE INTENTS DETECTED IN QUERY:\n"
            "You MUST address EVERY requested topic below in your response. "
            "Do not omit any requested intent. "
            "If evidence for a specific topic is unavailable or unverified in the records, "
            "explicitly state that the information is unavailable without inventing facts.\n"
        ]
        for it in intents_list:
            instructions_parts.append(f"--- Topic: {it.upper()} ---\n{_get_intent_instruction(it)}")
        intent_instructions = "\n\n".join(instructions_parts)
    else:
        intent_instructions = _get_intent_instruction(intent_val)

    if not raw_results:
        evidence_block = (
            f"{EVIDENCE_HEADER}"
            "[No official evidence was retrieved from the database for this query.]\n"
            f"{EVIDENCE_FOOTER}"
        )
    else:
        # Sort chunks to prioritize intent-relevant sections
        preferred_sections = INTENT_SECTION_MAP.get(intent_val, ["overview"])
        
        def _sort_key(item: dict) -> int:
            sec = (item.get("section") or "").lower()
            if sec in preferred_sections:
                return preferred_sections.index(sec)
            return 99

        sorted_results = sorted(raw_results, key=_sort_key)
        if intent_val in ("license_catalog", "available_business_licenses") or "license_catalog" in intents_list:
            selected_results = sorted_results
        else:
            selected_results = sorted_results[:max_evidence_chunks]
        evidence_items = []

        for i, item in enumerate(selected_results, start=1):
            source_id = item.get("source_id", "N/A")
            title = sanitize_text_for_evidence(item.get("source_title", "Official Source"))
            url = item.get("source_url") or "https://www.chicago.gov/BusinessDirect"
            code = item.get("service_code", "N/A")
            section = item.get("section", "general")
            content = sanitize_text_for_evidence(item.get("text") or item.get("content", ""))

            item_str = (
                f"[Source {i}]\n"
                f"Source ID: {source_id}\n"
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"License Code: {code}\n"
                f"Section: {section}\n"
                f"Content:\n{content}"
            )
            evidence_items.append(item_str)

        evidence_body = "\n\n".join(evidence_items)
        evidence_block = f"{EVIDENCE_HEADER}{evidence_body}{EVIDENCE_FOOTER}"

    prompt_body = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{evidence_block}\n\n"
        f"=== CITIZEN QUERY ===\n"
        f"{query}\n\n"
        f"=== DETECTED INTENT & SPECIFIC GUIDELINES ===\n"
        f"{intent_instructions}\n\n"
        f"=== RESPONSE INSTRUCTIONS ===\n"
        f"Answer the citizen's query based exclusively on the official evidence above. "
        f"Include appropriate [Source N] citations in your answer. "
        f"Follow the intent-specific guidelines strictly."
    )

    return prompt_body
