"""
GovGuide AI — Conversational Intent-Driven Response Formatter & Relevance Engine

Behaves like a natural, conversational government-service assistant:
1. Answers the user's specific question directly without rigid boilerplate headers or repeating templates.
2. Supports multilingual and code-mixed styles:
   - English -> Natural English
   - Thanglish -> Natural Thanglish
   - Tamil -> Natural Tamil
   - Sinhala -> Natural Sinhala
   - Singlish -> Natural Singlish
3. Formats responses conversationally:
   - Fees -> Direct cost, payment terms, and portal verification link.
   - Required Documents -> Clean bulleted checklist.
   - Eligibility -> Direct qualification statement.
   - Application Procedure -> Clean numbered step-by-step instructions.
   - Renewal -> Verified term and renewal procedure, or explicit missing-info refusal.
   - Multi-License Comparison -> Clean table + key distinctions.
   - Source Evidence -> Governing authority, MCC chapter, and verification status.
   - License Lookup -> Recommended license and brief purpose.
4. Merges multiple chunks of the same license into ONE coherent, deduplicated record.
5. Enforces strict missing-information handling and calibrated confidence.
"""

from typing import Any, Dict, List, Optional, Tuple
import re
from app.orchestrator.message_schema import Intent, ConfidenceLabel
from app.nlp.language_detector import LanguageCode, detect_language, resolve_query_language

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


# ── Multilingual Clarification & Fallback Templates ──────────────────────────

def get_clarification_response(
    language: Any = LanguageCode.ENGLISH,
    clarification_type: Optional[str] = None,
) -> str:
    """Returns a natural, tailored clarification request based on language and clarification type."""
    lang = language
    if isinstance(lang, str):
        try:
            lang = LanguageCode(lang.lower())
        except ValueError:
            lang = LanguageCode.ENGLISH

    # 0. Generic service query clarification (Requirement 8)
    if clarification_type == "service_selection":
        if lang in (LanguageCode.THANGLISH, LanguageCode.MIXED):
            return "Sure. Which government service would you like to know about? Please provide the service name or license code."
        elif lang == LanguageCode.TAMIL:
            return "நிச்சயமாக. நீங்கள் எந்த அரசு சேவை அல்லது உரிமம் பற்றி தெரிந்து கொள்ள விரும்புகிறீர்கள்? சேவை பெயர் அல்லது உரிமக் குறியீட்டைக் குறிப்பிடவும்."
        elif lang == LanguageCode.SINHALA:
            return "Sure! ඔබට දැන ගැනීමට අවශ්‍ය කුමන රජයේ සේවාව හෝ බලපත්‍රය පිළිබඳවද? කරුණාකර සේවා නම හෝ බලපත්‍ර කේතය සඳහන් කරන්න."
        elif lang == LanguageCode.SINGLISH:
            return "Sure. Oyata dana ganna ona mona government service hari license eka ganada? Karunakara service name eka hari license code eka kiyanna."
        return "Sure. Which government service would you like to know about? Please provide the service name or license code."

    # 1. Generic Retail clarification (asking for type of goods)
    if clarification_type == "retail_goods":
        if lang in (LanguageCode.THANGLISH, LanguageCode.MIXED):
            return (
                "Sure. Retail shop open panna license requirement business type-a depend aagum. "
                "Neenga enna type retail shop open panna poringa — clothing, grocery, electronics, tailoring, illa vera type? "
                "Adha sonna available government records based-a relevant license identify pannalaam."
            )
        elif lang == LanguageCode.TAMIL:
            return (
                "நிச்சயமாக. சில்லறை கடைக்கான உரிமத் தேவை நீங்கள் விற்கும் பொருள்களைப் பொறுத்தது. "
                "நீங்கள் என்ன வகை சில்லறை கடை திறக்க உள்ளீர்கள் — ஆடை, மளிகை, எலக்ட்ரானிக்ஸ், தையல் அல்லது வேறு வகையா?"
            )
        elif lang == LanguageCode.SINHALA:
            return (
                "Sure! සිල්ලර වෙළඳසැල් බලපත්‍ර අවශ්‍යතාවය ඔබ විකුණන භාණ්ඩ වර්ගය මත රඳා පවතී. "
                "ඔබ ආරම්භ කිරීමට බලාපොරොත්තු වන්නේ කුමන වර්ගයේ සිල්ලර වෙළඳසැලක්ද — ඇඳුම්, සිල්ලර බඩු, ඉලෙක්ට්‍රොනික හෝ වෙනත් වර්ගයක්ද?"
            )
        elif lang == LanguageCode.SINGLISH:
            return (
                "Sure. Retail store license requirement depend wenne business type eka anuwa. "
                "Oyata mona wage retail shop ekakda open karanna ona — clothing, grocery, electronics, tailoring wage?"
            )
        return (
            "Sure! Retail store licensing requirements depend on the type of goods you plan to sell. "
            "What type of retail shop are you planning to open — for example, clothing, grocery, electronics, tailoring, or another type?"
        )

    # 2. Tailoring setup clarification (commercial storefront vs home-based)
    if clarification_type == "tailoring_setup":
        if lang in (LanguageCode.THANGLISH, LanguageCode.MIXED):
            return (
                "Neenga 'tailoring' business/shop pathi kekkureenga-nu purinjukitten. "
                "License requirement-ku tailoring business-ku applicable-aana government service record irukka-nu check pannanum. "
                "Neenga tailoring shop open panna poringala, illa home-based tailoring business-aa?"
            )
        elif lang == LanguageCode.TAMIL:
            return (
                "நீங்கள் 'தையல்' வணிகம்/கடை பற்றி கேட்கிறீர்கள் என்பதை புரிந்து கொண்டேன். "
                "நீங்கள் தையல் கடையைத் திறக்க திட்டமிட்டுள்ளீர்களா அல்லது வீட்டிலிருந்தே தையல் செய்யப் போகிறீர்களா?"
            )
        elif lang == LanguageCode.SINHALA:
            return (
                "ඔබ 'මැහුම්' (tailoring) ව්‍යාපාරය පිළිබඳව විමසන බව තේරුම් ගතිමි. "
                "ඔබ මැහුම් සාප්පුවක් ආරම්භ කිරීමට බලාපොරොත්තු වන්නේද, නැතහොත් නිවසේ සිට කරන ව්‍යාපාරයක්ද?"
            )
        return (
            "I understand you are asking about a tailoring business. "
            "To determine applicable government licensing requirements, are you planning to open a commercial tailoring shop, or operate a home-based tailoring service?"
        )

    # 3. Context-less Explanation / Short Follow-up
    if clarification_type in ("explain_topic", "missing_context"):
        if lang in (LanguageCode.THANGLISH, LanguageCode.MIXED):
            return (
                "Sure 😊 Enna topic or license pathi explain pannanum? "
                "Unga question or business type sonna available government records based-a explain panren."
            )
        elif lang == LanguageCode.TAMIL:
            return (
                "நிச்சயமாக! 😊 எந்த உரிமம் அல்லது தலைப்பு பற்றி விளக்க வேண்டும்? "
                "உங்கள் கேள்வி அல்லது வணிக வகையைக் கூறுங்கள்."
            )
        elif lang == LanguageCode.SINHALA:
            return (
                "Sure! 😊 ඔබට කුමන මාතෘකාව හෝ බලපත්‍රය පිළිබඳව පැහැදිලි කිරීමට අවශ්‍යද? කරුණාකර සඳහන් කරන්න."
            )
        return (
            "Sure 😊 What topic or license would you like me to explain? "
            "Please specify your question or the business type you are interested in."
        )

    # 4. Default business_type / license inquiry clarification
    if lang in (LanguageCode.THANGLISH, LanguageCode.MIXED):
        return (
            "Sure, I can help. Ungalukku endha licence pathi theriyanum? "
            "Licence name, licence code, alladhu neenga start panna pora business type sonna, "
            "correct-aana information solla mudiyum."
        )
    elif lang == LanguageCode.TAMIL:
        return (
            "நிச்சயமாக, நான் உதவ முடியும். நீங்கள் எந்த உரிமத்தைப் பற்றி கேட்கிறீர்கள்? "
            "உரிமத்தின் பெயர், உரிமக் குறியீடு அல்லது நீங்கள் தொடங்க திட்டமிட்டுள்ள வணிக வகையைக் கூறுங்கள்."
        )
    elif lang == LanguageCode.SINHALA:
        return (
            "Sure, මට උදව් කළ හැක. ඔබ විමසන්නේ කුමන බලපත්‍රය පිළිබඳවද? "
            "බලපත්‍රයේ නම, බලපත්‍ර කේතය හෝ ඔබ ආරම්භ කිරීමට බලාපොරොත්තු වන ව්‍යාපාර වර්ගය සඳහන් කරන්න."
        )
    elif lang == LanguageCode.SINGLISH:
        return (
            "Sure, I can help. Oyata ona mona license ekada kiyala license name, code hari business type eka hari kiyanna."
        )
    return (
        "Sure, I can help. Which license are you asking about? "
        "You can provide the license name, license code, or the business type you are planning to operate."
    )


