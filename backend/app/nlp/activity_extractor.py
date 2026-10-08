"""
GovGuide AI — Business Activity & Entity Classifier

Extracts and categorizes specific business activities and domain entities
from natural-language citizen queries across English, Thanglish, Tamil, Sinhala, and Singlish.

Key Principles:
- Generic terms ("shop", "business", "retail", "company") remain GENERIC and are NEVER forced to food or specific licenses.
- Specialized activities (clothing, tailoring, electronics, bakery, restaurant, grocery, etc.) are accurately classified.
- Distinguishes between home-based operations, fixed food establishments, and specialized retail/services.
"""

from enum import Enum
import re
from typing import List, Optional, Set, Tuple
from pydantic import BaseModel, Field


class BusinessActivityType(str, Enum):
    # Food & Beverage Domains
    FOOD_RESTAURANT = "food_restaurant"
    FOOD_BAKERY_CAKE = "food_bakery_cake"
    FOOD_GROCERY = "food_grocery"
    FOOD_TRUCK = "food_truck"
    FOOD_GENERAL = "food_general"
    LIQUOR_BAR = "liquor_bar"

    # Retail Goods Domains
    RETAIL_CLOTHING = "retail_clothing"
    RETAIL_ELECTRONICS_MOBILE = "retail_electronics_mobile"
    RETAIL_TOBACCO = "retail_tobacco"
    RETAIL_GENERAL_SPECIFIED = "retail_general_specified"

    # Services Domains
    SERVICE_TAILORING = "service_tailoring"
    SERVICE_CHILDCARE = "service_childcare"
    SERVICE_AUTO = "service_auto"
    SERVICE_MASSAGE = "service_massage"
    SERVICE_ENTERTAINMENT = "service_entertainment"
    SERVICE_HOTEL = "service_hotel"
    SERVICE_ANIMAL_CARE = "service_animal_care"
    SERVICE_PARKING = "service_parking"

    # Generic & Unspecified (Ambiguous)
    GENERIC_RETAIL = "generic_retail"      # "retail shop", "store", "kadai" (goods unspecified)
    GENERIC_BUSINESS = "generic_business"  # "business", "company", "start pannum" (activity unspecified)
    
    # Non-business / Unknown
    UNRECOGNIZED_TOKEN = "unrecognized_token"
    NONE = "none"


class BusinessActivity(BaseModel):
    activity_type: BusinessActivityType
    extracted_text: str
    is_food_related: bool = False
    is_generic_or_ambiguous: bool = False
    suggested_candidate_service: Optional[str] = None
    clarification_prompt_type: Optional[str] = None  # "retail_type", "business_type", "cake_setup", "tailoring_setup"


# ── Pattern Definitions for Business Activity Extraction ─────────────────────

