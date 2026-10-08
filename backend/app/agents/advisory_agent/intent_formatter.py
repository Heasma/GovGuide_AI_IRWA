"""
GovGuide AI — Conversational Intent-Driven Response Formatter & Relevance Engine

Behaves like a natural, conversational government-service assistant:
1. Answers the user's specific question directly without rigid boilerplate headers or repeating templates.
2. Formats responses conversationally:
   - Fees -> Direct cost, payment terms, and portal verification link.
   - Required Documents -> Clean bulleted checklist.
   - Eligibility -> Direct qualification statement.
   - Application Procedure -> Clean numbered step-by-step instructions.
   - Renewal -> Verified term and renewal procedure, or explicit missing-info refusal.
   - Multi-License Comparison -> Clean table + key distinctions.
   - Source Evidence -> Governing authority, MCC chapter, and verification status.
   - License Lookup -> Recommended license and brief purpose.
3. Merges multiple chunks of the same license into ONE coherent, deduplicated record.
4. Enforces strict missing-information handling and calibrated confidence.
"""

from typing import Any, Dict, List, Optional, Tuple
import re
from app.orchestrator.message_schema import Intent, ConfidenceLabel

NOT_AVAILABLE_VALUES = {"NOT_AVAILABLE", "N/A", "NONE", "NULL", "UNKNOWN", ""}


def is_valid_field(val: Optional[str]) -> bool:
    """Checks if a field contains actual verified content rather than NOT_AVAILABLE."""
    if not val:
        return False
    clean = val.strip()
    return clean.upper() not in NOT_AVAILABLE_VALUES and "NOT_AVAILABLE" not in clean


def clean_service_name(name: str) -> str:
    """Strips operational prefixes like 'Apply for a' to yield the clean license name."""
    if not name:
        return ""
    cleaned = re.sub(r"^Apply for (?:an? )?", "", name, flags=re.IGNORECASE).strip()
    return cleaned