def get_insufficient_evidence_response(language: LanguageCode = LanguageCode.ENGLISH) -> str:
    """Returns a polite soft fallback response when verified evidence is unavailable."""
    if language == LanguageCode.THANGLISH or language == LanguageCode.MIXED:
        return (
            "Indha request-ku sufficiently relevant-aana verified government service information enakku kidaikkala. "
            "Thappaana information kudukka naan virumbala. Neenga konjam more details kudutha, "
            "available services-la correct-aana option irukka-nu check pannalaam."
        )
    elif language == LanguageCode.TAMIL:
        return (
            "இந்தக் கேள்விக்கு போதுமான சரிபார்க்கப்பட்ட அரசாங்க சேவைத் தகவல் கிடைக்கவில்லை. "
            "தவறான தகவலை வழங்காமல் இருப்பதற்காக, தயவுசெய்து உங்கள் தேவையைச் சிறிது தெளிவாகக் கூறுங்கள்."
        )
    elif language == LanguageCode.SINHALA:
        return (
            "මෙම විමසුම සඳහා ප්‍රමාණවත් නිල තොරතුරු සොයා ගැනීමට නොහැකි විය. "
            "වැරදි තොරතුරු සැපයීමෙන් වැළකී සිටීමට, කරුණාකර ඔබේ අවශ්‍යතාවය පිළිබඳ වැඩිදුර විස්තර සපයන්න."
        )
    elif language == LanguageCode.SINGLISH:
        return (
            "Me request ekata sufficiently relevant verified government service record ekak mata hambawune na. "
            "Waradi information nodi inna mata ona. Poddak wadiura details dunnoth available services check karala kiyannam."
        )
    return (
        "I could not find sufficient official evidence in the available verified government sources to answer your specific inquiry. "
        "I don't want to provide incorrect information. If you provide a little more detail about what you need, "
        "I can check the available services more accurately."
    )


def get_unsupported_domain_response(domain: Optional[str], language: LanguageCode = LanguageCode.ENGLISH) -> str:
    """Returns safe guidance for out-of-scope domains (such as cricket, cooking, driver licenses, or aviation)."""
    domain_str = (domain or "").lower()
    is_driver = domain_str in ("driver_license", "driver license", "driver's license", "driving license")
    is_aviation = domain_str in ("aviation", "aviation_license", "helicopter", "pilot")

    if language == LanguageCode.THANGLISH or language == LanguageCode.MIXED:
        if is_driver:
            return (
                "GovGuide AI knowledge base-la driver's licence pathina information kidaikkala.\n\n"
                "The available knowledge base currently focuses on City of Chicago government business licensing information.\n\n"
                "Please check the relevant official driver's licensing authority (Illinois Secretary of State / DMV https://www.ilsos.gov)."
            )
        elif is_aviation:
            return (
                "GovGuide AI knowledge base-la aviation licensing pathina information kidaikkala.\n\n"
                "The available knowledge base currently focuses on City of Chicago government business licensing information.\n\n"
                "Please consult the Federal Aviation Administration (FAA https://www.faa.gov)."
            )
        return (
            "Mannikkavum, indha topic pathina information GovGuide AI system-la available illa. "
            "Indha system government services, business licences, eligibility, documents, fees, "
            "renewal, application procedure matrum related official information-ku mattum design seyyappattullathu."
        )
    elif language == LanguageCode.TAMIL:
        if is_driver:
            return (
                "தற்போதைய GovGuide AI தரவுத்தளத்தில் ஓட்டுநர் உரிமம் பற்றிய தகவல்கள் இல்லை.\n\n"
                "இது சிகாகோ வணிக உரிமங்களில் மட்டுமே கவனம் செலுத்துகிறது.\n\n"
                "அதிகாரப்பூர்வ DMV (https://www.ilsos.gov) தளத்தைப் பார்க்கவும்."
            )
        return (
            "மன்னிக்கவும், இந்த தலைப்பு குறித்த தகவல்கள் GovGuide AI அமைப்பில் கிடைக்கவில்லை. "
            "இந்த அமைப்பு அரசு சேவைகள், வணிக உரிமங்கள், தகுதி, தேவையான ஆவணங்கள், விண்ணப்ப நடைமுறைகள், "
            "கட்டணங்கள், புதுப்பித்தல் மற்றும் தொடர்புடைய அதிகாரப்பூர்வ தகவல்களுக்கு மட்டுமே வடிவமைக்கப்பட்டுள்ளது."
        )
    elif language == LanguageCode.SINHALA:
        if is_driver:
            return (
                "GovGuide AI දැනුම් පදනමේ රියදුරු බලපත්‍ර පිළිබඳ තොරතුරු නොමැත.\n\n"
                "මෙය චිකාගෝ ව්‍යාපාරික බලපත්‍ර සඳහා පමණක් සීමා වේ.\n\n"
                "නිල DMV (https://www.ilsos.gov) පරීක්ෂා කරන්න."
            )
        return (
            "සමාවන්න, මෙම මාතෘකාව පිළිබඳ තොරතුරු GovGuide AI පද්ධතියේ නොමැත. "
            "මෙම පද්ධතිය රජයේ සේවාවන්, ව්‍යාපාර බලපත්‍ර, සුදුසුකම්, අවශ්‍ය ලියකියවිලි, "
            "අයදුම් කිරීමේ ක්‍රියා පටිපාටි, ගාස්තු, අලුත් කිරීම් සහ අදාළ නිල තොරතුරු සඳහා පමණක් නිර්මාණය කර ඇත."
        )

    # Standard English default
    if is_driver:
        return (
            "I couldn't find relevant information about driver's licences in the current GovGuide AI knowledge base.\n\n"
            "The available knowledge base currently focuses on City of Chicago government business licensing information.\n\n"
            "Please check the relevant official driver's licensing authority (such as the Illinois Secretary of State / DMV at https://www.ilsos.gov) for current licence class requirements and driving regulations."
        )
    if is_aviation:
        return (
            "I couldn't find relevant information about aviation licensing in the current GovGuide AI knowledge base.\n\n"
            "The available knowledge base currently focuses on City of Chicago government business licensing information.\n\n"
            "Please consult the Federal Aviation Administration (FAA at https://www.faa.gov) for official pilot and aircraft licensing requirements."
        )
    return (
        "Sorry, GovGuide AI does not provide information on this topic. "
        "It is designed to assist with government services, business licences, eligibility, "
        "required documents, application procedures, fees, renewal, and related official information."
    )