_ACTIVITY_PATTERNS: List[Tuple[BusinessActivityType, str, bool, bool, Optional[str], Optional[str]]] = [
    # 1. Bakery / Cake Business
    (
        BusinessActivityType.FOOD_BAKERY_CAKE,
        r"\b(cake\s+(?:business|shop|store|baking|sell)|baking\s+cake|bake\s+cake|bakery|bakeries|cupcakes?|pastr(?:y|ies)|home\s+baking|cake\s+bissinness|cake\s+bisness|cake\s+panradhu)\b",
        True,   # is_food_related
        False,  # is_generic_or_ambiguous
        "Retail Food Establishment License",
        "cake_setup",
    ),

    # 2. Food Truck / Mobile Food
    (
        BusinessActivityType.FOOD_TRUCK,
        r"\b(food\s+truck|mobile\s+food|food\s+cart|street\s+food\s+vendor|mobile\s+vendor)\b",
        True,
        False,
        "Mobile Food License",
        None,
    ),

    # 3. Grocery / Food Store
    (
        BusinessActivityType.FOOD_GROCERY,
        r"\b(grocery|groceries|grocery\s+(?:shop|store|kadai)|supermarket|provision\s+store|maligai\s+(?:kadai|store))\b",
        True,
        False,
        "Retail Food Establishment License",
        None,
    ),

    # 4. Restaurant / Dine-in / Food Service
    (
        BusinessActivityType.FOOD_RESTAURANT,
        r"\b(restaurant|restaurants|restaurent|resturant|cafe|cafes|diner|diners|bistro|eatery|coffee\s+shop|canteen|hotel\s+food|saapadu\s+kadai|unavagam)\b",
        True,
        False,
        "Retail Food Establishment License",
        None,
    ),

    # 5. General Food Business (Explicit Food Activity)
    (
        BusinessActivityType.FOOD_GENERAL,
        r"\b(food\s+business|food\s+establishment|food\s+service|food\s+license|food\s+licence|unavu\s+business|food\s+panradhu)\b",
        True,
        False,
        "Retail Food Establishment License",
        None,
    ),

    # 6. Bar / Tavern / Liquor
    (
        BusinessActivityType.LIQUOR_BAR,
        r"\b(bar|bars|tavern|taverns|pub|pubs|liquor\s+store|package\s+goods|alcohol|beer\s+and\s+wine|nightclub)\b",
        False,
        False,
        "Tavern License",
        None,
    ),

    # 7. Tobacco / Vape / Smoke Shop
    (
        BusinessActivityType.RETAIL_TOBACCO,
        r"\b(smoke\s+shop|vape\s+shop|tobacco\s+shop|cigar\s+shop|hookah\s+lounge|cigarettes?|tobacco\s+license)\b",
        False,
        False,
        "Retail Tobacco",
        None,
    ),

    # 8. Tailoring / Tailor / Clothing Alterations
    (
        BusinessActivityType.SERVICE_TAILORING,
        r"\b(tailoring|tailor|tailering|tailorng|tailer|tailors|tailor\s+shop|tailoring\s+shop|tailor\s+kadai|thayal\s+kadai|dress\s+stitching|alterations?\s+shop)\b",
        False,
        False,
        None,  # No specific standalone tailoring license code in Chicago DB; needs careful guidance / LBL inquiry
        "tailoring_setup",
    ),

    # 9. Clothing / Apparel / Shoes Retail
    (
        BusinessActivityType.RETAIL_CLOTHING,
        r"\b(clothing\s+(?:store|shop)|clothes\s+(?:store|shop)|dress\s+(?:shop|store|kadai)|boutique|apparel|shoe\s+(?:store|shop)|fashion\s+store|garment\s+store|textile\s+shop|thuni\s+kadai)\b",
        False,
        False,
        "Limited Business License",
        None,
    ),

    # 10. Electronics / Mobile Phone Retail
    (
        BusinessActivityType.RETAIL_ELECTRONICS_MOBILE,
        r"\b(mobile\s+phone\s+(?:shop|store)|phone\s+(?:shop|store)|cell\s*phone\s+shop|electronics?\s+(?:store|shop)|computer\s+(?:store|shop)|gadget\s+shop)\b",
        False,
        False,
        "Limited Business License",
        None,
    ),

    # 11. Other Specified Retail (Hardware, Books, Flowers, Furniture, etc.)
    (
        BusinessActivityType.RETAIL_GENERAL_SPECIFIED,
        r"\b(bookstore|book\s+shop|flower\s+shop|florist|hardware\s+store|furniture\s+store|gift\s+shop|jewelry\s+store|stationery\s+shop|pet\s+shop|toy\s+store)\b",
        False,
        False,
        "Limited Business License",
        None,
    ),

    # 12. Childcare / Daycare
    (
        BusinessActivityType.SERVICE_CHILDCARE,
        r"\b(daycare|day\s+care|childcare|child\s+care|preschool|nursery|children('s|\s+)?services)\b",
        False,
        False,
        "Children's Services Facility License",
        None,
    ),

    # 13. Auto Repair / Mechanic
    (
        BusinessActivityType.SERVICE_AUTO,
        r"\b(auto\s+repair|mechanic|car\s+repair|garage|body\s+shop|motor\s+vehicle\s+repair)\b",
        False,
        False,
        "Motor Vehicle Repair",
        None,
    ),

    # 14. Massage / Spa
    (
        BusinessActivityType.SERVICE_MASSAGE,
        r"\b(massage|spa|masseuse|massage\s+therapy|massage\s+establishment)\b",
        False,
        False,
        "Massage Establishment",
        None,
    ),

    # 15. Entertainment / Public Amusement
    (
        BusinessActivityType.SERVICE_ENTERTAINMENT,
        r"\b(amusement|public\s+place\s+of\s+amusement|music\s+venue|theater|concert\s+hall|bowling|arcade)\b",
        False,
        False,
        "Public Place of Amusement License",
        None,
    ),

    # 16. Generic Retail (Unspecified Goods - e.g. "retail shop", "retail store", "open a shop", "kadai open panna")
    (
        BusinessActivityType.GENERIC_RETAIL,
        r"\b(?:retail\s+shop|retail\s+store|retail\s+business|retail\s+outlet|retail\s+ondu|retail\s+kadai|retail\s+vangi|retail\s+panra|general\s+store|(?:open|start|run|launch|set\s+up)\s+(?:a\s+|an\s+|oru\s+)?(?:shop|store|retail|kadai)|(?:shop|store|kadai)\s+(?:open|start|podanum))\b",
        False,
        True,   # Ambiguous goods
        None,
        "retail_goods",
    ),

    # 17. Generic Business (Unspecified Activity - e.g. "business start", "business panna", "company open")
    (
        BusinessActivityType.GENERIC_BUSINESS,
        r"\b(business\s+start|business\s+open|start\s+(?:a\s+)?business|open\s+(?:a\s+)?business|business\s+panna|business\s+edukka|business\s+vekkara|puthiya\s+business|general\s+business|standard\s+business)\b",
        False,
        True,   # Ambiguous activity
        None,
        "business_type",
    ),
]