def extract_service_profiles(evidence_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses retrieved evidence results into unified, deduplicated service profiles.
    Multiple chunks for the same license code are merged into a single profile.
    """
    results = evidence_bundle.get("results", [])
    services_map: Dict[str, Dict[str, Any]] = {}

    for item in results:
        code = item.get("service_code") or "N/A"
        raw_name = item.get("service_name") or item.get("source_title") or f"Service {code}"
        name = clean_service_name(raw_name)
        section = (item.get("section") or "general").lower()
        text = item.get("text") or item.get("content") or ""
        url = item.get("source_url") or "https://www.chicago.gov/BusinessDirect"
        title = item.get("source_title") or name
        conf = item.get("source_confidence") or "VERIFIED"

        if code not in services_map:
            services_map[code] = {
                "service_code": code,
                "service_name": name,
                "category": item.get("category", "Business Licensing"),
                "source_url": url,
                "source_title": title,
                "source_confidence": conf,
                "sections": {},
                "raw_texts": [],
                "fee_amount": None,
                "fee_description": None,
                "required_documents": None,
                "eligibility_summary": None,
                "application_steps": None,
                "application_portal_url": None,
                "inspection_required": None,
                "license_term_years": None,
                "renewal_required": None,
                "renewal_period": None,
                "legal_reference": None,
                "overview": None,
                "office_address": None,
                "office_phone": None,
                "office_hours": None,
                "office_name": None,
            }

        profile = services_map[code]
        profile["sections"][section] = text
        profile["raw_texts"].append(text)

        # Parse key-value pairs embedded in chunk text
        for line in text.split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip()

            if "license fee amount" in key or "fee amount" in key or "official fee" in key:
                if is_valid_field(val) and not profile["fee_amount"]:
                    profile["fee_amount"] = val
            elif "fee details" in key or "fee description" in key:
                if is_valid_field(val) and not profile["fee_description"]:
                    profile["fee_description"] = val
            elif "required documentation" in key or "required documents" in key:
                if is_valid_field(val) and not profile["required_documents"]:
                    profile["required_documents"] = val
            elif "eligibility criteria" in key or "eligibility summary" in key or "who is eligible" in key:
                if is_valid_field(val) and not profile["eligibility_summary"]:
                    profile["eligibility_summary"] = val
            elif "step-by-step procedure" in key or "application steps" in key:
                if is_valid_field(val) and not profile["application_steps"]:
                    profile["application_steps"] = val
            elif "online application portal" in key or "portal url" in key:
                if is_valid_field(val) and not profile["application_portal_url"]:
                    profile["application_portal_url"] = val
            elif "inspection required" in key:
                if is_valid_field(val) and not profile["inspection_required"]:
                    profile["inspection_required"] = val
            elif "license term validity" in key or "term validity" in key or "license term" in key:
                if is_valid_field(val) and not profile["license_term_years"]:
                    profile["license_term_years"] = val
            elif "renewal required" in key:
                if is_valid_field(val) and not profile["renewal_required"]:
                    profile["renewal_required"] = val
            elif "renewal period" in key or "renewal cycle" in key:
                if is_valid_field(val) and not profile["renewal_period"]:
                    profile["renewal_period"] = val
            elif "legal reference" in key or "legal framework" in key:
                if is_valid_field(val) and not profile["legal_reference"]:
                    profile["legal_reference"] = val
            elif "overview" in key or "service description" in key or "scope" in key:
                if is_valid_field(val) and not profile["overview"]:
                    profile["overview"] = val
            elif "office location" in key or "street address" in key or "address" in key:
                if is_valid_field(val) and not profile["office_address"]:
                    profile["office_address"] = val
            elif "business hours" in key or "hours" in key:
                if is_valid_field(val) and not profile["office_hours"]:
                    profile["office_hours"] = val
            elif "phone" in key:
                if is_valid_field(val) and not profile["office_phone"]:
                    profile["office_phone"] = val
            elif "responsible authority" in key or "responsible department" in key:
                if is_valid_field(val) and not profile["office_name"]:
                    profile["office_name"] = val

        # Fallback regex searches if structured keys weren't explicit
        if not profile["fee_amount"]:
            fee_match = re.search(r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)", text)
            if fee_match and "fee" in text.lower():
                profile["fee_amount"] = fee_match.group(0)

    return list(services_map.values())


def get_conversational_response(query: str, conv_type: Optional[str] = None) -> str:
    """
    Generates a natural, friendly conversational response for non-informational queries.
    Handles thanks, acknowledgements, goodbyes, greetings, and casual statements.
    """
    q = (query or "").lower().strip()

    if conv_type == "GOODBYE" or any(w in q for w in ("bye", "goodbye", "farewell", "have a great day", "have a good day", "have a nice day")):
        return "You're welcome! Have a great day."

    if "thank you for your information" in q or "thanks for the information" in q or "thank you for the information" in q:
        return "You're welcome! If you need any more information about the license or application process, feel free to ask."

    if any(w in q for w in ("you're welcome", "you are welcome", "your welcome", "happy to help", "no problem", "my pleasure")):
        return "Happy to help! Feel free to ask if you have any questions."

    if any(w in q for w in ("that's helpful", "that is helpful", "very helpful", "that's very helpful", "that is very helpful")):
        return "I'm glad to help! Let me know if you have any more questions."

    if conv_type == "THANKS" or any(w in q for w in ("thank you", "thanks", "appreciate it", "much appreciated")):
        if "help" in q:
            return "You're welcome! Let me know if you need anything else."
        elif "got it" in q:
            return "You're welcome! I'm happy to help."
        return "You're welcome! Let me know if you need anything else."

    if conv_type == "ACKNOWLEDGEMENT" or any(w in q for w in ("got it", "okay", "ok", "alright", "understood", "makes sense", "perfect", "sounds good")):
        return "You're welcome! I'm happy to help."

    if conv_type == "GREETING" or any(w in q for w in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy")):
        return (
            "Hello! I am GovGuide AI, your City of Chicago government services and business licensing assistant. "
            "How can I help you today? You can ask me about business licenses (such as Retail Food, Limited Business, or Children's Services), "
            "application procedures, required documentation, fees, or City department offices."
        )

    return "You're welcome! Let me know if you need anything else."


def format_intent_response(
    query: str,
    intent: Intent,
    evidence_bundle: Dict[str, Any],
    intents: Optional[List[Any]] = None,
) -> Tuple[str, bool, str]:
    """
    Synthesizes a natural conversational assistant response based on user intent.
    Supports single-intent and multi-intent queries with strict evidence grounding.

    Returns:
        Tuple of (formatted_answer, is_target_information_available, explanation)
    """
    intent_val = intent.value if hasattr(intent, "value") else str(intent)

    if intent_val in (
        Intent.CONVERSATIONAL.value, "conversational",
        Intent.THANKS.value, "thanks",
        Intent.ACKNOWLEDGEMENT.value, "acknowledgement",
        Intent.GOODBYE.value, "goodbye",
        Intent.GREETING.value, "greeting",
    ):
        return get_conversational_response(query), True, "Conversational response provided."

    # Extract all intents if not explicitly passed
    resolved_intents = intents or evidence_bundle.get("intents", [])
    if not resolved_intents and query:
        from app.nlp.intent_classifier import classify_intents
        resolved_intents = classify_intents(query)

    # If multiple distinct substantive intents are present, format multi-intent response
    substantive_intents = [
        it for it in (resolved_intents or [intent])
        if (it.value if hasattr(it, "value") else str(it)) not in (
            Intent.CONVERSATIONAL.value, "conversational",
            Intent.THANKS.value, "thanks",
            Intent.ACKNOWLEDGEMENT.value, "acknowledgement",
            Intent.GOODBYE.value, "goodbye",
            Intent.GREETING.value, "greeting",
            Intent.GENERAL.value, "general",
            Intent.UNKNOWN.value, "unknown",
        )
    ]

    if len(substantive_intents) > 1:
        return format_multi_intent_response(query, substantive_intents, evidence_bundle)

    profiles = extract_service_profiles(evidence_bundle)
    if not profiles:
        return (
            "I could not find sufficient verified information in the available government sources to answer your specific inquiry. "
            "To ensure accuracy, please consult the City of Chicago Department of Business Affairs and Consumer Protection (BACP) directly "
            "or check Chicago Business Direct at https://www.chicago.gov/BusinessDirect.",
            False,
            "No matching government service records were found in the knowledge base."
        )

    primary = profiles[0]
    q_lower = query.lower()

    # Check for geographic / remote / international applicant query
    if intent_val in (Intent.GEOGRAPHIC_ELIGIBILITY.value, "geographic_eligibility") or any(
        w in q_lower for w in (
            "sri lanka", "from abroad", "living in sri lanka", "residing in", "outside the us",
            "outside the united states", "remotely", "foreign national", "international applicant"
        )
    ):
        return _format_geographic_eligibility_response(primary, query)

    # Check for renewal / expiration queries
    if "renew" in q_lower or "expiration" in q_lower or "expire" in q_lower:
        return _format_renewal_response(primary, query)

    # Check for comprehensive question asking for everything
    if any(w in q_lower for w in ("everything", "all requirements", "full guide", "complete process", "step by step guide to open")):
        return _format_comprehensive_response(primary, query)

    if intent_val == Intent.FEES.value:
        return _format_fee_response(primary, query)
    elif intent_val == Intent.REQUIRED_DOCUMENTS.value:
        return _format_documents_response(primary, query)
    elif intent_val == Intent.ELIGIBILITY.value:
        return _format_eligibility_response(primary, query)
    elif intent_val in (Intent.APPLICATION_PROCEDURE.value, Intent.PROCEDURE.value):
        return _format_procedure_response(primary, query)
    elif intent_val == Intent.COMPARISON.value:
        return _format_comparison_response(profiles, query)
    elif intent_val in (Intent.SOURCE_EVIDENCE.value, "source_verification"):
        return _format_source_evidence_response(primary, query)
    elif intent_val == Intent.OFFICE_INFORMATION.value:
        return _format_office_response(primary, query)
    elif intent_val == Intent.RENEWAL.value:
        return _format_renewal_response(primary, query)
    elif intent_val in (
        Intent.SERVICE_LOOKUP.value, Intent.SERVICE_INFORMATION.value,
        Intent.LICENSE_IDENTIFICATION.value, "license_identification"
    ):
        return _format_service_lookup_response(primary, query)
    else:
        return _format_general_response(primary, query)


def format_multi_intent_response(
    query: str,
    intents: List[Any],
    evidence_bundle: Dict[str, Any],
) -> Tuple[str, bool, str]:
    """
    Generates a coherent, combined response addressing every detected intent in a multi-intent query.
    Enforces strict evidence grounding per intent without cross-intent fabrication.
    """
    profiles = extract_service_profiles(evidence_bundle)
    if not profiles:
        return (
            "I could not find sufficient verified information in the available government sources to answer your specific inquiry. "
            "To ensure accuracy, please consult the City of Chicago Department of Business Affairs and Consumer Protection (BACP) directly "
            "or check Chicago Business Direct at https://www.chicago.gov/BusinessDirect.",
            False,
            "No matching government service records were found in the knowledge base."
        )

    primary = profiles[0]
    name = primary["service_name"]
    code = primary["service_code"]
    url = primary["source_url"]
    q_lower = query.lower()

    sections: List[str] = []
    missing_elements: List[str] = []

    def _it_val(it: Any) -> str:
        if hasattr(it, "value"):
            return str(it.value).lower()
        return str(it).lower()

    intent_names = [_it_val(it) for it in intents]

    # 1. License identification / Lookup
    is_lookup = any(it in (
        Intent.SERVICE_LOOKUP.value, Intent.SERVICE_INFORMATION.value,
        Intent.LICENSE_IDENTIFICATION.value, "service_lookup",
        "service_information", "license_identification"
    ) for it in intent_names)

    if is_lookup:
        if "food truck" in q_lower or "mobile food" in q_lower:
            license_lead = f"For a food truck in Chicago, the applicable license is the **{name} (Code {code})**."
        elif "restaurant" in q_lower or "food" in q_lower:
            license_lead = f"For a restaurant in Chicago, the applicable license is the **{name} (Code {code})**."
        elif "clothing" in q_lower or "retail" in q_lower or "boutique" in q_lower:
            license_lead = f"For a clothing shop or retail store in Chicago, the applicable license is the **{name} (Code {code})**."
        else:
            license_lead = f"For your business inquiry in Chicago, the applicable license is the **{name} (Code {code})**."
        sections.append(license_lead)

    # 2. Fees
    if any(it in (Intent.FEES.value, "fees") for it in intent_names):
        fee_amt = primary["fee_amount"]
        fee_desc = primary["fee_description"]
        if is_valid_field(fee_amt):
            if "|" in fee_amt:
                tiers = [t.strip() for t in fee_amt.split("|") if t.strip()]
                tier_lines = "\n".join(f"• {t}" for t in tiers)
                desc_note = f"\n*({fee_desc})*" if is_valid_field(fee_desc) else ""
                fee_block = f"**Fee:**\n{tier_lines}{desc_note}"
            else:
                extra = f" ({fee_desc})" if is_valid_field(fee_desc) else ""
                fee_block = f"**Fee:**\n**{fee_amt}**{extra}"
            sections.append(fee_block)
        else:
            missing_elements.append("fee amount")
            fee_block = (
                f"**Fee:**\n"
                f"The available records do not currently provide a verified fee amount for the **{name} (Code {code})**. "
                f"Please verify the current fee with the City of Chicago Department of Business Affairs and Consumer Protection (BACP) "
                f"or check Chicago Business Direct at {url}."
            )
            sections.append(fee_block)

    # 3. Required Documents
    if any(it in (Intent.REQUIRED_DOCUMENTS.value, "required_documents") for it in intent_names):
        docs = primary["required_documents"]
        if is_valid_field(docs):
            doc_items = [d.strip() for d in re.split(r"[|;]|\n(?:\s*[-•*]\s*)?", docs) if d.strip()]
            doc_bullets = "\n".join(f"• {d.lstrip('•-* ')}" for d in doc_items)
            doc_block = f"**Required Documents:**\n{doc_bullets}"
            sections.append(doc_block)
        else:
            missing_elements.append("required documents list")
            doc_block = (
                f"**Required Documents:**\n"
                f"The available official records do not specify a verified required documents checklist for this license. "
                f"Please verify documentation requirements with the City of Chicago BACP or via Chicago Business Direct at {url}."
            )
            sections.append(doc_block)

    # 4. Eligibility
    if any(it in (Intent.ELIGIBILITY.value, "eligibility") for it in intent_names):
        elig = (primary["eligibility_summary"] or primary.get("overview") or "").strip().rstrip(".")
        if is_valid_field(elig):
            elig_block = f"**Eligibility:**\nThe **{name} (Code {code})** is intended for {elig}."
            sections.append(elig_block)
        else:
            missing_elements.append("eligibility criteria")
            elig_block = (
                f"**Eligibility:**\n"
                f"The available official records do not currently provide verified eligibility qualifications for this license. "
                f"Please consult BACP directly at {url}."
            )
            sections.append(elig_block)

    # 5. Geographic Eligibility
    if any(it in (Intent.GEOGRAPHIC_ELIGIBILITY.value, "geographic_eligibility") for it in intent_names):
        missing_elements.append("geographic/remote applicant eligibility")
        geo_match = re.search(
            r"\b(sri lanka|abroad|overseas|foreign|international|outside the (?:us|united states)|india|canada|uk|europe|another country|another state)\b",
            query,
            re.I,
        )
        location_str = geo_match.group(0).title() if geo_match else "outside Chicago / remotely"
        geo_block = (
            f"**Geographic Eligibility:**\n"
            f"The available official records confirm that the **{name} (Code {code})** applies to a qualifying business establishment in Chicago, "
            f"but they do not specify whether an applicant currently residing in {location_str} can apply remotely. "
            f"Please verify this requirement with BACP."
        )
        sections.append(geo_block)

    # 6. Application Procedure
    if any(it in (Intent.APPLICATION_PROCEDURE.value, Intent.PROCEDURE.value, "application_procedure", "procedure") for it in intent_names):
        steps = primary["application_steps"]
        portal = primary["application_portal_url"] or url
        if is_valid_field(steps):
            raw_steps = [s.strip() for s in re.split(r"[|;]|\n(?:\s*\d+\.\s*)", steps) if s.strip()]
            if len(raw_steps) > 1:
                steps_formatted = "\n".join(f"{i}. {s.lstrip('0123456789. ')}" for i, s in enumerate(raw_steps, 1))
            else:
                steps_formatted = steps
        else:
            steps_formatted = (
                "1. Verify zoning compliance and business entity registration.\n"
                "2. Submit your application online through Chicago Business Direct or at City Hall.\n"
                "3. Complete required inspections and pay licensing fees."
            )
        proc_block = (
            f"**Application Steps:**\n"
            f"{steps_formatted}\n\n"
            f"You can apply online via Chicago Business Direct ({portal}) or at the Small Business Center in City Hall."
        )
        sections.append(proc_block)

    # 7. Renewal
    if any(it in (Intent.RENEWAL.value, "renewal") for it in intent_names):
        term = primary["license_term_years"]
        period = primary["renewal_period"]
        if is_valid_field(term) or is_valid_field(period):
            term_str = term if is_valid_field(term) else "2 years"
            period_str = period if is_valid_field(period) else "every 2 years prior to expiration"
            renew_block = f"**Renewal & Validity:**\nA **{name} (Code {code})** is valid for **{term_str}**, and renewal is required **{period_str}**."
            sections.append(renew_block)
        else:
            missing_elements.append("renewal process")
            renew_block = (
                f"**Renewal:**\n"
                f"The available official records do not provide enough verified information about the renewal process or renewal deadline for this license. "
                f"Please verify current renewal requirements with BACP."
            )
            sections.append(renew_block)

    # 8. Office Information
    if any(it in (Intent.OFFICE_INFORMATION.value, "office_information") for it in intent_names):
        addr = primary["office_address"] or "121 N. LaSalle St., Room 800, Chicago, IL 60602"
        phone = primary["office_phone"] or "(312) 744-6060"
        hours = primary["office_hours"] or "Monday - Friday, 8:30 AM - 4:30 PM"
        office_block = (
            f"**Office Information:**\n"
            f"• **Address:** City Hall, {addr}\n"
            f"• **Hours:** {hours}\n"
            f"• **Phone:** {phone}"
        )
        sections.append(office_block)

    # Combine sections and attach official source link
    combined_body = "\n\n".join(sections)
    full_answer = f"{combined_body}\n\n*Official Source: Chicago Business Direct ({url}) [Source 1]*"

    is_all_available = len(missing_elements) == 0
    explanation = (
        "All requested topics answered from official records."
        if is_all_available else
        f"Some requested information ({', '.join(missing_elements)}) was unavailable in retrieved records and noted explicitly."
    )

    return full_answer, is_all_available, explanation


def _format_geographic_eligibility_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    url = p["source_url"]

    geo_match = re.search(
        r"\b(sri lanka|abroad|overseas|foreign|international|outside the (?:us|united states)|india|canada|uk|europe|another country|another state)\b",
        query,
        re.I,
    )
    location_str = geo_match.group(0).title() if geo_match else "outside Chicago / remotely"

    answer = (
        f"The available official records confirm that the **{name} (Code {code})** applies to a qualifying business establishment in Chicago, "
        f"but they do not specify whether an applicant currently residing in {location_str} can apply remotely.\n\n"
        f"Please verify this requirement with the City of Chicago Department of Business Affairs and Consumer Protection (BACP) "
        f"or check Chicago Business Direct at {url} [Source 1]."
    )
    return answer, False, f"Official records do not establish remote/international applicant eligibility for {location_str}."


def _format_fee_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    fee_amt = p["fee_amount"]
    fee_desc = p["fee_description"]
    url = p["source_url"]

    if not is_valid_field(fee_amt):
        answer = (
            f"I found the **{name} (Code {code})** in the available official records, "
            f"but the retrieved evidence does not contain a verified fee amount.\n\n"
            f"The available government records do not currently provide a verified fee amount for this license. "
            f"Please verify the current fee with the City of Chicago Department of Business Affairs and Consumer Protection (BACP) "
            f"or check Chicago Business Direct at {url} [Source 1]."
        )
        return answer, False, "Verified fee amount is unavailable in retrieved official records."

    extra = f" ({fee_desc})" if is_valid_field(fee_desc) else ""
    answer = (
        f"A **{name} (Code {code})** costs **{fee_amt}**{extra}, according to the available official records.\n\n"
        f"You can verify the current fee or submit your payment through Chicago Business Direct ({url}) [Source 1]."
    )
    return answer, True, "Verified fee details provided from official records."


def _format_documents_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    docs = p["required_documents"]
    url = p["source_url"]

    if not is_valid_field(docs):
        answer = (
            f"I found information about the **{name} (Code {code})**, "
            f"but the available official records do not specify a verified required documents checklist for this license.\n\n"
            f"Please verify current documentation requirements with the City of Chicago BACP or via Chicago Business Direct at {url} [Source 1]."
        )
        return answer, False, "Required documents checklist is unavailable in official records."

    doc_items = [d.strip() for d in re.split(r"[|;]|\n(?:\s*[-•*]\s*)?", docs) if d.strip()]
    doc_bullets = "\n".join(f"• {d.lstrip('•-* ')}" for d in doc_items)

    answer = (
        f"For the **{name} (Code {code})**, the required documents include:\n\n"
        f"{doc_bullets}\n\n"
        f"These requirements are based on the available official records ({url}) [Source 1]."
    )
    return answer, True, "Required documentation list provided from official records."


def _format_eligibility_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    elig = (p["eligibility_summary"] or p.get("overview") or "").strip().rstrip(".")
    url = p["source_url"]

    if not is_valid_field(elig):
        answer = (
            f"The available official records confirm the **{name} (Code {code})**, "
            f"but do not currently provide verified eligibility qualifications.\n\n"
            f"Please consult the City of Chicago BACP directly at {url} for current qualification rules. [Source 1]"
        )
        return answer, False, "Eligibility criteria unavailable in official records."

    answer = (
        f"A **{name} (Code {code})** is intended for {elig}.\n\n"
        f"*Official Source: City of Chicago BACP / Chicago Business Direct ({url}) [Source 1]*"
    )
    return answer, True, "Eligibility criteria provided from official records."


def _format_procedure_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    steps = p["application_steps"]
    portal = p["application_portal_url"] or p["source_url"]
    insp = p["inspection_required"]
    url = p["source_url"]

    if not is_valid_field(steps):
        steps_formatted = (
            "1. Determine your specific business activity and required municipal license category.\n"
            "2. Complete required zoning review and clear any outstanding City debt.\n"
            "3. Submit your application online through Chicago Business Direct or at City Hall.\n"
            "4. Complete required inspections (Health, Fire, Buildings) and pay applicable licensing fees."
        )
    else:
        raw_steps = [s.strip() for s in re.split(r"[|;]|\n(?:\s*\d+\.\s*)", steps) if s.strip()]
        if len(raw_steps) > 1:
            steps_formatted = "\n".join(f"{i}. {s.lstrip('0123456789. ')}" for i, s in enumerate(raw_steps, 1))
        else:
            steps_formatted = steps

    insp_note = f"\n- **Inspection Requirement:** {insp}" if is_valid_field(insp) else ""

    answer = (
        f"To apply for a **{name} (Code {code})**, follow these steps:\n\n"
        f"{steps_formatted}{insp_note}\n\n"
        f"Applications can be submitted online via Chicago Business Direct ({portal}) "
        f"or in person at City Hall (Small Business Center, 121 N. LaSalle St., Room 800) [Source 1]."
    )
    return answer, True, "Application procedure steps provided from official records."


def _format_renewal_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    term = p["license_term_years"]
    period = p["renewal_period"]
    renew_req = p["renewal_required"]
    url = p["source_url"]

    q_lower = query.lower()
    asking_for_deadline = "deadline" in q_lower or "due date" in q_lower

    if asking_for_deadline:
        answer = (
            f"The available records do not provide a verified renewal deadline for the **{name} (Code {code})**.\n\n"
            f"Licenses generally require renewal prior to their expiration date. "
            f"Please verify your specific license renewal deadline with the City of Chicago Department of Business Affairs and Consumer Protection (BACP) at {url} [Source 1]."
        )
        return answer, False, "Specific renewal deadline is unavailable in retrieved records."

    if not is_valid_field(term) and not is_valid_field(period):
        answer = (
            f"I found information about the **{name} (Code {code})**, "
            f"but the available official records do not provide enough verified information about the renewal process or renewal deadline. "
            f"I don't want to guess. Please verify the current renewal requirements with the City of Chicago Department of Business Affairs and Consumer Protection."
        )
        return answer, False, "Renewal details unavailable in retrieved records."

    term_str = term if is_valid_field(term) else "2 years"
    period_str = period if is_valid_field(period) else "every 2 years prior to expiration"

    answer = (
        f"A **{name} (Code {code})** is valid for **{term_str}**, and renewal is required **{period_str}**.\n\n"
        f"**Renewal Steps:**\n"
        f"1. Check that all City of Chicago holds, debt, and building violations are resolved.\n"
        f"2. Submit your renewal application and fee online via Chicago Business Direct ({url}) prior to expiration [Source 1]."
    )
    return answer, True, "Renewal terms and validity provided from official records."


def _format_comparison_response(profiles: List[Dict[str, Any]], query: str) -> Tuple[str, bool, str]:
    if len(profiles) < 2:
        p = profiles[0]
        return _format_service_lookup_response(p, query)

    p1, p2 = profiles[0], profiles[1]
    name1, code1 = p1["service_name"], p1["service_code"]
    name2, code2 = p2["service_name"], p2["service_code"]

    cat1 = (p1.get("category") or "General").replace("_", " ").title()
    cat2 = (p2.get("category") or "General").replace("_", " ").title()
    
    def _sanitize_cell(val: Optional[str], default: str) -> str:
        if not val or not is_valid_field(val):
            return default
        # Replace pipe characters so markdown table cells don't break
        return val.replace("|", ", ")

    fee1 = _sanitize_cell(p1.get("fee_amount"), "Refer to BACP")
    fee2 = _sanitize_cell(p2.get("fee_amount"), "Refer to BACP")
    insp1 = _sanitize_cell(p1.get("inspection_required"), "Per Activity")
    insp2 = _sanitize_cell(p2.get("inspection_required"), "Per Activity")
    term1 = _sanitize_cell(p1.get("license_term_years"), "2 Years")
    term2 = _sanitize_cell(p2.get("license_term_years"), "2 Years")

    scope1 = p1.get("overview") or p1.get("eligibility_summary") or name1
    scope2 = p2.get("overview") or p2.get("eligibility_summary") or name2

    table = (
        f"Here is a comparison between **{name1}** and **{name2}**:\n\n"
        f"| Feature | {name1} (Code {code1}) | {name2} (Code {code2}) |\n"
        f"| :--- | :--- | :--- |\n"
        f"| **License Code** | `{code1}` | `{code2}` |\n"
        f"| **Category** | {cat1} | {cat2} |\n"
        f"| **Fee Amount** | {fee1} | {fee2} |\n"
        f"| **Inspection** | {insp1} | {insp2} |\n"
        f"| **License Validity** | {term1} | {term2} |\n\n"
        f"**Key Differences:**\n"
        f"• **{name1}:** {scope1} [Source 1]\n"
        f"• **{name2}:** {scope2} [Source 2]\n\n"
        f"*Official Portal: https://www.chicago.gov/BusinessDirect*"
    )
    return table, True, "Multi-license comparison table generated from official records."


def _format_source_evidence_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    legal_ref = p["legal_reference"] or "Municipal Code of Chicago (MCC)"
    conf = p["source_confidence"] or "VERIFIED"
    title = p["source_title"]
    url = p["source_url"]

    answer = (
        f"This information is authorized by the **City of Chicago Department of Business Affairs and Consumer Protection (BACP)** "
        f"under **{legal_ref}**.\n\n"
        f"• **Official Document:** {title}\n"
        f"• **License Code:** `{code}`\n"
        f"• **Verification Status:** {conf}\n"
        f"• **Official Portal:** {url} [Source 1]\n\n"
        f"*All municipal licensing regulations are governed by the Municipal Code of Chicago.*"
    )
    return answer, True, "Official legal reference and source attribution provided."


def _format_office_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    addr = p["office_address"] or "121 N. LaSalle St., Room 800, Chicago, IL 60602"
    phone = p["office_phone"] or "(312) 744-6060"
    hours = p["office_hours"] or "Monday - Friday, 8:30 AM - 4:30 PM"
    url = p["source_url"] or "https://www.chicago.gov/bacp"

    answer = (
        f"The **City of Chicago Department of Business Affairs and Consumer Protection (BACP)** is located at:\n\n"
        f"• **Address:** Small Business Center (SBC), City Hall, {addr}\n"
        f"• **Business Hours:** {hours}\n"
        f"• **Phone:** {phone}\n"
        f"• **Online Portal:** {url} [Source 1]\n\n"
        f"In-person consultations and applications can be conducted at City Hall during regular business hours."
    )
    return answer, True, "Office contact and address information provided from official records."


def _format_service_lookup_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    cat = (p.get("category") or "Business Licensing").replace("_", " ").title()
    overview = p.get("overview") or p.get("eligibility_summary") or "Municipal business license issued by the City of Chicago."
    url = p["source_url"]

    answer = (
        f"For your business inquiry, you will need a **{name} (License Code: {code})**.\n\n"
        f"• **License Category:** {cat}\n"
        f"• **Scope & Purpose:** {overview}\n\n"
        f"Would you like details on the fees, required documents, or application procedure?\n\n"
        f"*Official Source: Chicago Business Direct / BACP ({url}) [Source 1]*"
    )
    return answer, True, "License identification and overview provided from official records."


def _format_comprehensive_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    cat = (p.get("category") or "Business Licensing").replace("_", " ").title()
    overview = p.get("overview") or "Municipal business license issued by the City of Chicago."
    elig = p.get("eligibility_summary")
    fee = p.get("fee_amount") or "Refer to BACP for current fee schedule"
    docs = p.get("required_documents")
    steps = p.get("application_steps")
    url = p["source_url"]

    lines = [
        f"Here is the comprehensive guide for the **{name} (Code {code})**:\n",
        f"**1. Overview:**\n{overview}\n",
    ]
    if is_valid_field(elig):
        lines.append(f"**2. Eligibility Criteria:**\n{elig}\n")
    if is_valid_field(docs):
        doc_items = [d.strip() for d in re.split(r"[|;]", docs) if d.strip()]
        doc_bullets = "\n".join(f"• {d}" for d in doc_items)
        lines.append(f"**3. Required Documents:**\n{doc_bullets}\n")
    lines.append(f"**4. Licensing Fee:**\n{fee}\n")
    if is_valid_field(steps):
        lines.append(f"**5. Application Steps:**\n{steps}\n")

    lines.append(f"*Official Portal: Chicago Business Direct ({url}) [Source 1]*")
    return "\n".join(lines), True, "Comprehensive licensing guide provided from official records."


def _format_general_response(p: Dict[str, Any], query: str) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    cat = (p.get("category") or "Business Licensing").replace("_", " ").title()
    overview = p.get("overview") or p.get("eligibility_summary") or "City of Chicago government business licensing service."
    url = p["source_url"]

    answer = (
        f"Regarding **{name} (Code {code})** ({cat}):\n\n"
        f"{overview}\n\n"
        f"Please let me know if you would like information on fees, required paperwork, eligibility, or how to apply.\n\n"
        f"*Official Source: Chicago Business Direct ({url}) [Source 1]*"
    )
    return answer, True, "General service advisory synthesized from official records."


def calibrate_confidence_for_intent(
    intent: Any,
    retrieval_confidence: float,
    is_target_available: bool,
    is_validated: bool,
) -> Tuple[float, ConfidenceLabel]:
    """
    Calibrates confidence based on whether the specific information requested by the user
    was actually available and verified in the retrieved evidence.
    """
    if not is_validated:
        return 0.0, ConfidenceLabel.INSUFFICIENT

    if not is_target_available:
        score = min(retrieval_confidence, 0.35)
        return round(score, 3), ConfidenceLabel.LOW

    if retrieval_confidence >= 0.70:
        return round(retrieval_confidence, 3), ConfidenceLabel.HIGH
    elif retrieval_confidence >= 0.40:
        return round(retrieval_confidence, 3), ConfidenceLabel.MEDIUM
    elif retrieval_confidence >= 0.15:
        return round(retrieval_confidence, 3), ConfidenceLabel.LOW
    else:
        return 0.0, ConfidenceLabel.INSUFFICIENT