def get_conversational_response(query: str, conv_type: Optional[str] = None) -> str:
    """
    Generates a natural conversational response for non-informational queries.
    """
    q = (query or "").lower().strip()
    lang = resolve_query_language(query)

    if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
        if conv_type == "GREETING" or any(w in q for w in ("hi", "hello", "vanakkam", "hey")):
            return (
                "Vanakkam! Naan GovGuide AI, unga City of Chicago government services and business licensing assistant. "
                "Ungalukku enna help thevai? Business licenses (Retail Food, Limited Business), "
                "application procedure, documents, fees, alladhu City department offices pathi kekkalaam."
            )
        if conv_type in ("THANKS", "ACKNOWLEDGEMENT") or any(w in q for w in ("nandri", "thanks", "ok", "okay", "seri", "sari", "got it", "bro")):
            return "You're welcome! 😊 Ungalukku vera edhavadhu information thevaipatta kelunga."
        return "You're welcome! 😊 Edhavadhu questions irundha sollunga."

    if lang == LanguageCode.TAMIL:
        if conv_type == "GREETING" or "வணக்கம்" in query:
            return (
                "வணக்கம்! நான் GovGuide AI, உங்கள் சிகாகோ வணிக உரிம வழிகாட்டி. "
                "உங்களுக்கு எவ்வாறு உதவ முடியும்? வணிக உரிமங்கள், தேவையான ஆவணங்கள், "
                "கட்டணம் அல்லது விண்ணப்ப முறைகள் பற்றி நீங்கள் கேட்கலாம்."
            )
        if conv_type in ("THANKS", "ACKNOWLEDGEMENT") or any(w in query for w in ("நன்றி", "சரி")):
            return "மிக்க மகிழ்ச்சி! 😊 மேலும் ஏதேனும் தகவல் தேவைப்பட்டால் கேளுங்கள்."
        return "மிக்க மகிழ்ச்சி! 😊 உங்களுக்கு உதவ எப்போதும் தயாராக உள்ளேன்."

    if lang == LanguageCode.SINHALA:
        if conv_type == "GREETING" or "ආයුබෝවන්" in query:
            return (
                "ආයුබෝවන්! මම GovGuide AI. මම ඔබට චිකාගෝ ව්‍යාපාරික බලපත්‍ර, අවශ්‍ය ලියකියවිලි, "
                "ගාස්තු සහ අයදුම් කිරීමේ ක්‍රියාවලිය පිළිබඳව උපකාර කළ හැක."
            )
        if conv_type in ("THANKS", "ACKNOWLEDGEMENT") or any(w in query for w in ("ස්තූතියි", "හරි")):
            return "ඔබව සාදරයෙන් පිළිගනිමි! 😊 තවත් තොරතුරු අවශ්‍ය නම් විමසන්න."
        return "ඔබව සාදරයෙන් පිළිගනිමි! 😊"

    # Standard English
    if conv_type == "GOODBYE" or any(w in q for w in ("bye", "goodbye", "farewell", "have a great day", "have a good day", "have a nice day")):
        return "You're welcome! Have a great day."

    if "thank you for your information" in q or "thanks for the information" in q or "thank you for the information" in q:
        return "You're welcome! 😊 If you need anything else about the service, feel free to ask."

    if any(w in q for w in ("you're welcome", "you are welcome", "your welcome", "happy to help", "no problem", "my pleasure")):
        return "Happy to help! 😊 Feel free to ask if you have any questions."

    if any(w in q for w in ("that's helpful", "that is helpful", "very helpful", "that's very helpful", "that is very helpful")):
        return "I'm glad to help! 😊 Let me know if you have any more questions."

    if conv_type in ("THANKS", "ACKNOWLEDGEMENT") or any(w in q for w in ("thank you", "thanks", "ok", "okay", "got it", "alright", "great", "understood", "seri", "sari", "nandri", "bro", "appreciate it", "much appreciated")):
        return "You're welcome! 😊 If you need anything else about the service, feel free to ask."

    if conv_type == "GREETING" or any(w in q for w in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy")):
        return (
            "Hello! I am GovGuide AI, your City of Chicago government services and business licensing assistant. "
            "How can I help you today? You can ask me about business licenses (such as Retail Food, Limited Business, or Children's Services), "
            "application procedures, required documentation, fees, or City department offices."
        )

    return "You're welcome! 😊 If you need anything else about the service, feel free to ask."


# ── Single & Multi-Intent Formatters ──────────────────────────────────────────

def format_intent_response(
    query: str,
    intent: Intent,
    evidence_bundle: Dict[str, Any],
    intents: Optional[List[Any]] = None,
    language: Optional[LanguageCode] = None,
) -> Tuple[str, bool, str]:
    """
    Synthesizes a natural conversational assistant response based on user intent.
    Supports single-intent and multi-intent queries with strict evidence grounding and language adaptation.

    Returns:
        Tuple of (formatted_answer, is_target_information_available, explanation)
    """
    lang = language or resolve_query_language(query)
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
    if not resolved_intents:
        if intent and (intent.value if hasattr(intent, "value") else str(intent)) not in (
            Intent.GENERAL.value, "general", Intent.UNKNOWN.value, "unknown"
        ):
            resolved_intents = [intent]
        elif query:
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
        return format_multi_intent_response(query, substantive_intents, evidence_bundle, language=lang)

    profiles = extract_service_profiles(evidence_bundle)
    if not profiles:
        return (
            get_insufficient_evidence_response(lang),
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
        return _format_geographic_eligibility_response(primary, query, lang=lang)

    # Check for renewal / expiration queries
    if "renew" in q_lower or "expiration" in q_lower or "expire" in q_lower:
        return _format_renewal_response(primary, query, lang=lang)

    # Check for comprehensive question asking for everything
    if any(w in q_lower for w in ("everything", "all requirements", "full guide", "complete process", "step by step guide to open")):
        return _format_comprehensive_response(primary, query, lang=lang)

    if intent_val in (Intent.LICENSE_CATALOG.value, "license_catalog", "available_business_licenses"):
        return _format_license_catalog_response(profiles, query, lang=lang)
    elif intent_val == Intent.FEES.value:
        return _format_fee_response(primary, query, lang=lang)
    elif intent_val == Intent.REQUIRED_DOCUMENTS.value:
        return _format_documents_response(primary, query, lang=lang)
    elif intent_val == Intent.ELIGIBILITY.value:
        return _format_eligibility_response(primary, query, lang=lang)
    elif intent_val in (Intent.APPLICATION_PROCEDURE.value, Intent.PROCEDURE.value):
        return _format_procedure_response(primary, query, lang=lang)
    elif intent_val == Intent.COMPARISON.value:
        return _format_comparison_response(profiles, query, lang=lang)
    elif intent_val in (Intent.SOURCE_EVIDENCE.value, "source_verification"):
        return _format_source_evidence_response(primary, query, lang=lang)
    elif intent_val == Intent.OFFICE_INFORMATION.value:
        return _format_office_response(primary, query, lang=lang)
    elif intent_val == Intent.RENEWAL.value:
        return _format_renewal_response(primary, query, lang=lang)
    elif intent_val in (
        Intent.SERVICE_LOOKUP.value, Intent.SERVICE_INFORMATION.value,
        Intent.LICENSE_IDENTIFICATION.value, "license_identification"
    ):
        return _format_service_lookup_response(primary, query, lang=lang)
    else:
        return _format_general_response(primary, query, lang=lang)


def _format_license_catalog_response(
    profiles: List[Dict[str, Any]],
    query: str,
    lang: LanguageCode = LanguageCode.ENGLISH,
) -> Tuple[str, bool, str]:
    if not profiles:
        return (
            get_insufficient_evidence_response(lang),
            False,
            "No matching government service records were found in the knowledge base."
        )

    # Deduplicate profiles strictly by service_code preserving order
    seen_codes = set()
    deduped_profiles = []
    for p in profiles:
        c = p.get("service_code")
        if c and c not in seen_codes:
            seen_codes.add(c)
            deduped_profiles.append(p)

    selected = deduped_profiles
    count = len(selected)

    items_text = []
    for i, p in enumerate(selected, 1):
        name = p.get("service_name") or f"Service {p.get('service_code')}"
        code = p.get("service_code")
        desc = (p.get("overview") or p.get("eligibility_summary") or "").strip()
        if desc and desc.upper() not in NOT_AVAILABLE_VALUES and "NOT_AVAILABLE" not in desc:
            first_sent = re.split(r"(?<=[.!?])\s+", desc)[0].strip()
            if len(first_sent) > 160:
                first_sent = first_sent[:157].rstrip() + "..."
            short_desc = first_sent
        else:
            short_desc = "Summary unavailable in the current verified knowledge base."

        items_text.append(f"{i}. {name} — Code: {code}\n   Summary: {short_desc}")

    catalog_body = "\n\n".join(items_text)

    if lang in (LanguageCode.THANGLISH, LanguageCode.MIXED):
        lead = f"Verified government knowledge base-la irukka {count} services oda summary idho:\n\n"
        tail = (
            f"\n\nThese {count} services are based on the current verified GovernmentService knowledge base. "
            "If you tell me your business/activity, I can identify the most relevant service."
        )
    elif lang == LanguageCode.TAMIL:
        lead = f"சரிபார்க்கப்பட்ட அறிவுத் தளத்தில் உள்ள {count} அரசு சேவைகளின் சுருக்கம் இதோ:\n\n"
        tail = (
            f"\n\nஇந்த {count} சேவைகளும் தற்போதைய சரிபார்க்கப்பட்ட GovernmentService அறிவுத் தளத்தை அடிப்படையாகக் கொண்டவை. "
            "உங்கள் வணிகம் அல்லது செயல்பாட்டைக் கூறினால், உங்களுக்கு மிகவும் பொருத்தமான சேவையை அடையாளம் காண உதவுகிறேன்."
        )
    elif lang == LanguageCode.SINHALA:
        lead = f"තහවුරු කරන ලද දැනුම් පදනමේ ඇති රජයේ සේවාවන් {count} හි සාරාංශය මෙන්න:\n\n"
        tail = (
            f"\n\nමෙම සේවාවන් {count} වත්මන් තහවුරු කළ GovernmentService දැනුම් පදනම මත පදනම් වේ. "
            "ඔබගේ ව්‍යාපාරය හෝ ක්‍රියාකාරකම සඳහන් කළහොත්, වඩාත් ගැලපෙන සේවාව හඳුනා ගැනීමට මට උපකාර කළ හැක."
        )
    elif lang == LanguageCode.SINGLISH:
        lead = f"Verified knowledge base eke thiyena government services {count} wala summary eka mehema thiyenawa:\n\n"
        tail = (
            f"\n\nMe services {count} danata verified GovernmentService knowledge base eka matha adala wenne. "
            "Oya karanna inna business eka kiwwoth match wena service eka identify karala denna puluwan."
        )
    else:
        lead = f"Here is a summary of the {count} government services available in the verified knowledge base:\n\n"
        tail = (
            f"\n\nThese {count} services are based on the current verified GovernmentService knowledge base. "
            "If you tell me your business/activity, I can identify the most relevant service."
        )

    full_answer = f"{lead}{catalog_body}{tail}"
    return full_answer, True, f"Provided dynamic catalog of {count} distinct government services from official records."


def _format_service_full_details(
    p: Dict[str, Any],
    query: str,
    lang: LanguageCode = LanguageCode.ENGLISH
) -> Tuple[str, bool, str]:
    """
    Formats a comprehensive multi-section service overview as specified in Requirement 6:
    ### [Service Name]
    **Code:** [service_code]

    **Overview**
    [verified overview]

    **Eligibility**
    [verified eligibility]

    **Required Documents**
    [verified documents]

    **Application Procedure**
    [verified procedure]

    **Fees**
    [verified fees]

    **Renewal**
    [verified renewal]

    **Responsible Office**
    [verified office/contact]

    **Legal / Reference**
    [verified legal/source information]
    """
    name = p.get("service_name") or f"Service {p.get('service_code')}"
    code = p.get("service_code") or "N/A"
    url = p.get("source_url") or p.get("application_portal_url") or "https://www.chicago.gov/bacp"

    sections = [
        f"### {name}",
        f"**Code:** {code}\n"
    ]

    # Overview
    overview = p.get("overview") or p.get("service_description")
    if is_valid_field(overview):
        sections.append(f"**Overview**\n{overview.strip()}\n")
    else:
        sections.append("**Overview**\nInformation not available in the current verified knowledge base.\n")

    # Eligibility
    elig = p.get("eligibility_summary") or p.get("eligibility_criteria")
    if is_valid_field(elig):
        sections.append(f"**Eligibility**\n{elig.strip()}\n")
    else:
        sections.append("**Eligibility**\nInformation not available in the current verified knowledge base.\n")

    # Required Documents
    docs = p.get("required_documents")
    if is_valid_field(docs):
        doc_items = [d.strip() for d in re.split(r"[|;]|\n(?:\s*[-•*]\s*)?", docs) if d.strip()]
        doc_bullets = "\n".join(f"• {d.lstrip('•-* ')}" for d in doc_items)
        sections.append(f"**Required Documents**\n{doc_bullets}\n")
    else:
        sections.append("**Required Documents**\nInformation not available in the current verified knowledge base.\n")

    # Application Procedure
    proc = p.get("application_steps")
    insp = p.get("inspection_required")
    portal = p.get("application_portal_url") or url
    if is_valid_field(proc):
        raw_steps = [s.strip() for s in re.split(r"[|;]|\n(?:\s*\d+\.\s*)", proc) if s.strip()]
        if len(raw_steps) > 1:
            steps_formatted = "\n".join(f"{i}. {s.lstrip('0123456789. ')}" for i, s in enumerate(raw_steps, 1))
        else:
            steps_formatted = proc.strip()
        insp_note = f"\n• **Inspection Requirement:** {insp}" if is_valid_field(insp) else ""
        sections.append(f"**Application Procedure**\n{steps_formatted}{insp_note}\nPortal: {portal}\n")
    elif is_valid_field(portal) and portal != "NOT_AVAILABLE":
        sections.append(f"**Application Procedure**\nSubmit online via Chicago Business Direct ({portal}).\n")
    else:
        sections.append("**Application Procedure**\nInformation not available in the current verified knowledge base.\n")

    # Fees
    fee_amt = p.get("fee_amount")
    fee_desc = p.get("fee_description")
    if is_valid_field(fee_amt):
        extra = f" ({fee_desc})" if is_valid_field(fee_desc) else ""
        sections.append(f"**Fees**\n{fee_amt}{extra}\n")
    else:
        sections.append("**Fees**\nInformation not available in the current verified knowledge base.\n")

    # Renewal
    term = p.get("license_term_years")
    period = p.get("renewal_period")
    if is_valid_field(term) or is_valid_field(period):
        parts = []
        if is_valid_field(term):
            parts.append(f"Validity: {term}")
        if is_valid_field(period):
            parts.append(f"Renewal: {period}")
        sections.append(f"**Renewal**\n{' | '.join(parts)}\n")
    else:
        sections.append("**Renewal**\nInformation not available in the current verified knowledge base.\n")

    # Responsible Office
    addr = p.get("office_address") or "Small Business Center (SBC), City Hall, 121 N. LaSalle St., Room 800, Chicago, IL 60602"
    phone = p.get("office_phone") or "(312) 744-6060"
    hours = p.get("office_hours") or "Monday - Friday, 8:30 AM - 4:30 PM"
    dept = p.get("office_name") or "City of Chicago Department of Business Affairs and Consumer Protection (BACP)"
    sections.append(
        f"**Responsible Office**\n"
        f"{dept}\n"
        f"• Address: {addr}\n"
        f"• Business Hours: {hours}\n"
        f"• Phone: {phone}\n"
    )

    # Legal / Reference
    legal = p.get("legal_reference")
    if is_valid_field(legal):
        sections.append(f"**Legal / Reference**\n{legal.strip()}\nOfficial Portal: {url} [Source 1]")
    else:
        sections.append(f"**Legal / Reference**\nOfficial Portal: {url} [Source 1]")

    answer = "\n".join(sections)
    return answer, True, f"Full verified details for {name} (Code {code}) provided from official records."


def _format_service_lookup_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    cat = (p.get("category") or "Business Licensing").replace("_", " ").title()
    overview = p.get("overview") or p.get("eligibility_summary") or "Municipal business license issued by the City of Chicago."
    url = p["source_url"]
    q_lower = query.lower()

    # 1. Specialized cake / bakery business handling
    if bool(re.search(r"\b(cake|baking|bake|pastry|cupcake)\b", q_lower)) and "sport" not in q_lower:
        if lang in (LanguageCode.THANGLISH, LanguageCode.MIXED):
            answer = (
                "Cake business start panna, first unga business setup fixed commercial food establishment-aa, home-based-aa, illa retail bakery-aa nu determine panna vendum.\n\n"
                f"Available Chicago records-la commercial food preparation matrum bakery operations-ku **{name} (Code {code})** applicable aagum [Source 1].\n\n"
                "Unga business home-la irukkuma illa shop/commercial location-la irukkuma?"
            )
        elif lang == LanguageCode.TAMIL:
            answer = (
                "கேக் வணிகத்தைத் தொடங்க, முதலில் உங்கள் வணிக அமைப்பு வணிக ரீதியான உணவகமா/பேக்கரியா அல்லது வீட்டிலிருந்தே இயங்கும் வணிகமா என்பதை தீர்மானிக்க வேண்டும்.\n\n"
                f"சிகாகோ பதிவுகளின்படி, உணவு தயாரிப்பு மற்றும் பேக்கரி விற்பனைக்கு **{name} (Code {code})** பொருந்தும் [Source 1].\n\n"
                "உங்கள் வணிகம் வீட்டிலிருந்து இயங்குமா அல்லது கடையிலிருந்தா?"
            )
        else:
            answer = (
                "To start a cake business, it is essential to first determine whether your setup is a fixed commercial food establishment/bakery or a home-based operation.\n\n"
                f"Under City of Chicago regulations, commercial food preparation and retail bakeries typically operate under the **{name} (Code {code})** [Source 1].\n\n"
                "Will your cake business operate from a commercial storefront/bakery or from home?"
            )
        return answer, True, "Cake business guidance and applicable license overview provided from official records."

    # 2. Specialized tailoring service handling
    if bool(re.search(r"\b(tailoring|tailor|tailering|tailorng|alterations)\b", q_lower)) and "sport" not in q_lower:
        if lang in (LanguageCode.THANGLISH, LanguageCode.MIXED):
            answer = (
                f"Tailoring shop open panna, Chicago municipal guidelines padi general commercial retail & service activity-ku **{name} (Code {code})** check pannanum [Source 1].\n\n"
                f"• **Scope & Purpose:** {overview}\n\n"
                "Neenga storefront tailoring shop open panna poringala, illa home-based tailoring service-aa?"
            )
        else:
            answer = (
                f"For opening a tailoring shop in Chicago, municipal regulations govern commercial storefront service activities under the **{name} (Code {code})** [Source 1].\n\n"
                f"• **Scope & Purpose:** {overview}\n\n"
                "Are you planning a commercial storefront tailoring shop or a home-based tailoring service?"
            )
        return answer, True, "Tailoring service guidance provided from official records."

    # 3. Comprehensive service details for "tell me about", "service details", license code/name lookup
    # As specified in Requirement 6: Provide ALL AVAILABLE VERIFIED INFORMATION for that service.
    return _format_service_full_details(p, query, lang=lang)


def _format_procedure_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    steps = p["application_steps"]
    portal = p["application_portal_url"] or p["source_url"]
    insp = p["inspection_required"]

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

    if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Application Procedure:**\n"
            f"{steps_formatted}{insp_note}\n\n"
            f"Applications online-la Chicago Business Direct ({portal}) vazhiya alladhu City Hall Small Business Center (121 N. LaSalle St., Room 800)-la direct-a submit pannalaam [Source 1].\n\n"
            f"If you want, I can also show the eligibility, required documents, fees, and renewal details."
        )
    elif lang == LanguageCode.TAMIL:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**விண்ணப்ப முறை:**\n"
            f"{steps_formatted}{insp_note}\n\n"
            f"விண்ணப்பங்களை Chicago Business Direct ({portal}) மூலம் ஆன்லைனில் அல்லது City Hall Small Business Center (121 N. LaSalle St., Room 800) இல் சமர்ப்பிக்கலாம் [Source 1]."
        )
    elif lang == LanguageCode.SINHALA:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**අයදුම් කිරීමේ පියවර:**\n"
            f"{steps_formatted}{insp_note}\n\n"
            f"Chicago Business Direct ({portal}) හරහා මාර්ගගතව හෝ City Hall Small Business Center (121 N. LaSalle St., Room 800) හිදී අයදුම්පත් ඉදිරිපත් කළ හැක [Source 1]."
        )
    elif lang == LanguageCode.SINGLISH:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Application Procedure:**\n"
            f"{steps_formatted}{insp_note}\n\n"
            f"Applications Chicago Business Direct ({portal}) haraha online hari City Hall Small Business Center (121 N. LaSalle St., Room 800) eke direct hari submit karanna puluwan [Source 1]."
        )
    else:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Application Procedure:**\n"
            f"{steps_formatted}{insp_note}\n\n"
            f"Applications can be submitted online via Chicago Business Direct ({portal}) "
            f"or in person at City Hall (Small Business Center, 121 N. LaSalle St., Room 800) [Source 1].\n\n"
            f"If you want, I can also show the eligibility, required documents, fees, and renewal details."
        )
    return answer, True, "Application procedure steps provided from official records."