_UNKNOWN_TOKEN_REGEX = re.compile(r"\b([a-zA-Z0-9_-]*[0-9]+[a-zA-Z0-9_-]*)\b", re.I)
_KNOWN_DIGIT_TOKENS: Set[str] = {
    "1006", "1010", "1011", "1004", "1005", "1002", "1470", "1781", "4405", "1012",
    "800", "121", "60602", "744", "6060", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
}


def extract_business_activity(text: str) -> BusinessActivity:
    """
    Extracts structured BusinessActivity from a natural-language query string.
    Evaluates patterns in strict priority order to prevent generic terms from overriding
    specific activities or vice versa.
    """
    if not text:
        return BusinessActivity(
            activity_type=BusinessActivityType.NONE,
            extracted_text="",
            is_food_related=False,
            is_generic_or_ambiguous=False,
        )

    lower = text.lower().strip()

    # Check for unrecognized token (e.g. "XYZABC123")
    token_matches = _UNKNOWN_TOKEN_REGEX.findall(text)
    for tm in token_matches:
        if tm.lower() not in _KNOWN_DIGIT_TOKENS and len(tm) >= 5:
            return BusinessActivity(
                activity_type=BusinessActivityType.UNRECOGNIZED_TOKEN,
                extracted_text=tm,
                is_food_related=False,
                is_generic_or_ambiguous=False,
                clarification_prompt_type=None,
            )

    # Match against categorized patterns
    for act_type, pattern, is_food, is_ambig, candidate, prompt_type in _ACTIVITY_PATTERNS:
        match = re.search(pattern, lower, re.I)
        if match:
            return BusinessActivity(
                activity_type=act_type,
                extracted_text=match.group(0),
                is_food_related=is_food,
                is_generic_or_ambiguous=is_ambig,
                suggested_candidate_service=candidate,
                clarification_prompt_type=prompt_type,
            )

    # Check for generic single word occurrences
    if re.search(r"^\s*(?:tailoring|tailering|tailorng|tailer)\s*$", lower):
        return BusinessActivity(
            activity_type=BusinessActivityType.SERVICE_TAILORING,
            extracted_text=lower,
            is_food_related=False,
            is_generic_or_ambiguous=False,
            suggested_candidate_service=None,
            clarification_prompt_type="tailoring_setup",
        )

    if re.search(r"^\s*(?:shop|store|kadai)\s*$", lower):
        return BusinessActivity(
            activity_type=BusinessActivityType.GENERIC_RETAIL,
            extracted_text=lower,
            is_food_related=False,
            is_generic_or_ambiguous=True,
            suggested_candidate_service=None,
            clarification_prompt_type="retail_goods",
        )

    if re.search(r"^\s*(?:business|company|enterprise)\s*$", lower):
        return BusinessActivity(
            activity_type=BusinessActivityType.GENERIC_BUSINESS,
            extracted_text=lower,
            is_food_related=False,
            is_generic_or_ambiguous=True,
            suggested_candidate_service=None,
            clarification_prompt_type="business_type",
        )

    return BusinessActivity(
        activity_type=BusinessActivityType.NONE,
        extracted_text="",
        is_food_related=False,
        is_generic_or_ambiguous=False,
    )