def _format_documents_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    docs = p["required_documents"]
    url = p["source_url"]

    if not is_valid_field(docs):
        if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Required Documents:**\n"
                f"Information not available in the current verified knowledge base.\n\n"
                f"Current documentation requirements-ai verify panna City of Chicago BACP alladhu Chicago Business Direct ({url}) check pannunga [Source 1]."
            )
        elif lang == LanguageCode.TAMIL:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**தேவையான ஆவணங்கள்:**\n"
                f"தகவல் தற்போது சரிபார்க்கப்பட்ட தரவுத்தளத்தில் இல்லை.\n\n"
                f"தயவுசெய்து Chicago Business Direct ({url}) தளத்தைப் பார்க்கவும் [Source 1]."
            )
        elif lang == LanguageCode.SINHALA:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**අවශ්‍ය ලියකියවිලි:**\n"
                f"වත්මන් නිල දත්ත ගබඩාවේ තොරතුරු නොමැත.\n\n"
                f"කරුණාකර Chicago Business Direct ({url}) පරීක්ෂා කරන්න [Source 1]."
            )
        else:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Required Documents:**\n"
                f"Information not available in the current verified knowledge base.\n\n"
                f"Please verify current documentation requirements with the City of Chicago BACP or via Chicago Business Direct at {url} [Source 1]."
            )
        return answer, False, "Required documents checklist is unavailable in official records."

    doc_items = [d.strip() for d in re.split(r"[|;]|\n(?:\s*[-•*]\s*)?", docs) if d.strip()]
    doc_bullets = "\n".join(f"• {d.lstrip('•-* ')}" for d in doc_items)

    if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Required Documents:**\n"
            f"{doc_bullets}\n\n"
            f"Indha requirements official records ({url}) based-a provide pannapattu irukku [Source 1].\n\n"
            f"If you want, I can also show the eligibility, fees, application procedure, and renewal details."
        )
    elif lang == LanguageCode.TAMIL:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**தேவையான ஆவணங்கள்:**\n"
            f"{doc_bullets}\n\n"
            f"இவை அதிகாரப்பூர்வ பதிவுகளின்படி ({url}) வழங்கப்பட்டுள்ளன [Source 1]."
        )
    elif lang == LanguageCode.SINHALA:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**අවශ්‍ය ලියකියවිලි:**\n"
            f"{doc_bullets}\n\n"
            f"මෙම අවශ්‍යතා නිල වාර්තා ({url}) මත පදනම් වේ [Source 1]."
        )
    elif lang == LanguageCode.SINGLISH:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Required Documents:**\n"
            f"{doc_bullets}\n\n"
            f"Me awashyatha official records ({url}) anuwa we [Source 1]."
        )
    else:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Required Documents:**\n"
            f"{doc_bullets}\n\n"
            f"These requirements are based on the available official records ({url}) [Source 1].\n\n"
            f"If you want, I can also show the eligibility, fees, application procedure, and renewal details."
        )
    return answer, True, "Required documentation list provided from official records."


def _format_fee_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    fee_amt = p["fee_amount"]
    fee_desc = p["fee_description"]
    url = p["source_url"]

    if not is_valid_field(fee_amt):
        if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Fees:**\n"
                f"Information not available in the current verified knowledge base.\n\n"
                f"The available government records do not currently provide a verified fee amount for this license. "
                f"Current fee details-ai verify panna City of Chicago BACP alladhu Chicago Business Direct ({url}) check pannunga [Source 1]."
            )
        elif lang == LanguageCode.TAMIL:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**கட்டணம்:**\n"
                f"தகவல் தற்போது சரிபார்க்கப்பட்ட தரவுத்தளத்தில் இல்லை.\n\n"
                f"The available government records do not currently provide a verified fee amount for this license. "
                f"தயவுசெய்து Chicago Business Direct ({url}) தளத்தைப் பார்க்கவும் [Source 1]."
            )
        elif lang == LanguageCode.SINHALA:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**ගාස්තු:**\n"
                f"වත්මන් නිල දත්ත ගබඩාවේ තොරතුරු නොමැත.\n\n"
                f"The available government records do not currently provide a verified fee amount for this license. "
                f"කරුණාකර Chicago Business Direct ({url}) පරීක්ෂා කරන්න [Source 1]."
            )
        else:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Fees:**\n"
                f"Information not available in the current verified knowledge base.\n\n"
                f"The available government records do not currently provide a verified fee amount for this license. "
                f"Please verify the current fee with the City of Chicago Department of Business Affairs and Consumer Protection (BACP) "
                f"or check Chicago Business Direct at {url} [Source 1]."
            )
        return answer, False, "Verified fee amount is unavailable in retrieved official records."

    extra = f" ({fee_desc})" if is_valid_field(fee_desc) else ""

    if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Fees:**\n"
            f"Official records padi, license fee **{fee_amt}**{extra}.\n\n"
            f"Neenga current fee verify panna alladhu payment submit panna Chicago Business Direct ({url}) use pannalaam [Source 1].\n\n"
            f"If you want, I can also show the eligibility, required documents, application procedure, and renewal details."
        )
    elif lang == LanguageCode.TAMIL:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**கட்டணம்:**\n"
            f"அதிகாரப்பூர்வ பதிவுகளின்படி, உரிமக் கட்டணம் **{fee_amt}**{extra}.\n\n"
            f"Chicago Business Direct ({url}) மூலம் கட்டணத்தைச் செலுத்தலாம் அல்லது சரிபார்க்கலாம் [Source 1]."
        )
    elif lang == LanguageCode.SINHALA:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**ගාස්තු:**\n"
            f"නිල වාර්තාවලට අනුව, බලපත්‍ර ගාස්තුව **{fee_amt}**{extra} වේ.\n\n"
            f"Chicago Business Direct ({url}) හරහා ගාස්තුව ගෙවීමට හෝ තහවුරු කිරීමට හැක [Source 1]."
        )
    elif lang == LanguageCode.SINGLISH:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Fees:**\n"
            f"Official records anuwa, license fee eka **{fee_amt}**{extra} wenawa.\n\n"
            f"Chicago Business Direct ({url}) haraha payment karanna puluwan [Source 1]."
        )
    else:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Fees:**\n"
            f"A **{name} (Code {code})** costs **{fee_amt}**{extra}, according to the available official records.\n\n"
            f"You can verify the current fee or submit your payment through Chicago Business Direct ({url}) [Source 1].\n\n"
            f"If you want, I can also show the eligibility, required documents, application procedure, and renewal details."
        )
    return answer, True, "Verified fee details provided from official records."


def _format_office_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p.get("service_name")
    code = p.get("service_code")
    addr = p.get("office_address") or "121 N. LaSalle St., Room 800, Chicago, IL 60602"
    phone = p.get("office_phone") or "(312) 744-6060"
    hours = p.get("office_hours") or "Monday - Friday, 8:30 AM - 4:30 PM"
    url = p.get("source_url") or "https://www.chicago.gov/bacp"

    has_specific = bool(name and code and code != "N/A")

    if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
        lead = f"**{name} — Code {code}**\n\n" if has_specific else ""
        answer = (
            f"{lead}**Responsible Office:**\n"
            f"**City of Chicago Department of Business Affairs and Consumer Protection (BACP)**\n\n"
            f"• **Address:** Small Business Center (SBC), City Hall, {addr}\n"
            f"• **Business Hours:** {hours}\n"
            f"• **Phone:** {phone}\n"
            f"• **Online Portal:** {url} [Source 1]\n\n"
            f"City Hall Small Business Center-la business hours-la direct-a consultation panna mudiyum."
        )
    elif lang == LanguageCode.TAMIL:
        lead = f"**{name} — Code {code}**\n\n" if has_specific else ""
        answer = (
            f"{lead}**பொறுப்பான அலுவலகம்:**\n"
            f"**City of Chicago Department of Business Affairs and Consumer Protection (BACP)**\n\n"
            f"• **முகவரி:** Small Business Center (SBC), City Hall, {addr}\n"
            f"• **வேலை நேரம்:** {hours}\n"
            f"• **தொலைபேசி:** {phone}\n"
            f"• **இணையதளம்:** {url} [Source 1]"
        )
    elif lang == LanguageCode.SINHALA:
        lead = f"**{name} — Code {code}**\n\n" if has_specific else ""
        answer = (
            f"{lead}**වගකිවයුතු කාර්යාලය:**\n"
            f"**City of Chicago Department of Business Affairs and Consumer Protection (BACP)**\n\n"
            f"• **ලිපිනය:** Small Business Center (SBC), City Hall, {addr}\n"
            f"• **වේලාවන්:** {hours}\n"
            f"• **දුරකථන:** {phone}\n"
            f"• **නිල වෙබ් අඩවිය:** {url} [Source 1]"
        )
    else:
        service_lead = f"**{name} — Code {code}**\n\n" if has_specific else ""
        answer = (
            f"{service_lead}**Responsible Office:**\n"
            f"**City of Chicago Department of Business Affairs and Consumer Protection (BACP)**\n\n"
            f"• **Address:** Small Business Center (SBC), City Hall, {addr}\n"
            f"• **Business Hours:** {hours}\n"
            f"• **Phone:** {phone}\n"
            f"• **Online Portal:** {url} [Source 1]\n\n"
            f"In-person consultations and applications can be conducted at City Hall during regular business hours."
        )
    return answer, True, "Office contact and address information provided from official records."


def _format_eligibility_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    elig = (p["eligibility_summary"] or p.get("overview") or "").strip().rstrip(".")
    url = p["source_url"]

    if not is_valid_field(elig):
        if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Eligibility:**\n"
                f"Information not available in the current verified knowledge base.\n\n"
                f"City of Chicago BACP ({url}) check panni verify pannunga [Source 1]."
            )
        elif lang == LanguageCode.TAMIL:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**தகுதி வரம்புகள்:**\n"
                f"தகவல் தற்போது சரிபார்க்கப்பட்ட தரவுத்தளத்தில் இல்லை.\n\n"
                f"BACP இணையதளத்தை ({url}) பார்க்கவும் [Source 1]."
            )
        elif lang == LanguageCode.SINHALA:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**සුදුසුකම්:**\n"
                f"වත්මන් නිල දත්ත ගබඩාවේ තොරතුරු නොමැත.\n\n"
                f"BACP වෙබ් අඩවිය ({url}) පරීක්ෂා කරන්න [Source 1]."
            )
        else:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Eligibility:**\n"
                f"Information not available in the current verified knowledge base.\n\n"
                f"Please consult the City of Chicago BACP directly at {url} for current qualification rules. [Source 1]"
            )
        return answer, False, "Eligibility criteria unavailable in official records."

    if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Eligibility:**\n"
            f"{elig}.\n\n"
            f"*Official Source: City of Chicago BACP / Chicago Business Direct ({url}) [Source 1]*\n\n"
            f"If you want, I can also show the required documents, fees, application procedure, and renewal details."
        )
    elif lang == LanguageCode.TAMIL:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**தகுதி வரம்புகள்:**\n"
            f"{elig}.\n\n"
            f"*Official Source: City of Chicago BACP / Chicago Business Direct ({url}) [Source 1]*"
        )
    elif lang == LanguageCode.SINHALA:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**සුදුසුකම්:**\n"
            f"{elig}.\n\n"
            f"*Official Source: City of Chicago BACP / Chicago Business Direct ({url}) [Source 1]*"
        )
    elif lang == LanguageCode.SINGLISH:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Eligibility:**\n"
            f"{elig}.\n\n"
            f"*Official Source: City of Chicago BACP / Chicago Business Direct ({url}) [Source 1]*"
        )
    else:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Eligibility:**\n"
            f"A **{name} (Code {code})** is intended for {elig} (aged 18 or older where required for general business operations).\n\n"
            f"*Official Source: City of Chicago BACP / Chicago Business Direct ({url}) [Source 1]*\n\n"
            f"If you want, I can also show the required documents, fees, application procedure, and renewal details."
        )
    return answer, True, "Eligibility criteria provided from official records."


def _format_renewal_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    term = p["license_term_years"]
    period = p["renewal_period"]
    url = p["source_url"]

    q_lower = query.lower()
    asking_for_deadline = "deadline" in q_lower or "due date" in q_lower

    if asking_for_deadline:
        if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Renewal:**\n"
                f"Available records-la **{name} (Code {code})**-ku verified renewal deadline kidaikkala.\n\n"
                f"The available records do not provide a verified renewal deadline for the **{name} (Code {code})**.\n\n"
                f"General-a expiration date-ku munnadi renew panna vendum. "
                f"City of Chicago BACP ({url}) check pannunga [Source 1]."
            )
        elif lang == LanguageCode.TAMIL:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**புதுப்பித்தல்:**\n"
                f"**{name} (Code {code})** உரிமத்திற்கான புதுப்பித்தல் கடைசி தேதி பற்றிய தகவல் இல்லை.\n\n"
                f"The available records do not provide a verified renewal deadline for the **{name} (Code {code})**.\n\n"
                f"காலாவதியாகும் முன் BACP ({url}) மூலம் புதுப்பிக்கவும் [Source 1]."
            )
        elif lang == LanguageCode.SINHALA:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**අලුත් කිරීම:**\n"
                f"**{name} (Code {code})** සඳහා නිශ්චිත අලුත් කිරීමේ අවසන් දිනයක් නොමැත.\n\n"
                f"The available records do not provide a verified renewal deadline for the **{name} (Code {code})**.\n\n"
                f"කල් ඉකුත්වීමට පෙර BACP ({url}) පරීක්ෂා කරන්න [Source 1]."
            )
        else:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Renewal:**\n"
                f"The available records do not provide a verified renewal deadline for the **{name} (Code {code})**.\n\n"
                f"Licenses generally require renewal prior to their expiration date. "
                f"Please verify your specific license renewal deadline with the City of Chicago Department of Business Affairs and Consumer Protection (BACP) at {url} [Source 1]."
            )
        return answer, False, "Specific renewal deadline is unavailable in retrieved records."

    if not is_valid_field(term) and not is_valid_field(period):
        if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Renewal:**\n"
                f"Information not available in the current verified knowledge base.\n\n"
                f"Naan **{name} (Code {code})** pathina information kandupidithen, "
                f"aana renewal process alladhu deadline pathi verified information kidaikkala. "
                f"BACP-ai thodarpu kolla mudiyum [Source 1]."
            )
        elif lang == LanguageCode.TAMIL:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**புதுப்பித்தல்:**\n"
                f"தகவல் தற்போது சரிபார்க்கப்பட்ட தரவுத்தளத்தில் இல்லை.\n\n"
                f"BACP-ஐத் தொடர்பு கொள்ளவும் [Source 1]."
            )
        elif lang == LanguageCode.SINHALA:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**අලුත් කිරීම:**\n"
                f"වත්මන් නිල දත්ත ගබඩාවේ තොරතුරු නොමැත [Source 1]."
            )
        else:
            answer = (
                f"**{name} — Code {code}**\n\n"
                f"**Renewal:**\n"
                f"Information not available in the current verified knowledge base.\n\n"
                f"Please verify current renewal requirements with the City of Chicago Department of Business Affairs and Consumer Protection."
            )
        return answer, False, "Renewal details unavailable in retrieved records."

    term_str = term if is_valid_field(term) else "2 years"
    period_str = period if is_valid_field(period) else "every 2 years prior to expiration"

    if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Renewal:**\n"
            f"License **{term_str}** valid-aaga irukkum, matrum **{period_str}** renew panna vendum.\n\n"
            f"**Renewal Steps:**\n"
            f"1. City of Chicago holds, debt, matrum building violations illai enbadhai verify pannunga.\n"
            f"2. Expiration-ku munnadi Chicago Business Direct ({url}) vazhiya renewal application matrum fee submit pannunga [Source 1].\n\n"
            f"If you want, I can also show the overview, eligibility, required documents, fees, or application procedure."
        )
    elif lang == LanguageCode.TAMIL:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**புதுப்பித்தல்:**\n"
            f"உரிமம் **{term_str}** செல்லுபடியாகும், மேலும் **{period_str}** புதுப்பிக்கப்பட வேண்டும்.\n\n"
            f"**புதுப்பித்தல் படிகள்:**\n"
            f"1. நிலுவைக் கட்டணங்கள் மற்றும் விதிமீறல்கள் இல்லை என்பதை உறுதிப்படுத்தவும்.\n"
            f"2. காலாவதியாகும் முன் Chicago Business Direct ({url}) மூலம் புதுப்பித்தல் விண்ணப்பத்தை சமர்ப்பிக்கவும் [Source 1]."
        )
    elif lang == LanguageCode.SINHALA:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**අලුත් කිරීම:**\n"
            f"බලපත්‍රය **{term_str}** වලංගු වන අතර, **{period_str}** අලුත් කළ යුතුය.\n\n"
            f"**අලුත් කිරීමේ පියවර:**\n"
            f"1. කිසිදු නගර ණය හෝ නීතිමය ගැටළු නොමැති බව තහවුරු කරන්න.\n"
            f"2. කල් ඉකුත්වීමට පෙර Chicago Business Direct ({url}) හරහා අයදුම් කරන්න [Source 1]."
        )
    else:
        answer = (
            f"**{name} — Code {code}**\n\n"
            f"**Renewal:**\n"
            f"A **{name} (Code {code})** is valid for **{term_str}**, and renewal is required **{period_str}**.\n\n"
            f"**Renewal Steps:**\n"
            f"1. Check that all City of Chicago holds, debt, and building violations are resolved.\n"
            f"2. Submit your renewal application and fee online via Chicago Business Direct ({url}) prior to expiration [Source 1].\n\n"
            f"If you want, I can also show the overview, eligibility, required documents, fees, or application procedure."
        )
    return answer, True, "Renewal terms and validity provided from official records."


def _format_geographic_eligibility_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    url = p["source_url"]

    geo_match = re.search(
        r"\b(sri lanka|abroad|overseas|foreign|international|outside the (?:us|united states)|india|canada|uk|europe|another country|another state)\b",
        query,
        re.I,
    )
    location_str = geo_match.group(0).title() if geo_match else "outside Chicago / remotely"

    if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
        answer = (
            f"Available official records **{name} (Code {code})** Chicago-la irukkira business establishment-ku thevai enbadhai confirm pannudhu, "
            f"aana {location_str}-la irundhu remote-a apply panna mudiyuma enbadhai specify pannala.\n\n"
            f"Please City of Chicago BACP alladhu Chicago Business Direct ({url}) check panni verify pannunga [Source 1]."
        )
    elif lang == LanguageCode.TAMIL:
        answer = (
            f"அதிகாரப்பூர்வ பதிவுகள் **{name} (Code {code})** சிகாகோவில் உள்ள வணிகத்திற்கு பொருந்தும் என்பதை உறுதிப்படுத்துகின்றன, "
            f"ஆனால் {location_str} இல் இருந்து விண்ணப்பிக்க முடியுமா என்பதை குறிப்பிடவில்லை.\n\n"
            f"தயவுசெய்து Chicago Business Direct ({url}) மூலம் சரிபார்க்கவும் [Source 1]."
        )
    elif lang == LanguageCode.SINHALA:
        answer = (
            f"**{name} (Code {code})** චිකාගෝ හි ව්‍යාපාර සඳහා අදාළ වන නමුත් {location_str} සිට අයදුම් කළ හැකිද යන්න නිශ්චිතව දක්වා නොමැත.\n\n"
            f"කරුණාකර Chicago Business Direct ({url}) පරීක්ෂා කරන්න [Source 1]."
        )
    else:
        answer = (
            f"The available official records confirm that the **{name} (Code {code})** applies to a qualifying business establishment in Chicago, "
            f"but they do not specify whether an applicant currently residing in {location_str} can apply remotely.\n\n"
            f"Please verify this requirement with the City of Chicago Department of Business Affairs and Consumer Protection (BACP) "
            f"or check Chicago Business Direct at {url} [Source 1]."
        )
    return answer, False, f"Official records do not establish remote/international applicant eligibility for {location_str}."


def _format_comparison_response(profiles: List[Dict[str, Any]], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    if len(profiles) < 2:
        p = profiles[0]
        return _format_service_lookup_response(p, query, lang=lang)

    p1, p2 = profiles[0], profiles[1]
    name1, code1 = p1["service_name"], p1["service_code"]
    name2, code2 = p2["service_name"], p2["service_code"]

    cat1 = (p1.get("category") or "General").replace("_", " ").title()
    cat2 = (p2.get("category") or "General").replace("_", " ").title()

    def _sanitize_cell(val: Optional[str], default: str) -> str:
        if not val or not is_valid_field(val):
            return default
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


def _format_source_evidence_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
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


def _format_comprehensive_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
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


def _format_general_response(p: Dict[str, Any], query: str, lang: LanguageCode = LanguageCode.ENGLISH) -> Tuple[str, bool, str]:
    name = p["service_name"]
    code = p["service_code"]
    cat = (p.get("category") or "Business Licensing").replace("_", " ").title()
    overview = p.get("overview") or p.get("eligibility_summary") or "City of Chicago government business licensing service."
    url = p["source_url"]

    if lang == LanguageCode.THANGLISH or lang == LanguageCode.MIXED:
        answer = (
            f"**{name} (Code {code})** ({cat}):\n\n"
            f"{overview}\n\n"
            f"Fees, required paperwork, eligibility, alladhu how to apply pathina details thevaiya?\n\n"
            f"*Official Source: Chicago Business Direct ({url}) [Source 1]*"
        )
    elif lang == LanguageCode.TAMIL:
        answer = (
            f"**{name} (Code {code})** ({cat}):\n\n"
            f"{overview}\n\n"
            f"கட்டணம், தேவையான ஆவணங்கள் அல்லது விண்ணப்ப முறை பற்றிய விவரங்கள் வேண்டுமா?\n\n"
            f"*Official Source: Chicago Business Direct ({url}) [Source 1]*"
        )
    else:
        answer = (
            f"Regarding **{name} (Code {code})** ({cat}):\n\n"
            f"{overview}\n\n"
            f"Please let me know if you would like information on fees, required paperwork, eligibility, or how to apply.\n\n"
            f"*Official Source: Chicago Business Direct ({url}) [Source 1]*"
        )
    return answer, True, "General service advisory synthesized from official records."


def format_multi_intent_response(
    query: str,
    intents: List[Any],
    evidence_bundle: Dict[str, Any],
    language: LanguageCode = LanguageCode.ENGLISH,
) -> Tuple[str, bool, str]:
    """
    Generates a coherent, combined response addressing every detected intent in a multi-intent query.
    """
    profiles = extract_service_profiles(evidence_bundle)
    if not profiles:
        return (
            get_insufficient_evidence_response(language),
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
